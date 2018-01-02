##########################################################
# Standard Library Imports

import sys

##########################################################
# Third Party Imports

##########################################################
# Local Imports

sys.path.append("/home/app/src/lib/")

from metadata.parser import parse_marcxml, parse_records
from metadata.db import initialise_db, export_query, manage_db_session

##########################################################
# Environmental Variables

PROJECT_DIRECTORY = "/home/app/src/scripts/old_perth"
OUTPUT_DIRECTORY = "/home/app/data/output/old_perth"
INPUT_MARCXML_FILE = "/home/app/data/input/metadata/marc21.xml"
INPUT_SAMPLE_SIZE = 20

OUTPUT_FILE = "%s/old_perth.json" % (OUTPUT_DIRECTORY)

DB_CONFIG = {}
DB_CONFIG["database"] = ":memory:" #"%s/old_perth.sqlite3" % (OUTPUT_DIRECTORY)
DB_CONFIG["drivername"] = "sqlite"
DB_CONFIG["host"] = None
DB_CONFIG["username"] = None
DB_CONFIG["password"] = None

##########################################################
# Main - Scripts

def get_images(session):
    images = session.query(
        session.query(Image)
        .subquery()
    )
    return images

def main():
    records_sample = parse_marcxml(INPUT_MARCXML_FILE, INPUT_SAMPLE_SIZE)
    db_engine = initialise_db(DB_CONFIG)
    parse_records(records_sample, db_engine)
    with manage_db_session(db_engine) as session:
        query = get_images(session)
        export_query(query, OUTPUT_FILE)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
    main()

##########################################################
# Notes


"""
-- Convert metadata to json 
    -- height
    -- width
    -- date
    -- location (Google Maps Geocoding API)
        -- latitude
        -- longitude
    -- image_url
    -- title
-- Put JSON on basic map website (maybe MapBox?)
"""
