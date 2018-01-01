##########################################################
# Standard Library Imports

import logging
import re
import sys
from random import sample
from datetime import date
from collections import Hashable

##########################################################
# Third Party Imports

from pymarc import parse_xml_to_array, Record, Field
from datefinder import find_dates

##########################################################
# Local Imports

from db import (
    make_db_engine,
    make_db_tables,
    export_db_records
)

##########################################################
# Environmental Variables

LOGGING_BASIC_LEVEL = logging.DEBUG
LOGGING_DB_LEVEL = logging.INFO

INPUT_MARCXML_FILE = "/home/app/data/input/metadata/marc21.xml"
INPUT_SAMPLE_SIZE = 20

OUTPUT_CSV_FILE = "/home/app/data/output/metadata/marc21.csv"

DB_CONFIG = {}
#DB_CONFIG["database"] = "/home/app/data/output/metadata/metadata.sqlite3"

def configure_database(
        drivername="sqlite",
        host=None,
        username=None,
        password=None,
        database=":memory:"
    ):
    return {
        "drivername": drivername,
        "host": host,
        "username": username,
        "password": password,
        "database": database,
    }

DATABASE = configure_database(**DB_CONFIG)

##########################################################
# Logging Configuration

logging.basicConfig(level=LOGGING_BASIC_LEVEL, stream=sys.stdout)
logging.getLogger('sqlalchemy.engine').setLevel(LOGGING_DB_LEVEL)
logger = logging.getLogger(__name__)

##########################################################
# Main - Scripts

if __name__ == "__main__":
    records_input = parse_xml_to_array(input_file)
    records_sample = sample_records(records_input, sample_size)
    db_engine = make_db_engine(db_config)
    parse_records(records_sample, db_engine)
    export_query(db_engine, output_file)

##########################################################
# Notes
