##########################################################
# Standard Library Imports

import sys

##########################################################
# Third Party Imports

##########################################################
# Local Imports

sys.path.append("/home/app/src/lib/")

from metadata.parser import parse_marcxml, parse_records
from metadata.db import initialise_db, manage_db_session, export_query
from metadata.schema import (
    Base, Image, Collection, 
    CollectionLocation, CollectionSubject, CollectionTopic,
)

##########################################################
# Environmental Variables

PROJECT_DIRECTORY = "/home/app/src/scripts/face_recognition"
OUTPUT_DIRECTORY = "/home/app/data/output/face_recognition"
INPUT_MARCXML_FILE = "/home/app/data/input/metadata/marc21.xml"
INPUT_SAMPLE_SIZE = 20

OUTPUT_FILE = "%s/metadata/face_recognition.csv" % (OUTPUT_DIRECTORY)

DB_CONFIG = {}
DB_CONFIG["database"] = ":memory:" #"%s/metadata/face_recognition.sqlite3" % (OUTPUT_DIRECTORY)
DB_CONFIG["drivername"] = "sqlite"
DB_CONFIG["host"] = None
DB_CONFIG["username"] = None
DB_CONFIG["password"] = None

##########################################################
# Main - Scripts

def get_flat_view(session):
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
    )
    return flat_view

def export_flat_view(db_engine, output_file):
    with manage_db_session(db_engine) as session:
        query = get_flat_view(session)
        export_query(query, output_file)

def main():
    records_sample = parse_marcxml(INPUT_MARCXML_FILE, INPUT_SAMPLE_SIZE)
    db_engine = initialise_db(DB_CONFIG)
    parse_records(records_sample, db_engine)
    export_flat_view(db_engine, OUTPUT_FILE)

if __name__ == "__main__":
    import logging
    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
    main()

##########################################################
# Notes
