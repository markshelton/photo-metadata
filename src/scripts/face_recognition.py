##########################################################
# Standard Library Imports

import sys

##########################################################
# Third Party Imports

from pymarc import Record
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

##########################################################
# Local Imports

sys.path.append("/home/app/src/lib/")

from parser import (
    parse_collection, parse_images,
    parse_topics, parse_locations, parse_subjects,
    parse_records, parse_record_section,
    parse_marcxml, deep_get, logged
)
from database import (
    initialise_db, manage_db_session, export_records,
)
from schema import (
    Image, Collection, Subject,
    CollectionLocation, CollectionSubject, CollectionTopic,
)
from _types import (
    Any, List, Dict, Optional,
    ParsedRecord, DBConfig, DirPath, FilePath,
    Record, Engine,
)

##########################################################
# Environmental Variables

PROJECT_DIRECTORY = "/home/app/src/scripts/face_recognition" # type: DirPath
OUTPUT_DIRECTORY = "/home/app/data/output/face_recognition" # type: DirPath
INPUT_MARCXML_FILE = "/home/app/data/input/metadata/marc21.xml" # type: FilePath
INPUT_SAMPLE_SIZE = 20 # type: Optional[int]

FLAG_GEOCODING = False # type: bool
FLAG_DIMENSIONS = False # type: bool

OUTPUT_FILE = "%s/metadata/face_recognition.csv" % (OUTPUT_DIRECTORY)

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["database"] = "%s/metadata/face_recognition.sqlite3" % (OUTPUT_DIRECTORY)
DB_CONFIG["drivername"] = "sqlite"
DB_CONFIG["host"] = None
DB_CONFIG["username"] = None
DB_CONFIG["password"] = None

##########################################################

@logged
def get_query_results(db_engine: Engine) -> List[ParsedRecord]:
    with manage_db_session(db_engine) as session:
        collection_plus = (
            session.query(
                Collection, CollectionSubject, CollectionLocation, CollectionTopic
            )
            .join(CollectionSubject, isouter=True)
            .join(CollectionLocation, isouter=True)
            .join(CollectionTopic, isouter=True)
            .subquery()
        )
        flat_view = session.query(
            session.query(Image, collection_plus)
            .join(collection_plus, isouter=True)
            .subquery()
        ).all()
    flat_view = [record._asdict() for record in flat_view]
    return flat_view


##########################################################

@logged
def collect_collection_data(record: Record, **kwargs: Any) -> List[ParsedRecord]:
    collection_data = parse_collection(record, **kwargs)
    collection = [collection_data]
    return collection

@logged
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

@logged
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

@logged
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

@logged
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

@logged
def collect_images(record: Record, **kwargs: Any) -> List[ParsedRecord]:
    images_raw = parse_images(record, **kwargs)
    collection_raw = parse_collection(record, **kwargs)
    images = [] # type: List[ParsedRecord]
    for image_raw in images_raw:
        image = {
            "image_id": image_raw["image_id"],
            "image_note": image_raw["image_note"],
            "image_date_created": image_raw["image_date_created"],
            "collection_id": collection_raw["collection_id"],
        }
        images.append(image)
    return images


##########################################################

@logged
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
    records_sample = parse_marcxml(INPUT_MARCXML_FILE, INPUT_SAMPLE_SIZE)
    db_engine = initialise_db(DB_CONFIG)
    parse_records(records_sample, parse_record, engine=db_engine, geocoding=FLAG_GEOCODING, dimensions=FLAG_DIMENSIONS)
    records_out = get_query_results(db_engine)
    export_records_to_csv(records_out, OUTPUT_FILE)


def setup_logging() -> None:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARN)
    logging.getLogger("PIL.Image").setLevel(logging.INFO)
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)
    logging.getLogger("datefinder").setLevel(logging.INFO)


def setup_warnings() -> None:
    import warnings
    import sqlalchemy
    warnings.filterwarnings("ignore", category=sqlalchemy.exc.SAWarning)


if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()


##########################################################
# Notes
