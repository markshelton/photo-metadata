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
from functools import reduce, wraps

##########################################################
# Third Party Imports

import pymarc
import datefinder
from PIL import ImageFile
from mypy_extensions import TypedDict

##########################################################
# Local Imports

from database import manage_db_session
from geocoder import extract_coordinates_from_text
from schema import Base
from _types import (
    Dict, List, Pattern, Any, Callable, Optional, Union, KwArg,
    Tag, Dates, Size, Coordinates, ParsedRecord,
    Record, Field, Date, Engine, Schema, 
)

##########################################################
# Parser Configuration

TAG_DELIMITER = "$"
TAG_COLLECTION_ID = "035$a"
TAG_NOTE_TITLE = "245$a"
TAG_NOTE_GENERAL = "500$a"
TAG_NOTE_SUMMARY = "520$a"
TAG_SERIES_TITLE = "830$a"
TAG_SERIES_VOLUME = "830$v"
TAG_PHYSICAL_EXTENT = "300$a"
TAG_PHYSICAL_DETAILS = "300$b"
TAG_DATE_CREATED = "260$c"
TAG_DATE_CREATED_APPROX = "264$c"
TAG_TOPIC = "650$a"
TAG_LOCATION_DIVISION = "650$z"
TAG_LOCATION_NAME = "651$a"
TAG_SUBJECT_PERSON_NAME_MAIN = "100$a"
TAG_SUBJECT_PERSON_DATES_MAIN = "100$d"
TAG_SUBJECT_PERSON_RELATION_MAIN = "100$e"
TAG_SUBJECT_COMPANY_NAME_MAIN = "110$a"
TAG_SUBJECT_COMPANY_RELATION_MAIN = "110$e"
TAG_SUBJECT_PERSON_NAME_OTHER = "600$a"
TAG_SUBJECT_PERSON_DATES_OTHER = "600$d"
TAG_SUBJECT_COMPANY_NAME_OTHER = "610$a"
TAG_SUBJECT_COMPANY_RELATION_OTHER = "610$x"
TAG_IMAGE_URL = "856$u"
TAG_IMAGE_NOTE = "856$z"

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Helpers


def logged(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        logger.info("{0} | Started".format(f.__name__))
        start_time = time.time()
        try: result = f(*args, **kwargs)
        except:
            elapsed_time = time.time() - start_time
            logger.error("{0} | Failed | {1:.2f}".format(f.__name__,elapsed_time), exc_info=True)
        else:
            elapsed_time = time.time() - start_time
            logger.info("{0} | Passed | {1:.2f}".format(f.__name__,elapsed_time))
            return result
    return wrapper    


def deep_get(dictionary: Dict, *keys: str) -> Optional[Any]:
    return reduce(lambda d, key: d.get(key, None) if isinstance(d, dict) else None, keys, dictionary)


def consolidate_list(full_list: List[Any]) -> List[Any]:
    """Remove null entries from list and return sub-list."""
    consolidated_list = [x for x in full_list if x is not None]
    return consolidated_list


##########################################################
# Functions


def get_subfield_from_field(field: Field, subfield_key: str) -> Optional[str]:
    if subfield_key in field:
        subfield = field[subfield_key]
    else:
        subfield = None
    return subfield


def get_subfield_from_record(record: Record, field_key: str, subfield_key: str) -> Optional[str]:
    if field_key in record:
        field = record[field_key]
        subfield = get_subfield_from_field(field, subfield_key)
    else:
        subfield = None
    return subfield


def get_subfields(record: Record, field_key: str, subfield_key: str) -> List[Optional[str]]:
    fields = record.get_fields(field_key) # type: List[Field]
    subfields = [get_subfield_from_field(field, subfield_key) for field in fields]
    return subfields


def parse_tag_key(tag_key: str) -> Tag:
    """Split tag (e.g. "700$a") into a tuple of the field and subfield."""
    m = re.match(r"(?P<field>\S{3})(?:\$?)(?P<subfield>\S*)?", tag_key)
    tag = Tag(field=m.group("field"), subfield=m.group("subfield"))
    return tag


def get_subfield_from_tag(record_or_field: Union[Record, Field], tag_key: str) -> Optional[str]:
    tag = parse_tag_key(tag_key)
    field_key = tag["field"]
    subfield_key = tag["subfield"]
    if isinstance(record_or_field, pymarc.record.Record):
        subfield = get_subfield_from_record(record_or_field, field_key, subfield_key)
    elif isinstance(record_or_field, pymarc.field.Field):
        subfield = get_subfield_from_field(record_or_field, subfield_key)
    else:
        subfield = None
    return subfield


def get_subfields_from_tag(record: Record, tag_key: str) -> List[str]:
    tag = parse_tag_key(tag_key)
    field_key = tag["field"]
    subfield_key = tag["subfield"]
    subfields_raw = get_subfields(record, field_key, subfield_key)
    subfields = consolidate_list(subfields_raw)
    return subfields


def get_fields_from_tag(record: Record, tag_key: str) -> List[Field]:
    tag = parse_tag_key(tag_key)
    field_key = tag["field"]
    fields = record.get_fields(field_key) # type: List[Field]
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


def get_date_collection_created(record: Record) -> Optional[Date]:
    date_created_raw = get_subfield_from_tag(record, TAG_DATE_CREATED)
    date_created_approx_raw = get_subfield_from_tag(record, TAG_DATE_CREATED_APPROX)
    if date_created_raw:
        date_created = extract_date_from_text(date_created_raw)
    elif date_created_approx_raw:
        date_created = extract_date_from_text(date_created_approx_raw)
    else:
        date_created = None
    return date_created


def split_dates(record: Record, dates_tag: str) -> Dates:
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


def get_image_url(image: Field, tag: str, method: str = "main"):
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


def get_id_from_url(image: Field, tag: str) -> Optional[str]:
    image_url = get_subfield_from_tag(image, tag)
    if image_url is None: return None
    image_id = image_url.split("/")[-1].split(".")[0] # type: Optional[str]
    return image_id


def get_image_dimensions(field: Field, tag: str, dimensions_flag: bool = True) -> Optional[Size]:
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


def get_coordinates(field: Field, tag: str, geocoding_flag: bool = True) -> Optional[Coordinates]:
    if not geocoding_flag: return None
    location_text = get_subfield_from_tag(field, tag)
    if location_text is None: return None
    coordinates = extract_coordinates_from_text(location_text)
    return coordinates


def get_date(field: Field, tag: str) -> Optional[Date]:
    date_text = get_subfield_from_tag(field, tag)
    if date_text is None: return None
    extracted_date = extract_date_from_text(date_text)
    return extracted_date

def check_image(field: Field) -> bool:
    image_url = get_subfield_from_tag(field, TAG_IMAGE_URL)
    if image_url is None or ".png" in image_url: return False
    return True


##########################################################

def parse_topics(record: Record, **kwargs: Any) -> List[str]:
    topics_raw = get_subfields_from_tag(record, TAG_TOPIC)
    topics = consolidate_list(topics_raw)
    return topics

def parse_locations(record: Record, **kwargs: Any) -> List[str]:
    location_divisions_raw = get_subfields_from_tag(record, TAG_LOCATION_DIVISION)
    location_names_raw = get_subfields_from_tag(record, TAG_LOCATION_NAME)
    locations = consolidate_list([*location_divisions_raw, *location_names_raw])
    return locations

def parse_main_person(record: Record) -> ParsedRecord:
    subject_name = get_subfield_from_tag(record, TAG_SUBJECT_PERSON_NAME_MAIN)
    main_person = {
        "subject_name": get_subfield_from_tag(record, TAG_SUBJECT_PERSON_NAME_MAIN),
        "subject_relation": get_subfield_from_tag(record, TAG_SUBJECT_PERSON_RELATION_MAIN),
        "subject_dates": split_dates(record, TAG_SUBJECT_PERSON_DATES_MAIN),
        "subject_type": "Person",
        "subject_is_main": True,
    }
    return main_person


def parse_main_company(record: Record) -> ParsedRecord:
    subject_name = get_subfield_from_tag(record, TAG_SUBJECT_COMPANY_NAME_MAIN)
    main_company = {
        "subject_name": get_subfield_from_tag(record, TAG_SUBJECT_COMPANY_NAME_MAIN),
        "subject_relation": get_subfield_from_tag(record, TAG_SUBJECT_COMPANY_RELATION_MAIN),
        "subject_dates": Dates({"start": None, "end": None}),
        "subject_type": "Person",
        "subject_is_main": True,
    }
    return main_company


def parse_other_people(record: Record) -> List[ParsedRecord]:
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


def parse_other_companies(record: Record) -> List[ParsedRecord]:
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


def parse_collection(record: Record, **kwargs: Any) -> ParsedRecord:
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


def parse_images(record: Record, geocoding_flag: bool = False, dimensions_flag: bool = False, **kwargs: Any) -> List[ParsedRecord]:
    images_raw = get_fields_from_tag(record, TAG_IMAGE_URL)
    images = consolidate_list([
        {
            "image_id": get_id_from_url(image, TAG_IMAGE_URL),
            "image_url_main": get_image_url(image, TAG_IMAGE_URL, method="main"),
            "image_url_raw": get_image_url(image, TAG_IMAGE_URL, method="raw"),
            "image_url_thumb": get_image_url(image, TAG_IMAGE_URL, method="thumb"),
            "image_note": get_subfield_from_tag(image, TAG_IMAGE_NOTE),
            "image_dimensions": get_image_dimensions(image, TAG_IMAGE_URL, dimensions_flag=dimensions_flag),
            "image_coordinates": get_coordinates(image, TAG_IMAGE_NOTE, geocoding_flag=geocoding_flag),
            "image_date_created": get_date(image, TAG_IMAGE_NOTE),
        } for image in images_raw if check_image(image)
    ])
    return images


def parse_subjects(record: Record, **kwargs: Any) -> List[ParsedRecord]:
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


def parse_record_section(
        record: Record,
        Schema: Schema,
        parser: Callable[[Record, KwArg(Any)], List[ParsedRecord]],
        engine: Engine,
        **kwargs: Any
    ) -> None:
    records_parsed = parser(record, **kwargs)
    for record_parsed in records_parsed:
        with manage_db_session(engine) as session:
            record_object = Schema(**record_parsed)
            session.add(record_object)


def parse_records(
        records: List[Record],
        parser: Callable[[Record, KwArg(Any)], None],
        **kwargs: Any
    ) -> None:
    for record in records:
        parser(record, **kwargs)


def sample_records(records: List[Record], sample_size: Optional[int] = None) -> List[Record]:
    if sample_size:
        records_sample = random.sample(records, sample_size)
    else:
        records_sample = records
    return records_sample


def parse_marcxml(input_file: str, sample_size: Optional[int] = None) -> List[Record]:
    records_input = pymarc.parse_xml_to_array(input_file)
    records_sample = sample_records(records_input, sample_size)
    return records_sample


##########################################################
