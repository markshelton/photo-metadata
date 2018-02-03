# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import logging
from collections import OrderedDict
from functools import partial

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

from typing import List, Any, Union, Dict, Callable
Parser = Any
FilePath = str
DirPath = str

##########################################################
# Constants

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Wrappers


def process_wrapper(
        main_path: str,
        main_function: Callable,
        output_map: Dict[str, str],
        dependency_map: List[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
    store = Store(**kwargs)
    if not store.contains(main_path):
        for dependency in dependency_map:
            dependency_path = dependency["path"]
            dependency_function = dependency["func"]
            if not store.contains(dependency_path):
                dependency_function(storage_path=dependency_path, **kwargs)
    main_function(storage_path=main_path, **kwargs)
    try: database = Database(**kwargs)
    except: logger.warning("Database not available.")
    else:
        records = store.get_records(main_path)
        for record in tqdm(records, desc="Transferring Records"):
            store.export_to_database(record, output_map)


def apply_parser(
        input_table: str, #Table
        input_columns: List[str], # Columns
        output_table: str,
        output_map: Dict[str, str], # Map (df column -> db column)
        parser: Parser,
        sample: int = 0,
        **kwargs: Any
    ) -> None:
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


def detect_faces(input_image_dir: DirPath = None, **kwargs: Any) -> None:
    from thickshake.augment.image.faces import extract_faces_from_images
    process_wrapper(
        main_path = "faces/bounding_boxes",
        main_function = partial(extract_faces_from_images(input_image_dir, **kwargs)),
        output_map = {
            "image_subject.image_uuid": "image_uuid",
            "image_subject.face_bb_left": "face_bb_left",
            "image_subject.face_bb_right": "face_bb_right",
            "image_subject.face_bb_top": "face_bb_top",
            "image_subject.face_bb_bottom": "face_bb_bottom"
        }
    )


def identify_faces(input_image_dir: DirPath = None, **kwargs: Any) -> None:
    from thickshake.storage.writer import export_database_to_store
    from thickshake.augment.image.faces import extract_faces_from_images
    from thickshake.augment.classifier.classifier import run_face_classifier
    process_wrapper(
        main_path = "faces/identities",
        main_function = partial(run_face_classifier(**kwargs)),
        dependency_map = [
            dict(path=dump, func=partial(export_database_to_store(**kwargs))),
            dict(path=faces/bounding_boxes, func=partial(extract_faces_from_images(input_image_dir, **kwargs))),
        ],
        output_map = {
            "image_subject.subject_uuid": "subject_uuid",
            "image_subject.image_uuid": "image_uuid",
            "image_subject.face_bb_left": "face_bb_left",
            "image_subject.face_bb_right": "face_bb_right",
            "image_subject.face_bb_top": "face_bb_top",
            "image_subject.face_bb_bottom": "face_bb_bottom"
        }
    )


##########################################################
# Metadata Parsing


def parse_locations(**kwargs: Any) -> None:
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


def parse_links(**kwargs: Any) -> None:
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


def parse_sizes(**kwargs: Any) -> None:
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


def parse_dates(**kwargs: Any) -> None:
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