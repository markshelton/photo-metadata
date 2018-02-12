# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Python Compatibility

from __future__ import print_function, division, absolute_import
from builtins import dict
from future import standard_library
standard_library.install_aliases()

##########################################################
# Standard Library Imports

import logging
from collections import OrderedDict

##########################################################
# Third Party Imports

from envparse import env
import pandas as pd
from tqdm import tqdm

##########################################################
# Local Imports

from thickshake.storage import Store, Database

##########################################################
# Typing Configuration

from typing import Text, List, Any, Union, Dict, Callable, AnyStr
Parser = Any
FilePath = Text
DirPath = Text
DataFrame = Any
Series = Any

##########################################################
# Constants

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Wrappers


def process_wrapper(main_function, main_path, storage_map, output_map=None, dependencies=None, force=False, **kwargs):
    # type: (Callable, AnyStr, Dict[AnyStr, AnyStr], Dict[AnyStr, AnyStr], List[Callable], bool, **Any) -> None
    store = Store(force=force, **kwargs)
    if dependencies is None: dependencies = []
    if force or not store.contains(main_path):
        if any(not store.contains(path) for _, path in storage_map.items()):
            for dependency_function in dependencies:
                dependency_function(force=force, **kwargs)
        main_function(storage_map=storage_map, force=force, **kwargs)
    if output_map is None: return None
    try: 
        database = Database(force=force, **kwargs)
        if not force and database.check_history(main_function.__name__, **kwargs): return None
        df = store.get_dataframe(main_path)
        for i, row in tqdm(df.iterrows(), total=df.shape[0], desc="Transferring Records"):
            store.export_to_database(row, output_map)
        database.add_to_history(main_function.__name__, **kwargs)
    except Exception as e: 
        logger.warning("Database not available.", exc_info=True)


def apply_parser(input_table, input_columns, output_table, output_map, parser, sample=0, **kwargs):
    # type: (AnyStr, List[AnyStr], AnyStr, Dict[AnyStr, AnyStr], Parser, int, **Any) -> None
    database = Database(**dict(kwargs, force=False))
    input_dataframe = database.load_columns(input_table, input_columns, **kwargs)
    if sample != 0: input_dataframe = input_dataframe.sample(n=sample)
    total = input_dataframe.shape[0] 
    for i, row in tqdm(input_dataframe.iterrows(), total=total, desc="Parsing Records (%s)" % (parser.__name__)):
        input_values = row[input_columns].values
        if len(input_values) == 1: input_values = input_values[0]
        output_values = parser(input_values, **kwargs)
        if output_values:
            output_series = pd.DataFrame(output_values, index=[i])
            database.save_record(input_table, output_table, output_map, output_series, **kwargs)


##########################################################
# Image Processing


def dump_database(**kwargs):
    # type: (**Any) -> None
    from thickshake.storage.interface import export_database_to_store
    process_wrapper(
        main_function = export_database_to_store,
        main_path = "/dump",
        storage_map = {"dump": "/dump"},
        **kwargs
    )


def detect_faces(input_image_dir=None, **kwargs):
    # type: (DirPath, **Any) -> None
    from thickshake.augment.image.faces import extract_faces_from_images
    process_wrapper(
        main_function = extract_faces_from_images,
        main_path = "/faces/bounding_boxes",
        storage_map = {
            "bounding_boxes": "/faces/bounding_boxes",
            "landmarks": "/faces/landmarks",
            "embeddings": "/faces/embeddings",
        },
        output_map = {
            "image_subject.image_uuid": "image_uuid",
            "image_subject.face_box_x": "face_box_x",
            "image_subject.face_box_y": "face_box_y",
            "image_subject.face_box_w": "face_box_w",
            "image_subject.face_box_h": "face_box_h",
        },
        input_image_dir=input_image_dir, **kwargs
    )


def identify_faces(input_image_dir=None, **kwargs):
    # type: (DirPath, **Any) -> None
    from thickshake.augment.classifier.classifier import run_face_classifier
    process_wrapper(
        main_function = run_face_classifier,
        main_path = "/faces/identities",
        dependencies = [dump_database, detect_faces],
        storage_map = {"identities": "/faces/identities"},
        output_map = {
            "image_subject.subject_uuid": "subject_uuid",
            "image_subject.image_uuid": "image_uuid",
            "image_subject.face_box_x": "face_box_x",
            "image_subject.face_box_y": "face_box_y",
            "image_subject.face_box_w": "face_box_w",
            "image_subject.face_box_h": "face_box_h",
        },
        input_image_dir=input_image_dir, **kwargs
    )


##########################################################
# Metadata Parsing


def parse_locations(**kwargs):
    # type: (**Any) -> None
    from thickshake.augment.parser.geocoder import extract_location
    apply_parser(
        input_table = "image",
        input_columns = ["image_note"],
        output_table = "location",
        output_map = { 
            "index": "image_uuid",
            "building_name": "building_name",
            "street_number": "street_number",
            "street_name": "street_name",
            "street_type": "street_type",
            "suburb": "suburb",
            "state": "state",
            "post_code": "post_code",
            "latitude": "latitude",
            "longitude": "longitude",
            "confidence": "confidence",
            "location_type": "location_type"
        },
        parser = extract_location,
        **kwargs
    )


def parse_links(**kwargs):
    # type: (**Any) -> None
    from thickshake.augment.parser.links import extract_image_links
    apply_parser(
        input_table = "image",
        input_columns = ["image_url"],
        output_table = "image",
        output_map = { 
            "index": "uuid",
            "image_label": "image_label",
            "image_url_raw": "image_url_raw",
            "image_url_thumb": "image_url_thumb",
        },
        parser = extract_image_links,
        **kwargs
    )


def parse_sizes(**kwargs):
    # type: (**Any) -> None
    from thickshake.augment.parser.links import extract_image_dimensions
    apply_parser(
        input_table = "image",
        input_columns = ["image_url_raw"],
        output_table = "image",
        output_map = { 
            "index": "uuid",
            "image_height": "image_height",
            "image_width": "image_width"
        },
        parser = extract_image_dimensions,
        **kwargs
    )


def parse_dates(**kwargs):
    # type: (**Any) -> None
    from thickshake.augment.parser.dates import extract_date_from_title, combine_dates, split_dates
    apply_parser(
        input_table = "image",
        input_columns = ["image_note"],
        output_table = "image",
        output_map = { 
            "index": "uuid",
            "date": "image_date_created"
        },
        parser = extract_date_from_title,
        **kwargs
    )
    apply_parser(
        input_table = "record",
        input_columns = ["date_created", "date_created_approx"],
        output_table = "record",
        output_map = { 
            "index": "uuid",
            "date": "date_created_parsed"
        },
        parser = combine_dates,
        **kwargs
    )
    apply_parser(
        input_table = "subject",
        input_columns = ["subject_dates"],
        output_table = "subject",
        output_map = { 
            "index": "uuid",
            "start_date": "subject_start_date",
            "end_date": "subject_end_date"
        },
        parser = split_dates,
        **kwargs
    )

##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    main()


##########################################################
# Notes

"""
store:
    faces:
        bounding_boxes: <image_id, box_num, ...bb_anchors>
        landmarks: <image_id, box_num, ...landmarks>
        embeddings: <image_id, box_num, ...embeddings>
        identities: <image_id, box_num, ...bb_anchors, subject_uuid>
    ocr:
        bounding_boxes: <image_id, box_num, ...bb_anchors>
        ocr_text: <image_id, box_num, ocr_text>
    caption:
        bounding_boxes: <image_id, box_num, ...bb_anchors>
        caption: <image_id, box_num, caption>
    dump: <timestamp, image_id, ...features>
    classifier: <timestamp, ...weights>

/faces/bounding_boxes
/faces/landmarks
/faces/embeddings
/faces/identities
/faces/counts
"""