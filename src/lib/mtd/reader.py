# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import datetime
import logging
import re
import random
import urllib.request
import urllib.error
import time
from envparse import env

##########################################################
# Third Party Imports

import datefinder
import pymarc
import sqlalchemy.engine
from PIL import ImageFile

##########################################################
# Local Imports

from thickshake.mtd.database import manage_db_session, initialise_db
from thickshake.mtd import schema
from thickshake.utils import consolidate_list, log_progress, setup_warnings, setup_logging, get_file_type
from thickshake.types import *

##########################################################
# Parser Configuration

INPUT_METADATA_FILE = env.str("INPUT_METADATA_FILE") # type: FilePath

OUTPUT_METADATA_FILE = env.str("OUTPUT_METADATA_FILE")

FLAG_MTD_GEOCODING = env.bool("FLAG_MTD_GEOCODING", default=False)
FLAG_MTD_DIMENSIONS = env.bool("FLAG_MTD_DIMENSIONS", default=False)
FLAG_MTD_LOGGING = env.bool("FLAG_MTD_LOGGING", default=True)
FLAG_MTD_SAMPLE = env.int("FLAG_MTD_SAMPLE", default=0)

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["drivername"] = env.str("DB_DRIVER")
DB_CONFIG["host"] = env.str("DB_HOST")
DB_CONFIG["database"] = env.str("POSTGRES_DB")
DB_CONFIG["username"] = env.str("POSTGRES_USER")
DB_CONFIG["password"] = env.str("POSTGRES_PASSWORD")

TAG_COLLECTION_ID = env.list("TAG_COLLECTION_ID", default=['035', 'a']) 
TAG_NOTE_TITLE = env.list("TAG_NOTE_TITLE", default=["245", "a"])
TAG_NOTE_GENERAL = env.list("TAG_NOTE_GENERAL", default=["500", "a"])
TAG_NOTE_SUMMARY = env.list("TAG_NOTE_SUMMARY", default=["520", "a"])
TAG_SERIES_TITLE = env.list("TAG_SERIES_TITLE", default=["830", "a"])
TAG_SERIES_VOLUME = env.list("TAG_SERIES_VOLUME", default=["830", "v"])
TAG_PHYSICAL_EXTENT = env.list("TAG_PHYSICAL_EXTENT", default=["300", "a"])
TAG_PHYSICAL_DETAILS = env.list("TAG_PHYSICAL_DETAILS", default=["300", "b"])
TAG_DATE_CREATED = env.list("TAG_DATE_CREATED", default=["260", "c"])
TAG_DATE_CREATED_APPROX = env.list("TAG_DATE_CREATED_APPROX", default=["264", "c"])
TAG_TOPIC = env.list("TAG_TOPIC", default=["650", "a"])
TAG_LOCATION_DIVISION = env.list("TAG_LOCATION_DIVISION", default=["650", "z"])
TAG_LOCATION_NAME = env.list("TAG_LOCATION_NAME", default=["651", "a"])
TAG_SUBJECT_PERSON_NAME_MAIN = env.list("TAG_SUBJECT_PERSON_NAME_MAIN", default=["100", "a"])
TAG_SUBJECT_PERSON_DATES_MAIN = env.list("TAG_SUBJECT_PERSON_DATES_MAIN", default=["100", "d"])
TAG_SUBJECT_PERSON_RELATION_MAIN = env.list("TAG_SUBJECT_PERSON_RELATION_MAIN", default=["100", "e"])
TAG_SUBJECT_COMPANY_NAME_MAIN = env.list("TAG_SUBJECT_COMPANY_NAME_MAIN", default=["110", "a"])
TAG_SUBJECT_COMPANY_RELATION_MAIN = env.list("TAG_SUBJECT_COMPANY_RELATION_MAIN", default=["110", "e"])
TAG_SUBJECT_PERSON_NAME_OTHER = env.list("TAG_SUBJECT_PERSON_NAME_OTHER", default=["600", "a"])
TAG_SUBJECT_PERSON_DATES_OTHER = env.list("TAG_SUBJECT_PERSON_DATES_OTHER", default=["600", "d"])
TAG_SUBJECT_COMPANY_NAME_OTHER = env.list("TAG_SUBJECT_COMPANY_NAME_OTHER", default=["610", "a"])
TAG_SUBJECT_COMPANY_RELATION_OTHER = env.list("TAG_SUBJECT_COMPANY_RELATION_OTHER", default=["610", "x"])
TAG_IMAGE_URL = env.list("TAG_IMAGE_URL", default=["856", "u"])
TAG_IMAGE_NOTE = env.list("TAG_IMAGE_NOTE", default=["856", "z"])

class FileType:
    JSON = ".json"
    HDF5 = ".hdf5"
    MARC21 = ".marc"
    MARCXML = ".xml"
    CSV = ".csv"

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Helper Functions


def get_subfield_from_field(field: PymarcField, subfield_key: str) -> Optional[str]:
    if subfield_key not in field: return None
    subfield = field[subfield_key]
    return subfield


def get_subfield_from_record(record: PymarcRecord, field_key: str, subfield_key: str) -> Optional[str]:
    if field_key not in record: return None
    field = record[field_key]
    subfield = get_subfield_from_field(field, subfield_key)
    return subfield


def get_subfields(record: PymarcRecord, field_key: str, subfield_key: str) -> List[Optional[str]]:
    fields = record.get_fields(field_key) # type: List[PymarcField]
    subfields = [get_subfield_from_field(field, subfield_key) for field in fields]
    return subfields


def parse_tag_key(tag_key: List[str]) -> Tag:
    """Split tag into a tuple of the field and subfield."""
    if len(tag_key) == 2:
        tag = Tag(field=tag_key[0], subfield=tag_key[1])
    elif len(tag_key) == 1:
        tag = Tag(field=tag_key[0], subfield=None)
    else: tag = None
    return tag


def get_subfield_from_tag(record_or_field: Union[PymarcRecord, PymarcField], tag_key: str) -> Optional[str]:
    tag = parse_tag_key(tag_key)
    field_key = tag["field"]
    subfield_key = tag["subfield"]
    if isinstance(record_or_field, PymarcRecord):
        subfield = get_subfield_from_record(record_or_field, field_key, subfield_key)
    elif isinstance(record_or_field, PymarcField):
        subfield = get_subfield_from_field(record_or_field, subfield_key)
    else: subfield = None
    return subfield


def get_subfields_from_tag(record: PymarcRecord, tag_key: str) -> List[str]:
    tag = parse_tag_key(tag_key)
    field_key = tag["field"]
    subfield_key = tag["subfield"]
    subfields_raw = get_subfields(record, field_key, subfield_key)
    subfields = consolidate_list(subfields_raw)
    return subfields


def get_fields_from_tag(record: PymarcRecord, tag_key: str) -> List[PymarcField]:
    tag = parse_tag_key(tag_key)
    field_key = tag["field"]
    fields = record.get_fields(field_key) # type: List[PymarcField]
    return fields


def get_id_from_url(image_file: Optional[FilePath]) -> Optional[str]:
    if image_file is None: return None
    image_id = image_file.split("/")[-1].split(".")[0] # type: Optional[str]
    return image_id


##########################################################
# Low level parser


def parse_topics(record: PymarcRecord, **kwargs: Any) -> List[str]:
    topics_raw = get_subfields_from_tag(record, TAG_TOPIC)
    topics_raw = consolidate_list(topics_raw)
    topics = [{"topic": topic} for topic in topics_raw]
    return topics


def parse_locations(record: PymarcRecord, **kwargs: Any) -> List[str]:
    location_divisions_raw = get_subfields_from_tag(record, TAG_LOCATION_DIVISION)
    location_names_raw = get_subfields_from_tag(record, TAG_LOCATION_NAME)
    locations_raw = consolidate_list([*location_divisions_raw, *location_names_raw])
    locations = [{"location": location} for location in locations_raw]
    return locations


def parse_main_person(record: PymarcRecord) -> ParsedRecord:
    main_person = {
        "subject_name": get_subfield_from_tag(record, TAG_SUBJECT_PERSON_NAME_MAIN),
        "subject_relation": get_subfield_from_tag(record, TAG_SUBJECT_PERSON_RELATION_MAIN),
        "subject_dates": get_subfield_from_tag(record, TAG_SUBJECT_PERSON_DATES_MAIN),
        "subject_type": "Person",
        "subject_is_main": True,
    }
    return main_person


def parse_main_company(record: PymarcRecord) -> ParsedRecord:
    main_company = {
        "subject_name": get_subfield_from_tag(record, TAG_SUBJECT_COMPANY_NAME_MAIN),
        "subject_relation": get_subfield_from_tag(record, TAG_SUBJECT_COMPANY_RELATION_MAIN),
        "subject_dates": None,
        "subject_type": "Company",
        "subject_is_main": True,
    }
    return main_company


def parse_other_people(record: PymarcRecord) -> List[ParsedRecord]:
    other_people_raw = get_fields_from_tag(record, TAG_SUBJECT_PERSON_NAME_OTHER)
    other_people = [
        {
            "subject_name": get_subfield_from_tag(person, TAG_SUBJECT_PERSON_NAME_OTHER),
            "subject_relation": None,
            "subject_dates": get_subfield_from_tag(person, TAG_SUBJECT_PERSON_DATES_OTHER),
            "subject_type": "Person",
            "subject_is_main": False,
        } for person in other_people_raw
    ]
    return other_people


def parse_other_companies(record: PymarcRecord) -> List[ParsedRecord]:
    other_companies_raw = get_fields_from_tag(record, TAG_SUBJECT_COMPANY_NAME_OTHER)
    other_companies = [
        {
            "subject_name": get_subfield_from_tag(company, TAG_SUBJECT_COMPANY_NAME_OTHER),
            "subject_relation": get_subfield_from_tag(company, TAG_SUBJECT_COMPANY_RELATION_OTHER),
            "subject_dates": None,
            "subject_type": "Company",
            "subject_is_main": False,
        } for company in other_companies_raw
    ]
    return other_companies


def parse_subjects(record: PymarcRecord, **kwargs: Any) -> List[ParsedRecord]:
    main_person = parse_main_person(record)
    main_company = parse_main_company(record)
    other_people = parse_other_people(record)
    other_companies = parse_other_companies(record)
    subjects = consolidate_list([main_person, main_company, *other_people, *other_companies])
    return subjects


def parse_collection(record: PymarcRecord, **kwargs: Any) -> ParsedRecord:
    collection = {
        "collection_id": get_subfield_from_tag(record, TAG_COLLECTION_ID),
        "note_title": get_subfield_from_tag(record, TAG_NOTE_TITLE),
        "note_general": get_subfield_from_tag(record, TAG_NOTE_GENERAL),
        "note_summary": get_subfield_from_tag(record, TAG_NOTE_SUMMARY),
        "series_title": get_subfield_from_tag(record, TAG_SERIES_TITLE),
        "series_volume": get_subfield_from_tag(record, TAG_SERIES_VOLUME),
        "physical_extent": get_subfield_from_tag(record, TAG_PHYSICAL_EXTENT),
        "physical_details": get_subfield_from_tag(record, TAG_PHYSICAL_DETAILS),
        "date_created": get_subfield_from_tag(record, TAG_DATE_CREATED),
        "date_created_approx": get_subfield_from_tag(record, TAG_DATE_CREATED_APPROX),
    }
    return collection


def parse_images(record: PymarcRecord, geocoding_flag: bool = False, dimensions_flag: bool = False, **kwargs: Any) -> List[ParsedRecord]:
    images_raw = get_fields_from_tag(record, TAG_IMAGE_URL)
    images = []
    for image_raw in images_raw:
        image_url = get_subfield_from_tag(image_raw, TAG_IMAGE_URL)
        if image_url is None or ".png" in image_url: continue
        image = {
            "image_id": get_id_from_url(get_subfield_from_tag(image_raw, TAG_IMAGE_URL)),
            "image_url": get_subfield_from_tag(image_raw, TAG_IMAGE_URL),
            "image_note": get_subfield_from_tag(image_raw, TAG_IMAGE_NOTE),
        }
        images.append(image)
    images = consolidate_list(images)
    return images


##########################################################
# High-level Parser


def parse_record_section(record: PymarcRecord, db_schema: Schema, parser: Parser, collection: PymarcRecord, engine: Engine, **kwargs: Any) -> None:
    records_parsed = parser(record, **kwargs)
    if not isinstance(records_parsed, list): # for Collection
        records_parsed = [records_parsed]
        collection = {}
    for record_parsed in records_parsed:
        with manage_db_session(engine) as session:
            record_object = db_schema(**dict(**record_parsed, **collection))
            session.add(record_object)


def parse_record(record: PymarcRecord, **kwargs: Any) -> None:
    collection = parse_collection(record, **kwargs)
    parse_record_section(record, schema.Collection, parse_collection, collection, **kwargs)
    parse_record_section(record, schema.CollectionTopic, parse_topics, collection, **kwargs)
    parse_record_section(record, schema.CollectionLocation, parse_locations, collection, **kwargs)
    parse_record_section(record, schema.Subject, parse_subjects, collection, **kwargs)
    parse_record_section(record, schema.CollectionSubject, parse_subjects, collection, **kwargs)
    parse_record_section(record, schema.Image, parse_images, collection, **kwargs)


def load_database(records: List[PymarcRecord], db_config: DBConfig, logging_flag: bool = True, **kwargs: Any) -> None:
    db_engine = initialise_db(db_config, **kwargs)
    total = len(records)
    start_time = time.time()
    for i, record in enumerate(records):
        parse_record(record, engine=db_engine, **kwargs)
        if logging_flag: log_progress(i+1, total, start_time)


##########################################################
# Reader IO Functions


def sample_records(records: List[PymarcRecord], sample_size: int = 0) -> List[PymarcRecord]:
    return records if sample_size == 0 else random.sample(records, sample_size)


def read_marcxml(input_file: str, sample_size: int = 0, **kwargs: Any) -> List[PymarcRecord]:
    return pymarc.parse_xml_to_array(input_file)


def read_marc21(input_file: FilePath, **kwargs: Any) -> List[PymarcRecord]:
    return list(pymarc.reader.MARCReader(file(input_file)))


def read_json(input_file: FilePath, **kwargs: Any) -> List[PymarcRecord]:
    return list(pymarc.reader.JSONReader(file(input_file)))


def read_file(input_file: FilePath, sample_size: int = 0, **kwargs: Any) -> List[PymarcRecord]:
    file_type = get_file_type(input_file)
    if file_type == FileType.JSON:
        records = read_json(input_file, **kwargs)
    elif file_type == FileType.MARC21:
        records = read_marc21(input_file, **kwargs)
    elif file_type == FileType.MARCXML:
        records = read_marcxml(input_file, **kwargs)
    else: raise NotImplementedError
    records = sample_records(records, sample_size=sample_size)
    return records


##########################################################
# Main

def main():
    records = read_file(
        input_file=INPUT_METADATA_FILE,
        sample_size=FLAG_MTD_SAMPLE
    )
    load_database(
        records=records,
        db_config=DB_CONFIG,
        logging_flag=FLAG_MTD_LOGGING,
    )

if __name__ == "__main__":
    setup_warnings()
    setup_logging()
    main()