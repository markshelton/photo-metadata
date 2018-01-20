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
from thickshake.mtd.writer import write_hdf5
from thickshake.mtd.geocoder import extract_location_from_text
from thickshake.mtd import schema
from thickshake.utils import (
    consolidate_list, log_progress, deep_get,
    setup_warnings, setup_logging, get_file_type,
)
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
# Functions


def get_subfield_from_field(field: PymarcField, subfield_key: str) -> Optional[str]:
    if subfield_key in field:
        subfield = field[subfield_key]
    else:
        subfield = None
    return subfield


def get_subfield_from_record(record: PymarcRecord, field_key: str, subfield_key: str) -> Optional[str]:
    if field_key in record:
        field = record[field_key]
        subfield = get_subfield_from_field(field, subfield_key)
    else:
        subfield = None
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
    else:
        subfield = None
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


##########################################################


def get_possible_dates(date_string: str) -> List[Date]:
    years = re.findall(".*([1-2][0-9]{3})", date_string)
    dates = [datetime.date(year=int(year), month=1, day=1) for year in years]
    if not dates:
        dates = list(datefinder.find_dates(date_string))
    return dates


def select_date(possible_dates: List[Date], method: str = "first") -> Optional[Date]:
    if len(possible_dates) == 0: return None
    if method == "first":
        return possible_dates[0]
    elif method == "last":
        return possible_dates[-1]
    else:
        logger.error("Invalid method argument: %s. Please use 'first' or 'last'.", method)
        return None
    

def extract_date_from_text(date_text: str, method: str = "first") -> Optional[Date]:
    possible_dates = get_possible_dates(date_text)
    selected_date = select_date(possible_dates, method=method)
    return selected_date


def get_date_collection_created(record: PymarcRecord) -> Optional[Date]:
    date_created_raw = get_subfield_from_tag(record, TAG_DATE_CREATED)
    date_created_approx_raw = get_subfield_from_tag(record, TAG_DATE_CREATED_APPROX)
    if date_created_raw:
        date_created = extract_date_from_text(date_created_raw)
    elif date_created_approx_raw:
        date_created = extract_date_from_text(date_created_approx_raw)
    else:
        date_created = None
    return date_created


def split_dates(record: PymarcRecord, dates_tag: str) -> Dates:
    dates_raw = get_subfield_from_tag(record, dates_tag)
    if dates_raw is None: return Dates({"start": None, "end": None})
    dates_num = len(dates_raw.split("-"))
    if dates_num >= 2:
        date_start_raw, date_end_raw, *_ = dates_raw.split("-")
        date_start = extract_date_from_text(date_start_raw)
        date_end = extract_date_from_text(date_end_raw)
    elif dates_num == 1:
        date_start_raw = dates_raw.split("-")[0]
        date_start = extract_date_from_text(date_start_raw)
        date_end = None
    dates = Dates({"start": date_start, "end": date_end})
    return dates


def get_image_url(image: PymarcField, tag: str, method: str = "main"):
    image_url_raw = get_subfield_from_tag(image, tag)
    if image_url_raw is None: return None
    if method == "main":
        image_url = image_url_raw
    elif method == "raw":
        image_url = image_url_raw + ".jpg"
    elif method == "thumb":
        image_url = image_url_raw + ".png"
    else: return None
    return image_url


def get_id_from_url(image_file: Optional[FilePath]) -> Optional[str]:
    if image_file is None: return None
    image_id = image_file.split("/")[-1].split(".")[0] # type: Optional[str]
    return image_id


def get_image_dimensions(field: PymarcField, tag: str, dimensions_flag: bool = True) -> Optional[Size]:
    if dimensions_flag is False: return None
    image_url_raw = get_subfield_from_tag(field, tag)
    if image_url_raw is None: return None
    image_url = image_url_raw + ".jpg"
    try:
        with urllib.request.urlopen(image_url) as image_file:
            parser = ImageFile.Parser()
            while True:
                data = image_file.read(1024)
                if not data:
                    break
                parser.feed(data)
                if parser.image:
                    width, height = parser.image.size
                    return Size({"width": width, "height": height})
    except urllib.error.URLError:
        logger.warning("Image not found. Size could not be determined.")
    return None


def get_location(field: PymarcField, tag: str, geocoding_flag: bool = True) -> Optional[Location]:
    if not geocoding_flag: return None
    location_text = get_subfield_from_tag(field, tag)
    if location_text is None: return None
    location = extract_location_from_text(location_text)
    return location


def get_date(field: PymarcField, tag: str) -> Optional[Date]:
    date_text = get_subfield_from_tag(field, tag)
    if date_text is None: return None
    extracted_date = extract_date_from_text(date_text)
    return extracted_date

def check_image(field: PymarcField) -> bool:
    image_url = get_subfield_from_tag(field, TAG_IMAGE_URL)
    if image_url is None or ".png" in image_url: return False
    return True


##########################################################

def parse_topics(record: PymarcRecord, **kwargs: Any) -> List[str]:
    topics_raw = get_subfields_from_tag(record, TAG_TOPIC)
    topics = consolidate_list(topics_raw)
    return topics

def parse_locations(record: PymarcRecord, **kwargs: Any) -> List[str]:
    location_divisions_raw = get_subfields_from_tag(record, TAG_LOCATION_DIVISION)
    location_names_raw = get_subfields_from_tag(record, TAG_LOCATION_NAME)
    locations = consolidate_list([*location_divisions_raw, *location_names_raw])
    return locations

def parse_main_person(record: PymarcRecord) -> ParsedRecord:
    subject_name = get_subfield_from_tag(record, TAG_SUBJECT_PERSON_NAME_MAIN)
    main_person = {
        "subject_name": get_subfield_from_tag(record, TAG_SUBJECT_PERSON_NAME_MAIN),
        "subject_relation": get_subfield_from_tag(record, TAG_SUBJECT_PERSON_RELATION_MAIN),
        "subject_dates": split_dates(record, TAG_SUBJECT_PERSON_DATES_MAIN),
        "subject_type": "Person",
        "subject_is_main": True,
    }
    return main_person


def parse_main_company(record: PymarcRecord) -> ParsedRecord:
    subject_name = get_subfield_from_tag(record, TAG_SUBJECT_COMPANY_NAME_MAIN)
    main_company = {
        "subject_name": get_subfield_from_tag(record, TAG_SUBJECT_COMPANY_NAME_MAIN),
        "subject_relation": get_subfield_from_tag(record, TAG_SUBJECT_COMPANY_RELATION_MAIN),
        "subject_dates": Dates({"start": None, "end": None}),
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
            "subject_dates": split_dates(person, TAG_SUBJECT_PERSON_DATES_OTHER),
            "subject_type": "Person",
            "subject_is_main": False,
        } for person in other_people_raw
    ]
    return other_people


def parse_other_companies(record: PymarcRecord) -> List[ParsedRecord]:
    other_companies_raw = get_fields_from_tag(record, TAG_SUBJECT_COMPANY_NAME_OTHER)
    other_companies = [
        {
            "subject_name": get_subfield_from_tag(company, TAG_SUBJECT_COMPANY_NAME_MAIN),
            "subject_relation": get_subfield_from_tag(company, TAG_SUBJECT_COMPANY_RELATION_MAIN),
            "subject_dates": Dates({"start": None, "end": None}),
            "subject_type": "Company",
            "subject_is_main": False,
        } for company in other_companies_raw
    ]
    return other_companies


##########################################################


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
        "date_created": get_date_collection_created(record),
    }
    return collection


def parse_images(record: PymarcRecord, geocoding_flag: bool = False, dimensions_flag: bool = False, **kwargs: Any) -> List[ParsedRecord]:
    images_raw = get_fields_from_tag(record, TAG_IMAGE_URL)
    images = consolidate_list([
        {
            "image_id": get_id_from_url(get_subfield_from_tag(image, TAG_IMAGE_URL)),
            "image_url_main": get_image_url(image, TAG_IMAGE_URL, method="main"),
            "image_url_raw": get_image_url(image, TAG_IMAGE_URL, method="raw"),
            "image_url_thumb": get_image_url(image, TAG_IMAGE_URL, method="thumb"),
            "image_note": get_subfield_from_tag(image, TAG_IMAGE_NOTE),
            "image_dimensions": get_image_dimensions(image, TAG_IMAGE_URL, dimensions_flag=dimensions_flag),
            "image_location": get_location(image, TAG_IMAGE_NOTE, geocoding_flag=geocoding_flag),
            "image_date_created": get_date(image, TAG_IMAGE_NOTE),
        } for image in images_raw if check_image(image)
    ])
    return images


def parse_subjects(record: PymarcRecord, **kwargs: Any) -> List[ParsedRecord]:
    main_person = parse_main_person(record)
    main_company = parse_main_company(record)
    other_people = parse_other_people(record)
    other_companies = parse_other_companies(record)
    subjects = consolidate_list([
        main_person, main_company,
        *other_people, *other_companies
    ])
    return subjects


##########################################################


def collect_collection_data(record: PymarcRecord, **kwargs: Any) -> List[ParsedRecord]:
    collection_data = parse_collection(record, **kwargs)
    collection = [collection_data]
    return collection


def collect_collection_topics(record: PymarcRecord, **kwargs: Any) -> List[ParsedRecord]:
    topics = parse_topics(record, **kwargs)
    collection_data = parse_collection(record, **kwargs)
    collection_topics = [
        {
            "collection_id": collection_data["collection_id"],
            "topic": topic,
        } for topic in topics
    ]
    return collection_topics


def collect_collection_locations(record: PymarcRecord, **kwargs: Any) -> List[ParsedRecord]:
    locations = parse_locations(record, **kwargs)
    collection_data = parse_collection(record, **kwargs)
    collection_locations = [
        {
            "collection_id": collection_data["collection_id"],
            "location": location,
        } for location in locations
    ]
    return collection_locations


def collect_subjects(record: PymarcRecord, **kwargs: Any) -> List[ParsedRecord]:
    subjects_data = parse_subjects(record, **kwargs)
    subjects = [
        {
            "subject_name": subject["subject_name"],
            "subject_type": subject["subject_type"],
            "subject_start_date": subject["subject_dates"]["start"],
            "subject_end_date": subject["subject_dates"]["end"],
        } for subject in subjects_data
    ]
    return subjects


def collect_collection_subjects(record: PymarcRecord, **kwargs: Any) -> List[ParsedRecord]:
    subjects_data = parse_subjects(record, **kwargs)
    collection_data = parse_collection(record, **kwargs)
    collection_subjects = [
        {
            "collection_id": collection_data["collection_id"],
            "subject_name": subject["subject_name"],
            "subject_relation": subject["subject_relation"],
            "subject_is_main": subject["subject_is_main"],
        } for subject in subjects_data
    ]
    return collection_subjects


def collect_images(record: PymarcRecord, **kwargs: Any) -> List[ParsedRecord]:
    images_raw = parse_images(record, **kwargs)
    collection_raw = parse_collection(record, **kwargs)
    images = [] # type: List[ParsedRecord]
    for image_raw in images_raw:
        image = {
            "image_id": image_raw["image_id"],
            "image_url_main": image_raw["image_url_main"],
            "image_url_raw": image_raw["image_url_raw"],
            "image_url_thumb": image_raw["image_url_thumb"],
            "image_note": image_raw["image_note"],
            "image_width": deep_get(image_raw, "image_dimensions", "width"),
            "image_height": deep_get(image_raw, "image_dimensions", "height"),
            "image_longitude": deep_get(image_raw, "image_coordinates", "longitude"),
            "image_latitude": deep_get(image_raw, "image_coordinates", "latitude"),
            "image_date_created": image_raw["image_date_created"],
            "collection_id": collection_raw["collection_id"],
        }
    images.append(image)
    return images


##########################################################


def parse_record_section(
        record: PymarcRecord,
        db_schema: Schema,
        parser: Callable[[PymarcRecord, KwArg(Any)], List[ParsedRecord]],
        engine: Engine,
        **kwargs: Any
    ) -> None:
    records_parsed = parser(record, **kwargs)
    for record_parsed in records_parsed:
        with manage_db_session(engine) as session:
            record_object = db_schema(**record_parsed)
            session.add(record_object)


def parse_record(record: PymarcRecord, **kwargs: Any) -> None:
    parse_record_section(record, schema.Collection, collect_collection_data, **kwargs)
    parse_record_section(record, schema.CollectionTopic, collect_collection_topics, **kwargs)
    parse_record_section(record, schema.CollectionLocation, collect_collection_locations, **kwargs)
    parse_record_section(record, schema.Subject, collect_subjects, **kwargs)
    parse_record_section(record, schema.CollectionSubject, collect_collection_subjects, **kwargs)
    parse_record_section(record, schema.Image, collect_images, **kwargs)


def sample_records(records: List[PymarcRecord], sample_size: int = 0) -> List[PymarcRecord]:
    return records if sample_size == 0 else random.sample(records, sample_size)


def read_marcxml(input_file: str, sample_size: int = 0, **kwargs: Any) -> List[PymarcRecord]:
    records_input = pymarc.parse_xml_to_array(input_file)
    records_sample = sample_records(records_input, sample_size)
    return records_sample


def read_marc21(input_file: FilePath, **kwargs: Any) -> List[PymarcRecord]:
    pass


def read_json(input_file: FilePath, **kwargs: Any) -> List[PymarcRecord]:
    pass


def read_hdf5(input_file: FilePath, **kwargs: Any) -> List[PymarcRecord]:
    pass


def read_csv(input_file: FilePath, **kwargs: Any) -> List[PymarcRecord]:
    pass


def read_file(input_file, **kwargs) -> List[Any]:
    file_type = get_file_type(input_file) #DONE
    if file_type == FileType.JSON:
        records = read_json(input_file, **kwargs) #TODO
    elif file_type == FileType.HDF5:
        records = read_hdf5(input_file, **kwargs) #TODO
    elif file_type == FileType.MARC21:
        records = read_marc21(input_file, **kwargs) #TODO
    elif file_type == FileType.MARCXML:
        records = read_marcxml(input_file, **kwargs) #DONE
    elif file_type == FileType.CSV:
        records = read_csv(input_file, **kwargs) #TODO
    else: raise NotImplementedError
    return records


def load_database(records, db_config, logging_flag: bool = True, **kwargs):
    db_engine = initialise_db(db_config, **kwargs)
    total = len(records)
    start_time = time.time()
    for i, record in enumerate(records):
        parse_record(record, engine=db_engine, **kwargs)
        if logging_flag: log_progress(i+1, total, start_time)


##########################################################

def main():
    load_marcxml(
        input_file=INPUT_METADATA_FILE,
        metadata_file=OUTPUT_METADATA_FILE,
        db_config=DB_CONFIG,
        geocoding=FLAG_MTD_GEOCODING,
        dimensions=FLAG_MTD_DIMENSIONS,
        logging_flag=FLAG_MTD_LOGGING,
        sample_size=FLAG_MTD_SAMPLE
    )

if __name__ == "__main__":
    setup_warnings()
    setup_logging()
    main()