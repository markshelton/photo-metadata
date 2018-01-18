##########################################################
# Standard Library Imports

import enum
import os

##########################################################
# Third Party Imports

from envparse import env

##########################################################
# Local Imports

from thickshake.mtd.database import dump_database
from thickshake.mtd.reader import load_database, read_file
from thickshake.mtd.writer import write_file
from thickshake.utils import setup_logging, setup_warnings
from thickshake.types import *

##########################################################
# Constants

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["drivername"] = env.str("DB_DRIVER")
DB_CONFIG["host"] = env.str("DB_HOST")
DB_CONFIG["database"] = env.str("POSTGRES_DB")
DB_CONFIG["username"] = env.str("POSTGRES_USER")
DB_CONFIG["password"] = env.str("POSTGRES_PASSWORD")

class FileType:
    JSON = ".json"
    HDF5 = ".hdf5"
    MARC21 = ".marc"
    MARCXML = ".xml"
    CSV = ".csv"


##########################################################
# Functions


# Import metadata files from any format to RDBMS
def import_metadata(input_file: FilePath, db_config: DBConfig=DB_CONFIG, **kwargs: Any) -> None:
    if not os.path.exists(input_file):
        logger.error("Input file (%s) does not exist.", input_file)
    try:
        logger.info("Importing metadata to database from %s.", input_file)
        records = read_file(input_file, **kwargs)
        load_database(records, db_config, **kwargs)
        logger.info("Import from %s completed successfully.", input_file)
    except:
        logger.error("Import from %s failed.", input_file)


# Export metadata records from RDBMS to any format
def export_metadata(output_file: FilePath, db_config: DBConfig=DB_CONFIG,, **kwargs: Any) -> None:
    if os.path.exists(output_file):
        logger.error("Output file (%s) already exists.", output_file)
    try:
        logger.info("Exporting metadata from database to %s.", output_file)
        records = dump_database(db_config, **kwargs)
        write_file(records, output_file, **kwargs)
        logger.info("Export to %s completed successfully.", output_file)
    except:
        logger.error("Export to %s failed.", output_file)


# Convert metadata files from one format to another
# e.g. MARCXML -> SQL Dump, MARC21 -> HDF5
def convert_metadata_format(
        input_file: FilePath,
        output_file: FilePath,
        db_config: DBConfig=DB_CONFIG,
        **kwargs: Any
    ) -> None:
    try:
        logger.info("Starting conversion from %s to %s.", input_file, output_file)
        import_metadata(input_file, db_config, **kwargs)
        export_metadata(output_file, db_config, **kwargs)
        logger.info("Conversion from %s to %s completed successfully.", input_file, output_file)
    except:
        logger.error("Conversion from %s to %s failed.", input_file, output_file)


##########################################################
# Main

def main():
    convert_metadata_format(
        input_file=INPUT_METADATA_FILE,
        output_file=OUTPUT_METADATA_FILE
    )

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()