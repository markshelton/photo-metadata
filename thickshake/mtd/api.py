##########################################################
# Standard Library Imports

import enum
import logging
import os

##########################################################
# Third Party Imports

from envparse import env

##########################################################
# Local Imports

from thickshake.mtd.database import dump_database, initialise_db
from thickshake.mtd.reader import load_database, read_file
from thickshake.mtd.writer import write_file
from thickshake.utils import setup_logging, setup_warnings
from thickshake.types import *

##########################################################
# Constants

INPUT_METADATA_FILE = env.str("INPUT_METADATA_FILE", default="") # type: FilePath
OUTPUT_METADATA_FILE = env.str("OUTPUT_METADATA_FILE", default="")

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["drivername"] = env.str("DB_DRIVER")
DB_CONFIG["host"] = env.str("DB_HOST")
DB_CONFIG["database"] = env.str("POSTGRES_DB")
DB_CONFIG["username"] = env.str("POSTGRES_USER")
DB_CONFIG["password"] = env.str("POSTGRES_PASSWORD")


##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)


##########################################################
# Functions


# Import metadata files from any format to RDBMS
def import_metadata(input_file: FilePath, db_config: DBConfig=DB_CONFIG, **kwargs: Any) -> None:
    assert os.path.exists(input_file)
    records = read_file(input_file, **kwargs)
    load_database(records, db_config, **kwargs)


# Export metadata records from RDBMS to any format
def export_metadata(output_file: FilePath, db_config: DBConfig=DB_CONFIG, **kwargs: Any) -> None:
    assert not os.path.exists(output_file)
    records = dump_database(db_config, **kwargs)
    write_file(records, output_file, **kwargs)


# Convert metadata files from one format to another
# e.g. MARCXML -> SQL Dump, MARC21 -> HDF5
def convert_metadata_format(
        input_file: FilePath,
        output_file: FilePath,
        db_config: DBConfig=DB_CONFIG,
        **kwargs: Any
    ) -> None:
    import_metadata(input_file, db_config, **kwargs)
    export_metadata(output_file, db_config, **kwargs)


##########################################################
# Main

def main():
    convert_metadata_format(
        input_file=INPUT_METADATA_FILE,
        output_file="/home/app/data/output/metadata.csv",
        sample_size=20,
        logging_flag=True,
        clear_flag=True,
    )

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()