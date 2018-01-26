# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

##########################################################
# Local Imports

from thickshake.metadata.metadata import (
    import_metadata, export_metadata,
)
from thickshake.utils import (
    setup, generate_diff, generate_output_path,
)

##########################################################
# Typing Configuration

from typing import Any, List, Optional, Tuple, Dict
from mypy_extensions import TypedDict

DBConfig = Dict[str, Optional[str]]
FilePath = str
DirPath = str

##########################################################
# Constants

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


# Apply metadata parsing and image processing techniques
# to add to or improve metadata e.g. subject name, gps coordinates
def augment_metadata(
        input_metadata_file: FilePath,
        output_metadata_file: FilePath = None,
        input_image_dir: DirPath = None,
        diff: bool = True,
        **kwargs
    ) -> None:
    if output_metadata_file is None:
        output_metadata_file = generate_output_path(input_metadata_file)
    import_metadata(input_metadata_file, **kwargs)
    apply_parsers(**kwargs)
    process_images(input_image_dir, **kwargs)
    export_metadata(output_metadata_file, **kwargs)
    if diff: generate_diff(input_metadata_file, output_metadata_file)
    

# Find appearances of a face in the photo
# archive and if possible identify the face
def find_matching_faces(
        input_face_file: FilePath,
        input_metadata_file: FilePath,
        input_image_dir: DirPath,
        **kwargs
    ) -> Tuple[Any, List[Any]]:
    pass


# Find similar images in the photo archive 
def find_similar_images(
        input_image_file: FilePath,
        input_metadata_file: FilePath,
        input_image_dir: DirPath,
        **kwargs
    ) -> List[Any]:
    pass


# Apply 
def process_images(
        input_image_dir: DirPath,
        output_image_dir: FilePath = None,
        **kwargs
    ) -> None:
    image_files = get_files_in_directory(input_image_dir, **kwargs)
    for image_file in image_files:
        if output_image_dir is not None:
            output_file = generate_output_path(image_file, output_image_dir)
        else: output_file = None
        extract_faces_from_image(image_file, output_file, **kwargs)
        extract_text_from_image(image_file, output_file, **kwargs)
        caption_image(image_file, output_file, **kwargs)


# Convert metadata files from one format to another
# e.g. MARCXML -> SQL Dump, MARC21 -> HDF5
def convert_metadata(
        input_metadata_file: FilePath,
        output_metadata_file: FilePath,
        **kwargs
    ) -> None:
    import_metadata(input_metadata_file, **kwargs)
    export_metadata(output_metadata_file, **kwargs)


##########################################################
# Main

def main():
    pass

if __name__ == "__main__":
    setup()
    main()


##########################################################
