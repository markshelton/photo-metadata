##########################################################
# Standard Library Imports

##########################################################
# Third Party Imports

##########################################################
# Local Imports

from thickshake.mtd import import_metadata, export_metadata
from thickshake.utils import get_file_type

##########################################################
# Constants

DETECT_FACES = "DETECT_FACES"
CAPTION_IMAGES = "CAPTION_IMAGES"
READ_TEXT = "READ_TEXT"

##########################################################
# Functions

# Convert metadata files from one format to another
# e.g. MARCXML -> SQL Dump, MARC21 -> HDF5
def convert_metadata_format(input_file: FilePath, output_file: FilePath) -> None:
    if get_file_type(input_file) == get_file_type(output_file): raise
    import_metadata(input_file, db_config)
    export_metadata(output_file, db_config)

# Apply an image processing technique
# (usually involving a pre-trained neural net)
def process_image(image: Image, method: str) -> Image:
    pass

# Apply metadata parsing and image processing techniques
# to add to or improve metadata e.g. subject name, gps coordinates
def augment_metadata(image_dir: DirPath, metadata_file: FilePath, output_file):
    pass

# Train and apply a machine learning classifier
def fit_model(image_dir: DirPath, metadata_file: FilePath, label: str) -> TClassifier:
    pass

class TClassifier():
    def predict(image_file: FilePath, metadata_file: FilePath):
        pass