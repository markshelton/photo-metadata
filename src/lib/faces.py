##########################################################
# Standard Library Imports

import glob
import os
import errno
import shutil
import functools
import operator
import random

##########################################################
# Third Party Imports

from matplotlib import pyplot as plt
import numpy as np
import dlib
import cv2

##########################################################
# Local Imports

from _types import (
    Dict, List, Pattern, Optional,
    FilePath, DirPath, Match, Coordinates, Address,
    Image,
)

##########################################################
# Environmental Variables

INPUT_IMAGE_DIR = "/src/input/images/JPEG_Convert_Resolution_1024" # type: DirPath
OUTPUT_FACES_IMAGE_DIR = "/src/output/face_recognition/images/faces" # type: DirPath
FACIAL_LANDMARK_DETECTOR_MODEL = None # type: FilePath

STANDARDIZED_IMAGE_SIZE = {}
STANDARDIZED_IMAGE_SIZE["width"] = 500
STANDARDIZED_IMAGE_SIZE["height"] = 500

INPUT_SAMPLE_SIZE = 100

RESET_FILES_FLAG = True
SHOW_IMAGES_FLAG = False
LIST_FILES_FLAG = False

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
#Helpers


def rect_to_bb(rect: Rectangle) -> BoundingBox:
	x = rect.left()
	y = rect.top()
	w = rect.right() - x
	h = rect.bottom() - y
	return Face(x=x, y=y, w=w, h=h)


def shape_to_np(shape: Shape, dtype="int") -> Array:
	coords = np.zeros((68, 2), dtype=dtype)
	for i in range(0, 68):
		coords[i] = (shape.part(i).x, shape.part(i).y)
	return coords


def resize_image(
        image_original: Image,
        width_target: Optional[int] = None,
        height_target: Optional[int] = None,
        interpolation_type: Enum = cv2.INTER_AREA
    ) -> Image:

    height_original, width_original = image.shape[:2]
    if width_target is None and height_target is None: return image_original
    if width_target is None:
        ratio = height_target / float(height_original)
        dimensions = (int(width_original * ratio), height_target)
    else:
        ratio = width_target / float(width_original)
        dimensions = (width_target, int(height_original * ratio))
    image_resized = cv2.resize(image_original, dimensions, interpolation=inter)
    return resized


def make_directory(directory: DirPath, clear: str = RESET_FILES_FLAG):
    if clear: shutil.rmtree(directory)
    try: os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST: raise


def count_files_that_match_pattern(directory: DirPath, pattern: str) -> int:
    return len(glob.glob1(directory, pattern))


def maybe_increment_path(file_path: FilePath, sep: str = "_") -> Optional[FilePath]:
    file_path_base, file_ext = os.path.splitext(file_path)
    directory_path = os.path.dirname(file_path)
    max_files = count_files_that_match_pattern(directory_path, "file_path_base*")
    for i in range(max_files):
        full_file_path = "%s%s%s%s" % (file_path_base, sep, i, file_ext)
        if not os.path.exists(full_file_path):
            return full_file_path
    return None


def show_image(image: Image) -> None:
    plt.imshow(img_rgb)
    plt.show()


def save_image(image_file: FilePath, image: Image) -> None:
    image_file = maybe_increment_path(image_file)
    cv2.imwrite(image_file, image)


##########################################################
# Functions


def find_faces_in_image(image_gray: Image) -> List[Rectangle]:
    detector = dlib.get_frontal_face_detector()
    faces_rect = detector(gray, 1)
    return faces_rect


def detect_facial_landmarks(face_rect: Rectangle) -> Array[int]:
    predictor = dlib.shape_predictor(FACIAL_LANDMARK_DETECTOR_MODEL)
    landmarks_shape = predictor(gray, face_rect)
	landmarks_array = face_utils.shape_to_np(landmarks_shape)
    return landmarks_array


def process_image(image_file: FilePath) -> List[Face]:
    image_bgr = cv2.imread(image_file)
    image_resized = resize_image(image, width=500)
    image_gray = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)
    faces_rect = find_faces_in_image(image_gray)
    landmarks_arrays = [detect_facial_landmarks(face_rect) for face_rect in faces_rect]


##########################################################
# Main

if __name__ == "__main__":
    pass

##########################################################
# Notes
"""

https://docs.opencv.org/3.3.0/d7/d8b/tutorial_py_face_detection.html

https://hackernoon.com/building-a-facial-recognition-pipeline-with-deep-learning-in-tensorflow-66e7645015b8
https://medium.com/@ageitgey/machine-learning-is-fun-part-4-modern-face-recognition-with-deep-learning-c3cffc121d78
https://medium.com/@ageitgey/try-deep-learning-in-python-now-with-a-fully-pre-configured-vm-1d97d4c3e9b
https://www.pyimagesearch.com/2017/04/03/facial-landmarks-dlib-opencv-python/

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