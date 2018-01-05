##########################################################
# Standard Library Imports

##########################################################
# Third Party Imports

##########################################################
# Local Imports

import sys; sys.path.append("/home/app/src/lib/")

from metadata.parser import (
    parse_images, parse_collection,
    parse_records, parse_record_section,
    parse_marcxml,
)
from metadata.db import (
    initialise_db, manage_db_session, export_records,
)
from metadata.schema import Image
from metadata._types import (
    Any, List, Dict,
    ParsedRecord, DBConfig, FilePath, DirPath,
    Record, Engine,
)

##########################################################
# Environmental Variables

PROJECT_DIRECTORY = "/home/app/src/scripts/old_perth" # type: DirPath
OUTPUT_DIRECTORY = "/home/app/data/output/old_perth" # type: DirPath
INPUT_MARCXML_FILE = "/home/app/data/input/metadata/marc21.xml" # type: FilePath
INPUT_SAMPLE_SIZE = 10 # type: int

FLAG_GEOCODING = True # type: bool
FLAG_DIMENSIONS = True # type: bool

OUTPUT_FILE = "%s/old_perth.json" % (OUTPUT_DIRECTORY) # type: FilePath

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["database"] = "%s/old_perth.sqlite3" % (OUTPUT_DIRECTORY) # type: str
DB_CONFIG["drivername"] = "sqlite" # type: str
DB_CONFIG["host"] = None # type: Optional[str]
DB_CONFIG["username"] = None # type: Optional[str]
DB_CONFIG["password"] = None # type: Optional[str]

##########################################################


def reformat_for_old_perth(records: List[ParsedRecord]) -> List[ParsedRecord]:
    records_out = [
        {
            "text": None,
            "height": getattr(record, "image_height"),
            "date": getattr(record, "image_date_created"),
            "thumb_url": getattr(record, "image_url_thumb"),
            "photo_id": getattr(record, "image_id"),
            "title": getattr(record, "image_note").split(":")[1].strip(),
            "width": getattr(record, "image_width"),
            "image_url": getattr(record, "image_url_raw"),
            "location": {
                "lat": getattr(record, "image_latitude"),
                "lon": getattr(record, "image_longitude")
            },
            "folder": None,
            "years": [""]
        } for record in records if getattr(record, "image_latitude") is not None
    ]
    return records_out


def get_query_results(db_engine: Engine) -> List[ParsedRecord]:
    with manage_db_session(db_engine) as session:
        images = session.query(
            session.query(Image)
            .subquery()
        ).all()
        #TODO -> Convert to dict
    return images


def prepare_records_for_export(db_engine: Engine) -> List[ParsedRecord]:
    records_raw = get_query_results(db_engine)
    records_clean = reformat_for_old_perth(records_raw)
    return records_clean


##########################################################


def collect_images(record: Record, **kwargs: Any) -> List[ParsedRecord]:
    images_data = parse_images(record, **kwargs)
    collection_data = parse_collection(record, **kwargs)
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
            "collection_id": collection_data["collection_id"],
        } for image in images_data
    ]
    return images


##########################################################


def parse_record(record: Record, **kwargs: Any) -> None:
    parse_record_section(record, Image, collect_images, **kwargs)


##########################################################


def main():
    records_sample = parse_marcxml(INPUT_MARCXML_FILE, INPUT_SAMPLE_SIZE)
    db_engine = initialise_db(DB_CONFIG) #TODO: SCHEMA_CONFIG
    parse_records(records_sample, parse_record, engine=db_engine,
                  geocoding_flag=FLAG_GEOCODING, dimensions_flag=FLAG_DIMENSIONS
                 )
    records_out = prepare_records_for_export(db_engine)
    export_records(records_out, OUTPUT_FILE)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
    logger = logging.getLogger("__name__")
    main()


##########################################################
# Notes
