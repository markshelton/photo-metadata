##########################################################
# Standard Library Imports

import logging
import re
import random
import datetime
import collections
import urllib

##########################################################
# Third Party Imports

import pymarc
import datefinder
from PIL import ImageFile

##########################################################
# Local Imports

from metadata.schema import (
    Collection, Subject, Image,
    CollectionSubject, CollectionTopic, CollectionLocation,
)
from metadata.db import manage_db_session
from metadata.ext.geocoder import resolve_location

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


def remove_nulls(full_list):
    if full_list and isinstance(full_list, list):
        non_null_list = [x for x in full_list if x is not None]
    else:
        non_null_list = []
    return non_null_list


def consolidate_list(full_list):
    consolidated_list = remove_nulls(full_list)
    return consolidated_list

##########################################################


def get_subfield_from_field(field, subfield_key):
    if subfield_key:
        if subfield_key in field:
            subfield = field[subfield_key]
        else:
            subfield = None
    else:
        subfield = field.value()
    return subfield


def get_subfield_from_record(record, field_key, subfield_key):
    if field_key in record:
        field = record[field_key]
        subfield = get_subfield_from_field(field, subfield_key)
    else:
        subfield = None
    return subfield


def get_subfields(record, field_key, subfield_key):
    fields = record.get_fields(field_key)
    subfields = [
        get_subfield_from_field(
            field,
            subfield_key) for field in fields]
    return subfields


def parse_tag_key(tag_key):
    if TAG_DELIMITER in tag_key:
        field_key, subfield_key = tag_key.split(TAG_DELIMITER)
    else:
        field_key, subfield_key = tag_key, None
    return field_key, subfield_key


def get_subfield_from_tag(record_or_field, tag_key):
    field_key, subfield_key = parse_tag_key(tag_key)
    if isinstance(record_or_field, pymarc.Record):
        subfield = get_subfield_from_record(
            record_or_field, field_key, subfield_key)
    elif isinstance(record_or_field, pymarc.Field):
        subfield = get_subfield_from_field(record_or_field, subfield_key)
    else:
        subfield = None
    return subfield


def get_subfields_from_tag(record, tag_key):
    field_key, subfield_key = parse_tag_key(tag_key)
    subfields_raw = get_subfields(record, field_key, subfield_key)
    subfields = consolidate_list(subfields_raw)
    return subfields


def get_fields_from_tag(record, tag_key):
    field_key, _ = parse_tag_key(tag_key)
    fields = record.get_fields(field_key)
    return fields

##########################################################


def get_possible_dates(field):
    if field:
        years = re.findall(".*([1-2][0-9]{3})", field)
        dates = [datetime.date(year=int(year), month=1, day=1)
                 for year in years]
        if not dates:
            dates = list(datefinder.find_dates(field))
    else:
        dates = None
    return dates


def select_date(possible_dates, method="first"):
    if possible_dates:
        if method == "first":
            selected_date = possible_dates[0]
        elif method == "last":
            selected_date = possible_dates[-1]
        else:
            selected_date = None
        if len(possible_dates) > 1:
            ignored_dates = possible_dates - selected_date
            logger.warning("Multiple matching dates. \
                Selected: %s. Ignored: %s",
                           selected_date, ignored_dates)
    else:
        selected_date = None
    return selected_date


def extract_date_from_field(field, method="first"):
    possible_dates = get_possible_dates(field)
    selected_date = select_date(possible_dates, method=method)
    return selected_date


def get_date_collection_created(record):
    date_created_raw = get_subfield_from_tag(record, TAG_DATE_CREATED)
    date_created_approx_raw = get_subfield_from_tag(
        record, TAG_DATE_CREATED_APPROX)
    if date_created_raw:
        date_created = extract_date_from_field(date_created_raw)
    elif date_created_approx_raw:
        date_created = extract_date_from_field(date_created_approx_raw)
    else:
        date_created = None
    return date_created


def get_topics(record):
    topics_raw = get_subfields_from_tag(record, TAG_TOPIC)
    topics = consolidate_list(topics_raw)
    return topics


def get_locations(record):
    location_divisions_raw = get_subfields_from_tag(
        record, TAG_LOCATION_DIVISION)
    location_names_raw = get_subfields_from_tag(record, TAG_LOCATION_NAME)
    locations = consolidate_list(
        [*location_divisions_raw, *location_names_raw])
    return locations


def split_dates(record, dates_tag):
    dates_raw = get_subfield_from_tag(record, dates_tag)
    dates = {"start": None, "end": None}
    if dates_raw:
        dates_num = len(dates_raw.split("-"))
        if dates_num >= 2:
            date_start_raw, date_end_raw, *_ = dates_raw.split("-")
            dates["start"] = extract_date_from_field(
                date_start_raw, method="first")
            dates["end"] = extract_date_from_field(date_end_raw, method="last")
        elif dates_num == 1:
            date_start_raw = dates_raw.split("-")[0]
            dates["start"] = extract_date_from_field(
                date_start_raw, method="first")
    return dates


def get_main_person(record):
    subject_name = get_subfield_from_tag(record, TAG_SUBJECT_PERSON_NAME_MAIN)
    if subject_name:
        main_person = {
            "subject_name": get_subfield_from_tag(record, TAG_SUBJECT_PERSON_NAME_MAIN),
            "subject_relation": get_subfield_from_tag(record, TAG_SUBJECT_PERSON_RELATION_MAIN),
            "subject_dates": split_dates(record, TAG_SUBJECT_PERSON_DATES_MAIN),
            "subject_type": "Person",
            "subject_is_main": True,
        }
    else:
        main_person = None
    return main_person


def get_main_company(record):
    subject_name = get_subfield_from_tag(record, TAG_SUBJECT_COMPANY_NAME_MAIN)
    if subject_name:
        main_company = {
            "subject_name": get_subfield_from_tag(record, TAG_SUBJECT_COMPANY_NAME_MAIN),
            "subject_relation": get_subfield_from_tag(record, TAG_SUBJECT_COMPANY_RELATION_MAIN),
            "subject_dates": {"start": None, "end": None},
            "subject_type": "Person",
            "subject_is_main": True,
        }
    else:
        main_company = None
    return main_company


def get_other_people(record):
    other_people_raw = get_fields_from_tag(
        record, TAG_SUBJECT_PERSON_NAME_OTHER)
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


def get_other_companies(record):
    other_companies_raw = get_fields_from_tag(
        record, TAG_SUBJECT_COMPANY_NAME_OTHER)
    other_companies = [
        {
            "subject_name": get_subfield_from_tag(company, TAG_SUBJECT_COMPANY_NAME_MAIN),
            "subject_relation": get_subfield_from_tag(company, TAG_SUBJECT_COMPANY_RELATION_MAIN),
            "subject_dates": {"start": None, "end": None},
            "subject_type": "Company",
            "subject_is_main": False,
        } for company in other_companies_raw
    ]
    return other_companies


def get_subjects(record):
    main_person = get_main_person(record)
    main_company = get_main_company(record)
    other_people = get_other_people(record)
    other_companies = get_other_companies(record)
    subjects = consolidate_list([
        main_person, main_company,
        *other_people, *other_companies
    ])
    return subjects


def get_id_from_url(image):
    image_url = get_subfield_from_tag(image, TAG_IMAGE_URL)
    if image_url:
        image_id = image_url.split("/")[-1].split(".")[0]
    else:
        image_id = None
    return image_id


def get_image_size(image_url):
    try:
        with urllib.request.urlopen(image_url) as image_file:
            p = ImageFile.Parser()
            while True:
                data = image_file.read(1024)
                if not data:
                    break
                p.feed(data)
                if p.image:
                    return p.image.size
            return None
    except urllib.error.URLError:
        log.warning("Image not found. Size could not be determined.")


def get_dimensions(image):
    dimensions = {"width": None, "height": None}
    image_url = get_subfield_from_tag(image, TAG_IMAGE_URL) + ".jpg"
    image_size = get_image_size(image_url)
    if image_size:
        width, height = image_size
        dimensions = {"width": width, "height": height}
    return dimensions


def get_coordinates(image):
    coordinates = {"latitude": None, "longitude": None}
    image_note = get_subfield_from_tag(image, TAG_IMAGE_NOTE)
    if image_note:
        geocoding_details = resolve_location(image_note)
        if geocoding_details:
            coordinates["latitude"] = geocoding_details["latitude"]
            coordinates["longitude"] = geocoding_details["longitude"]
    return coordinates


def get_date_image_created(image):
    image_note = get_subfield_from_tag(image, TAG_IMAGE_NOTE)
    date_created = extract_date_from_field(image_note)
    return date_created


def get_images(record):
    images_raw = get_fields_from_tag(record, TAG_IMAGE_URL)
    images = [
        {
            "image_id": get_id_from_url(image),
            "image_url_main": get_subfield_from_tag(image, TAG_IMAGE_URL),
            "image_url_raw": get_subfield_from_tag(image, TAG_IMAGE_URL) + ".jpg",
            "image_url_thumb": get_subfield_from_tag(image, TAG_IMAGE_URL) + ".png",
            "image_note": get_subfield_from_tag(image, TAG_IMAGE_NOTE),
            "image_dimensions": get_dimensions(image),
            "image_coordinates": get_coordinates(image),
            "image_date_created": get_date_image_created(image),
        } for image in images_raw
    ]
    consolidate_list(images)
    return images

##########################################################


def parse_collection(record):
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


def parse_collection_topics(record):
    topics = get_topics(record)
    collection_topics = [
        {
            "collection_id": get_subfield_from_tag(record, TAG_COLLECTION_ID),
            "topic": topic,
        } for topic in topics
    ]
    return collection_topics


def parse_collection_locations(record):
    locations = get_locations(record)
    collection_locations = [
        {
            "collection_id": get_subfield_from_tag(record, TAG_COLLECTION_ID),
            "location": location,
        } for location in locations
    ]
    return collection_locations


def parse_subjects(record):
    subjects_data = get_subjects(record)
    subjects = [
        {
            "subject_name": subject["subject_name"],
            "subject_type": subject["subject_type"],
            "subject_start_date": subject["subject_dates"]["start"],
            "subject_end_date": subject["subject_dates"]["end"],
        } for subject in subjects_data
    ]
    return subjects


def parse_collection_subjects(record):
    subjects_data = get_subjects(record)
    collection_subjects = [
        {
            "collection_id": get_subfield_from_tag(record, TAG_COLLECTION_ID),
            "subject_name": subject["subject_name"],
            "subject_relation": subject["subject_relation"],
            "subject_is_main": subject["subject_is_main"],
        } for subject in subjects_data
    ]
    return collection_subjects


def parse_images(record):
    images_data = get_images(record)
    images = [
        {
            "image_id": image["image_id"],
            "image_url_main": image["image_url_main"],
            "image_url_raw": image["image_url_raw"],
            "image_url_thumb": image["image_url_thumb"],
            "image_note": image["image_note"],
            "image_width": image["image_dimensions"]["width"],
            "image_height": image["image_dimensions"]["height"],
            "image_longitude": image["image_coordinates"]["longitude"],
            "image_latitude": image["image_coordinates"]["latitude"],
            "image_date_created": image["image_date_created"],
            "collection_id": get_subfield_from_tag(record, TAG_COLLECTION_ID),
        } for image in images_data
    ]
    return images

##########################################################


def add_collection_topic(collection_topic, db_engine):
    with manage_db_session(db_engine) as session:
        db_collection_topic = CollectionTopic(**collection_topic)
        session.add(db_collection_topic)


def add_collection_location(collection_location, db_engine):
    with manage_db_session(db_engine) as session:
        db_collection_location = CollectionLocation(**collection_location)
        session.add(db_collection_location)


def add_subject(subject, db_engine):
    with manage_db_session(db_engine) as session:
        db_subject = Subject(**subject)
        session.add(db_subject)


def add_collection_subject(collection_subject, db_engine):
    with manage_db_session(db_engine) as session:
        db_collection_subject = CollectionSubject(**collection_subject)
        session.add(db_collection_subject)


def add_image(image, db_engine):
    with manage_db_session(db_engine) as session:
        db_image = Image(**image)
        session.add(db_image)

##########################################################


def add_collection(record, db_engine):
    collection = parse_collection(record)
    with manage_db_session(db_engine) as session:
        db_collection = Collection(**collection)
        session.add(db_collection)


def add_collection_topics(record, db_engine):
    collection_topics = parse_collection_topics(record)
    for collection_topic in collection_topics:
        add_collection_topic(collection_topic, db_engine)


def add_collection_locations(record, db_engine):
    collection_locations = parse_collection_locations(record)
    for collection_location in collection_locations:
        add_collection_location(collection_location, db_engine)


def add_subjects(record, db_engine):
    subjects = parse_subjects(record)
    for subject in subjects:
        add_subject(subject, db_engine)


def add_collection_subjects(record, db_engine):
    collection_subjects = parse_collection_subjects(record)
    for collection_subject in collection_subjects:
        add_collection_subject(collection_subject, db_engine)


def add_images(record, db_engine):
    images = parse_images(record)
    for image in images:
        add_image(image, db_engine)

##########################################################


def parse_record(record, db_engine):
    add_collection(record, db_engine)
    add_collection_topics(record, db_engine)
    add_collection_locations(record, db_engine)
    add_subjects(record, db_engine)
    add_collection_subjects(record, db_engine)
    add_images(record, db_engine)


def sample_records(records, sample_size):
    if sample_size:
        records_sample = random.sample(records, sample_size)
    else:
        records_sample = records
    return records_sample


def parse_records(records, db_engine):
    total = len(records)
    for i, record in enumerate(records):
        logger.info("Records Processed: %s out of %s.", i + 1, total)
        parse_record(record, db_engine)


def parse_marcxml(input_file, sample_size=None):
    records_input = pymarc.parse_xml_to_array(input_file)
    records_sample = sample_records(records_input, sample_size)
    return records_sample

##########################################################
