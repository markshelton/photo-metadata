##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

from envparse import env

##########################################################
# Local Imports

from thickshake.mtd import import_metadata, export_metadata
from thickshake.utils import get_file_type, setup_logging, setup_warnings
from thickshake.types import *

##########################################################
# Constants

INPUT_METADATA_FILE = env.str("INPUT_METADATA_FILE") # type: FilePath
OUTPUT_METADATA_FILE = env.str("OUTPUT_METADATA_FILE")

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["drivername"] = env.str("DB_DRIVER")
DB_CONFIG["host"] = env.str("DB_HOST")
DB_CONFIG["database"] = env.str("POSTGRES_DB")
DB_CONFIG["username"] = env.str("POSTGRES_USER")
DB_CONFIG["password"] = env.str("POSTGRES_PASSWORD")

DETECT_FACES = "DETECT_FACES"
CAPTION_IMAGES = "CAPTION_IMAGES"
READ_TEXT = "READ_TEXT"

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions

# Convert metadata files from one format to another
# e.g. MARCXML -> SQL Dump, MARC21 -> HDF5
def convert_metadata_format(
        input_file: FilePath,
        output_file: FilePath,
        db_config: DBConfig=DB_CONFIG,
        **kwargs: Any
    ) -> None:
    if get_file_type(input_file) == get_file_type(output_file):
        logger.error("Input and output file have the same type: %s", get_file_type(input_file))
    logger.info("Starting conversion from %s to %s.", input_file, output_file)
    try:
        #import_metadata(input_file, db_config, **kwargs)
        export_metadata(output_file, db_config, **kwargs)
        logger.info("Conversion from %s to %s completed successfully.", input_file, output_file)
    except:
        logger.error("Conversion from %s to %s failed.", input_file, output_file)


# Apply an image processing technique
# (usually involving a pre-trained neural net)
def process_image(image: Image, method: str) -> Image:
    pass


# Apply metadata parsing and image processing techniques
# to add to or improve metadata e.g. subject name, gps coordinates
def augment_metadata(image_dir: DirPath, metadata_file: FilePath, output_file):
    pass


# Train and apply a machine learning classifier
def fit_model(image_dir: DirPath, metadata_file: FilePath, label: str) -> Any:
    pass


def predict(image_file: FilePath, metadata_file: FilePath) -> Any:
    pass


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