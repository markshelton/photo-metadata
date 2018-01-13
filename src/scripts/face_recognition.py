##########################################################
# Standard Library Imports

import os

##########################################################
# Third Party Imports

from envparse import env
from pymarc import Record

##########################################################
# Local Imports

from thickshake.mtd.parse import (
    parse_collection, parse_images,
    parse_topics, parse_locations, parse_subjects,
    parse_record_section, load_marcxml
)
from thickshake.mtd.schema import (
    Image, Collection, Subject,
    CollectionLocation, CollectionSubject, CollectionTopic,
)
from thickshake.utils import setup_warnings, setup_logging, deep_get
from thickshake._types import Any, List, Optional, ParsedRecord, DBConfig, FilePath

##########################################################
# Environmental Variables

INPUT_METADATA_FILE = env.str("INPUT_METADATA_FILE") # type: FilePath

FLAG_MTD_GEOCODING = env.bool("FLAG_MTD_GEOCODING", default=False) # type: bool
FLAG_MTD_DIMENSIONS = env.bool("FLAG_MTD_DIMENSIONS", default=False) # type: bool
FLAG_MTD_LOGGING = env.bool("FLAG_MTD_LOGGING", default=False) # type: bool
FLAG_MTD_SAMPLE = env.int("FLAG_MTD_SAMPLE", default=0) # type: int

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["drivername"] = env.str("DB_DRIVER", default="postgres")
DB_CONFIG["host"] = env.str("DB_HOST", default="thickshake_database_1")
DB_CONFIG["database"] = env.str("POSTGRES_DB", default="postgres")
DB_CONFIG["username"] = env.str("POSTGRES_USER", default="postgres")
DB_CONFIG["password"] = env.str("POSTGRES_PASSWORD", default="thickshake")

##########################################################

def collect_collection_data(record: Record, **kwargs: Any) -> List[ParsedRecord]:
    collection_data = parse_collection(record, **kwargs)
    collection = [collection_data]
    return collection

def collect_collection_topics(record: Record, **kwargs: Any) -> List[ParsedRecord]:
    topics = parse_topics(record, **kwargs)
    collection_data = parse_collection(record, **kwargs)
    collection_topics = [
        {
            "collection_id": collection_data["collection_id"],
            "topic": topic,
        } for topic in topics
    ]
    return collection_topics

def collect_collection_locations(record: Record, **kwargs: Any) -> List[ParsedRecord]:
    locations = parse_locations(record, **kwargs)
    collection_data = parse_collection(record, **kwargs)
    collection_locations = [
        {
            "collection_id": collection_data["collection_id"],
            "location": location,
        } for location in locations
    ]
    return collection_locations

def collect_subjects(record: Record, **kwargs: Any) -> List[ParsedRecord]:
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

def collect_collection_subjects(record: Record, **kwargs: Any) -> List[ParsedRecord]:
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

def collect_images(record: Record, **kwargs: Any) -> List[ParsedRecord]:
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

def parse_record(record: Record, **kwargs: Any) -> None:
    parse_record_section(record, Collection, collect_collection_data, **kwargs)
    parse_record_section(record, CollectionTopic, collect_collection_topics, **kwargs)
    parse_record_section(record, CollectionLocation, collect_collection_locations, **kwargs)
    parse_record_section(record, Subject, collect_subjects, **kwargs)
    parse_record_section(record, CollectionSubject, collect_collection_subjects, **kwargs)
    parse_record_section(record, Image, collect_images, **kwargs)


##########################################################
# Main


def main() -> None:
    load_marcxml(
        input_file=INPUT_METADATA_FILE,
        record_parser=parse_record, #TODO: Find way to configure through env variables
        db_config=DB_CONFIG,
        geocoding=FLAG_MTD_GEOCODING,
        dimensions=FLAG_MTD_DIMENSIONS,
        logging_flag=FLAG_MTD_LOGGING,
        sample_size=FLAG_MTD_SAMPLE
    )

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()


##########################################################
# Notes
