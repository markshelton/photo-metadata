##########################################################
# Standard Library Imports

##########################################################
# Third Party Imports

##########################################################
# Local Imports

from thickshake.types import *

##########################################################
# Constants


##########################################################
# Functions


# Apply 
def process_images(image_dir: DirPath, output_file: FilePath, **kwargs: Any) -> None:
    image_files = get_files_in_directory(input_images_dir, **kwargs)
    for image_file in image_files:
        extract_faces_from_image(image_file, output_file)
        extract_text_from_image(image_file, output_file)
        caption_image(image_file, output_file)




##########################################################
# Functions

