##########################################################
# Standard Library Imports

import sys

##########################################################
# Third Party Imports

##########################################################
# Local Imports

sys.path.append("/home/app/src/lib/")

from metadata.parser import parse_marcxml, add_images
from metadata.db import (
    initialise_db, manage_db_session, export_records,
)
from metadata.schema import Image

##########################################################
# Environmental Variables

PROJECT_DIRECTORY = "/home/app/src/scripts/old_perth"
OUTPUT_DIRECTORY = "/home/app/data/output/old_perth"
INPUT_MARCXML_FILE = "/home/app/data/input/metadata/marc21.xml"
INPUT_SAMPLE_SIZE = 10

OUTPUT_FILE = "%s/old_perth.json" % (OUTPUT_DIRECTORY)

DB_CONFIG = {}
DB_CONFIG["database"] = "%s/old_perth.sqlite3" % (OUTPUT_DIRECTORY) #":memory:" #
DB_CONFIG["drivername"] = "sqlite"
DB_CONFIG["host"] = None
DB_CONFIG["username"] = None
DB_CONFIG["password"] = None

##########################################################
# Main - Scripts

def parse_records(records, db_engine):
    total = len(records)
    for i, record in enumerate(records):
        logger.info("Records Processed: %s out of %s.", i+1, total)
        add_images(record, db_engine)

def get_query_results(db_engine):
    with manage_db_session(db_engine) as session:
        images = session.query(
            session.query(Image)
            .subquery()
        ).all()
    return images

def reformat_for_old_perth(records):
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

def prepare_records_for_export(db_engine):
    records_raw = get_query_results(db_engine)
    records_clean = reformat_for_old_perth(records_raw)
    return records_clean

def main():
    records_sample = parse_marcxml(INPUT_MARCXML_FILE, INPUT_SAMPLE_SIZE)
    db_engine = initialise_db(DB_CONFIG)
    parse_records(records_sample, db_engine)
    records_out = prepare_records_for_export(db_engine)
    export_records(records_out, OUTPUT_FILE)
    
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    #logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
    logger = logging.getLogger("__name__")
    main()

##########################################################
# Notes