# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Python Compatibility

from __future__ import print_function, division, absolute_import
from builtins import map, str, range
from future import standard_library

standard_library.install_aliases()

##########################################################
# Standard Library Imports

import logging
import os

##########################################################
# Third Party Imports

import cv2
import dlib
from envparse import env
import numpy as np
import pandas as pd
from tqdm import tqdm

##########################################################
# Local Imports

from thickshake.storage import Store
from thickshake.augment.image.utils import get_image, handle_image, rect_to_bb
from thickshake.utils import get_files_in_directory, check_output_directory

##########################################################
#Typing Configuration

from typing import Text, List, Any, Optional, Tuple, Iterable, Dict, AnyStr

FilePath = Text 
DirPath = Text 
ImageType = Any
Rectangle = Any
Recognizer = Any
Predictor = Any
DataFrame = Any
NPArray = Any

##########################################################
# Constants

CURRENT_FILE_DIR, _ = os.path.split(__file__)
DATA_DIR_PATH = "%s/../../_data/image/faces" % CURRENT_FILE_DIR
IMG_FACE_PREDICTOR_FILE = env.str("IMG_FACE_PREDICTOR_FILE", default="%s/shape_predictor_68_face_landmarks.dat" % DATA_DIR_PATH)
IMG_FACE_RECOGNIZER_FILE = env.str("IMG_FACE_RECOGNIZER_FILE", default="%s/dlib_face_recognition_resnet_model_v1.dat" % DATA_DIR_PATH)
IMG_FACE_TEMPLATE_FILE = env.str("IMG_FACE_TEMPLATE_FILE", default="%s/openface_68_face_template.npy" % DATA_DIR_PATH)
KEY_INDICES = env.list("KEY_INDICES", default=[39, 42, 57], subcast=int) # INNER_EYES_AND_BOTTOM_LIP
FACE_SIZE = env.int("FACE_SIZE", default=200)

##########################################################
# Initialization

logger = logging.getLogger(__name__)

##########################################################
# Functions


def prepare_template(face_template_file):
    # type: (FilePath) -> List[int]
    face_template = np.load(face_template_file)
    tpl_min, tpl_max = np.min(face_template, axis=0), np.max(face_template, axis=0)
    minmax_template = (face_template - tpl_min) / (tpl_max - tpl_min)
    return minmax_template


def find_faces_in_image(image):
    # type: (ImageType) -> List[Rectangle]
    detector = dlib.get_frontal_face_detector()
    faces = detector(image, 1)
    return faces


def split_face_id(face_id):
    # type: (AnyStr) -> Tuple[AnyStr, AnyStr]
    face_id_parts = face_id.split("_")
    image_id = "_".join(face_id_parts[0:2])
    box_number = face_id_parts[2]
    return image_id, box_number


def make_dataframe(array, value_name, index_names, face_id):
    # type: (NPArray, AnyStr, List[AnyStr], AnyStr) -> DataFrame
    index = pd.MultiIndex.from_product([range(s)for s in array.shape], names=index_names)
    df = pd.Series(array.flatten(), index=index, name=value_name)
    df = df.reset_index()
    image_id, box_number = split_face_id(face_id)
    df["image_id"] = image_id
    df["box_number"] = box_number
    return df


def save_face_dataset(face_id, array, storage_path=None, index_names=None, **kwargs):
    # type: (AnyStr, NPArray, AnyStr, Optional[List[AnyStr]], **Any) -> None
    if storage_path is None: return None
    from thickshake.storage import Store
    store = Store(**kwargs)
    df = make_dataframe(array, value_name="value", index_names=index_names, face_id=face_id)
    store.save(storage_path, df, index=["image_id", "box_number"], **kwargs)


def extract_face_landmarks(image, face_box, face_id, predictor=None, storage_map=None, **kwargs):
    # type: (ImageType, Rectangle, AnyStr, Predictor, Dict[AnyStr, AnyStr], **Any) -> List[Any]
    points = predictor(image, face_box)
    landmarks = list(map(lambda p: (p.x, p.y), points.parts()))
    landmarks_np = np.float32(landmarks)
    save_face_dataset(face_id, landmarks_np, storage_path=storage_map["landmarks"], index_names=['point', 'component'], **kwargs)
    return landmarks_np


def extract_face_embeddings(image, face_box, face_id, predictor=None, recognizer=None, storage_map=None, **kwargs):
    # type: (ImageType, Rectangle, AnyStr, Predictor, Recognizer, Dict[AnyStr, AnyStr], **Any) -> List[float]
    points = predictor(image, face_box)
    embeddings = recognizer.compute_face_descriptor(image, points)
    embeddings_np = np.float32(embeddings)[np.newaxis, :]
    save_face_dataset(face_id, embeddings_np, storage_path=storage_map["embeddings"], index_names=['point', 'component'], **kwargs)
    return embeddings_np


def normalize_face(image, landmarks, face_id, image_file, template=None, key_indices=KEY_INDICES, face_size=FACE_SIZE, **kwargs):
    # type: (ImageType, List[Any], AnyStr, FilePath, List[float], List[int], int, **Any) -> ImageType
    key_indices_np = np.array(key_indices)
    H = cv2.getAffineTransform(landmarks[key_indices_np], face_size * template[key_indices_np])
    image_face = cv2.warpAffine(image, H, (face_size, face_size))
    handle_image(image_face, input_file=image_file, output_folder="faces", **kwargs)
    return image_face


def annotate_image(image, face_box, face_id, landmarks, **kwargs):
    # type: (ImageType, Rectangle, AnyStr, List[Any], **Any) -> ImageType
    (x, y, w, h) = rect_to_bb(face_box)
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(image, "Face #{}".format(face_id), (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    for (x, y) in landmarks:
        cv2.circle(image, (x, y), 1, (0, 0, 255), -1)
    return image


def get_template(template=None, template_path=IMG_FACE_TEMPLATE_FILE, **kwargs):
    # type: (Optional[List[int]], FilePath, **Any) -> List[int]
    return prepare_template(template_path) if template is None else template


def get_predictor(predictor=None, predictor_path=IMG_FACE_PREDICTOR_FILE, **kwargs):
    # type: (Optional[Predictor], FilePath, **Any) -> Predictor
    return dlib.shape_predictor(predictor_path) if predictor is None else predictor


def get_recognizer(recognizer=None, recognizer_path=IMG_FACE_RECOGNIZER_FILE, **kwargs):
    # type: (Optional[Recognizer], FilePath, **Any) -> Recognizer
    return dlib.face_recognition_model_v1(recognizer_path) if recognizer is None else recognizer


def get_dependencies(**kwargs):
    # type: (**Any) -> Tuple[List[int], Predictor, Recognizer]
    template = get_template(**kwargs)
    predictor = get_predictor(**kwargs)
    recognizer = get_recognizer(**kwargs)
    return template, predictor, recognizer


def generate_face_id(image_file, face_number, **kwargs):
    # type: (FilePath, int, **Any) -> AnyStr
    base = os.path.basename(image_file)
    image_id_parts = base.split("_")
    face_id_parts = [image_id_parts[1], image_id_parts[2], face_number]
    face_id = "_".join(str(part) for part in face_id_parts)
    return face_id


def save_face_box(face_id, face_box, storage_map=None, **kwargs):
    # type: (AnyStr, int, Optional[Dict[AnyStr, AnyStr]], **Any) -> None
    face_box = np.array(rect_to_bb(face_box))
    save_face_dataset(face_id, face_box, storage_path=storage_map["bounding_boxes"], index_names=['component'], **kwargs)


def extract_faces_from_image(image_file, **kwargs):
    # type: (FilePath, **Any) -> ImageType
    image = get_image(image_file)
    image_annotated = image.copy()
    faces = find_faces_in_image(image)
    for face_number, face_box in enumerate(faces):
        face_id = generate_face_id(image_file, face_number, **kwargs)
        landmarks = extract_face_landmarks(image, face_box, face_id, **kwargs)
        image_face = normalize_face(image, landmarks, face_id, image_file, **kwargs)
        embeddings = extract_face_embeddings(image, face_box, face_id, **kwargs)
        save_face_box(face_id, face_box, **kwargs)
        image_annotated = annotate_image(image_annotated, face_box, face_id, landmarks, **kwargs) 
    handle_image(image_annotated, input_file=image_file, sub_folder="faces_annotated", **kwargs)
    return image_annotated


#TODO: Make asynchronous, see https://hackernoon.com/building-a-facial-recognition-pipeline-with-deep-learning-in-tensorflow-66e7645015b8
def extract_faces_from_images(input_image_dir=None, output_image_dir=None, **kwargs):
    # type: (DirPath, DirPath, **Any) -> None
    image_files = get_files_in_directory(input_image_dir, **kwargs)
    check_output_directory(output_image_dir, **kwargs)
    template, predictor, recognizer = get_dependencies(**kwargs)
    for image_file in tqdm(image_files, desc="Extracting Faces"):
        image_annotated = extract_faces_from_image(
            image_file,
            input_image_dir=input_image_dir,
            output_image_dir=output_image_dir,
            template=template,
            predictor=predictor,
            recognizer=recognizer,
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

https://docs.opencv.org/3.3.0/d7/d8b/tutorial_py_face_detection.html

https://hackernoon.com/building-a-facial-recognition-pipeline-with-deep-learning-in-tensorflow-66e7645015b8
https://medium.com/@ageitgey/machine-learning-is-fun-part-4-modern-face-recognition-with-deep-learning-c3cffc121d78
https://medium.com/@ageitgey/try-deep-learning-in-python-now-with-a-fully-pre-configured-vm-1d97d4c3e9b
https://www.pyimagesearch.com/2017/04/03/facial-landmarks-dlib-opencv-python/
http://www.hackevolve.com/face-recognition-deep-learning/

- Pre-processing Pipeline
For each image:
    1. Read metadata for image (if exists)
        - Find locally (directory flag)
        - Find remotely (SLWA catalogue API)
    2. Convert metadata to digestible format - DONE
    3. Find face in image
        For each face:
            2. Find facial landmarks
            3. Normalize face (scale, shift)
            4. Generate face encodings (apply pre-trained CNN model)
            5. Save face encoding with image metadata

"""
##########################################################
