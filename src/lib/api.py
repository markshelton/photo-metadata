##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

from envparse import env

##########################################################
# Local Imports

from thickshake.utils import setup_logging, setup_warnings
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


# Apply metadata parsing and image processing techniques
# to add to or improve metadata e.g. subject name, gps coordinates
def augment_metadata(
        image_dir: DirPath,
        input_metadata_file: FilePath,
        output_metadata_file: FilePath,
        output_diff_file: FilePath,
    ) -> None:
    import_metadata(input_metadata_file)
    export_metadata(internal_metadata_file)
    


# Find appearances of a face in the photo
# archive and if possible identify the face
def find_matching_faces(
        face_file: FilePath,
        image_dir: DirPath,
        metadata_file: FilePath,
    ) -> Tuple[Any, List[Any]]:
    pass


# Find similar images in the photo archive 
def find_similar_images(
        image_file: FilePath,
        image_dir: DirPath,
        metadata_file: FilePath
    ) -> List[Any]:
    pass


##########################################################
# Main

def main():
    pass

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()