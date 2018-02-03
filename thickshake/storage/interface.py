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

##########################################################
# Local Imports

from thickshake.storage.store import Store
from thickshake.storage.database import Database

##########################################################
# Typing Configuration

from typing import List, Any, Union, Dict, Callable

##########################################################
# Constants

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################


def process_wrapper(
        main_path: str,
        main_function: Callable,
        output_map: Dict[str, str],
        dependency_map: OrderedDict[str, Callable] = None,
        **kwargs: Any
    ) -> None:
    store = Store(**kwargs)
    if not store.contains(main_path):
        for dependency_path, dependency_function in dependency_map.items():
            if not store.contains(dependency_path):
                dependency_function(**kwargs)
    main_function(**kwargs)
    try: database = Database(**kwargs)
    except: logger.warning("Database not available.")
    else:
        records = store.get_records(main_path)
        for record in tqdm(records, desc="Transferring Records"):
            store.export_to_database(record, output_map)


def detect_faces(input_image_dir: DirPath = None, **kwargs: Any) -> None:
    from thickshake.image.faces import extract_faces_from_images
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
    from thickshake.image.faces import extract_faces_from_images
    from thickshake.classifier.classifier import run_face_classifier
    process_wrapper(
        main_path = "faces/identities",
        main_function = partial(run_face_classifier(**kwargs)),
        dependency_map = OrderedDict(
            "dump": partial(export_database_to_store(**kwargs)),
            "faces/bounding_boxes": partial(extract_faces_from_images(input_image_dir, **kwargs)),
        )
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