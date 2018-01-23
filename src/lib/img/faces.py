##########################################################
# Standard Library Imports

import logging
import os
import time

##########################################################
# Third Party Imports

import cv2
import dlib
import h5py
import numpy as np

from envparse import env
from matplotlib import pyplot as plt

##########################################################
# Local Imports

from thickshake.utils import (
    logged, setup_logging, setup_warnings, log_progress,
    clear_directory, maybe_increment_path, get_files_in_directory,
    maybe_make_directory,
)
from thickshake.types import *

##########################################################
# Environmental Variables

INPUT_IMAGE_DIR = env.str("INPUT_IMAGE_DIR", default="/home/app/data/input/images/JPEG_Convert_Resolution_1024") # type: DirPath
OUTPUT_IMAGE_FACES_DIR = env.str("OUTPUT_IMAGE_FACES_DIR", default="/home/app/data/output/images/faces") # type: DirPath
OUTPUT_IMAGE_ANNOTATIONS_DIR = env.str("OUTPUT_IMAGE_ANNOTATIONS_DIR", default="/home/app/data/output/images/face_annotations") # type: DirPath
OUTPUT_IMAGE_DATA_FILE = env.str("OUTPUT_IMAGE_DATA_FILE", default="/home/app/data/output/face_recognition/faces.hdf5") # type: FilePath

FLAG_IMG_SAMPLE = env.int("FLAG_IMG_SAMPLE", default=0)
FLAG_IMG_FACE_SIZE = env.int("FLAG_IMG_FACE_SIZE", default=200)
FLAG_IMG_CLEAR_FACES = env.bool("FLAG_IMG_CLEAR_FACES", default=True)
FLAG_IMG_OVERWRITE_FACES = env.bool("FLAG_IMG_OVERWRITE_FACES", default=True)
FLAG_IMG_SAVE_FACES = env.bool("FLAG_IMG_SAVE_FACES", default=True)
FLAG_IMG_SHOW_FACES = env.bool("FLAG_IMG_SHOW_FACES", default=False)
FLAG_IMG_SAVE_IMAGES = env.bool("FLAG_IMG_SAVE_IMAGES", default=True)
FLAG_IMG_SHOW_IMAGES = env.bool("FLAG_IMG_SHOW_IMAGES", default=True)
FLAG_IMG_LOGGING = env.bool("FLAG_IMG_LOGGING", default=True)
FLAG_IMG_LANDMARK_INDICES = env.list("", default=[39, 42, 57], subcast=int) #INNER_EYES_AND_BOTTOM_LIP
#FLAG_IMG_LANDMARK_INDICES = env.list("", default=[36, 45, 33], subcast=int) #OUTER_EYES_AND_NOSE

CURRENT_FILE_DIR, _ = os.path.split(__file__)
IMG_FACE_PREDICTOR_FILE = env.str("IMG_FACE_PREDICTOR_FILE", default="%s/deps/shape_predictor_68_face_landmarks.dat" % CURRENT_FILE_DIR)
IMG_FACE_RECOGNIZER_FILE = env.str("IMG_FACE_RECOGNIZER_FILE", default="%s/deps/dlib_face_recognition_resnet_model_v1.dat" % CURRENT_FILE_DIR)
IMG_FACE_TEMPLATE_FILE = env.str("IMG_FACE_TEMPLATE_FILE", default="%s/deps/openface_68_face_template.npy" % CURRENT_FILE_DIR)

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions

def rect_to_bb(rect):
	x = rect.left()
	y = rect.top()
	w = rect.right() - x
	h = rect.bottom() - y
	return (x, y, w, h)


def show_image(image_rgb: ImageType) -> None:
    plt.imshow(image_rgb)
    plt.show()


def prepare_template(face_template_file: FilePath) -> None:
    face_template = np.load(face_template_file)
    tpl_min, tpl_max = np.min(face_template, axis=0), np.max(face_template, axis=0)
    minmax_template = (face_template - tpl_min) / (tpl_max - tpl_min)
    return minmax_template


def enhance_image(image):
    image_YCrCb = cv2.cvtColor(image, cv2.COLOR_BGR2YCR_CB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    channels = [clahe.apply(channel) for channel in cv2.split(image_YCrCb)]
    image = cv2.merge(channels)
    image = cv2.cvtColor(image_YCrCb, cv2.COLOR_YCR_CB2BGR)
    return image


def find_faces_in_image(image: ImageType) -> List[Rectangle]:
    detector = dlib.get_frontal_face_detector()
    faces = detector(image, 1)
    return faces


def extract_face_landmarks(image: ImageType, face: Rectangle, predictor: Any) -> np.float32:
    points = predictor(image, face)
    landmarks = list(map(lambda p: (p.x, p.y), points.parts()))
    landmarks_np = np.float32(landmarks)
    return landmarks_np


def extract_face_embeddings(image: ImageType, face: Rectangle, predictor: Any, recognizer: Any) -> np.float32:
    points = predictor(image, face)
    embeddings = recognizer.compute_face_descriptor(image, points)
    embeddings_np = np.float32(embeddings)[np.newaxis, :]
    return embeddings_np


def normalize_face(
        image: ImageType,
        landmarks: np.float32,
        face_template: np.array,
        key_indices: List[int],
        face_size: int = 200,
        **kwargs
    ) -> ImageType:
    key_indices_np = np.array(key_indices)
    H = cv2.getAffineTransform(landmarks[key_indices_np], face_size * face_template[key_indices_np])
    face_norm = cv2.warpAffine(image, H, (face_size, face_size))
    return face_norm


def save_image(
        image_rgb: ImageType,
        image_file: FilePath,
        input_images_dir: Optional[DirPath] = None,
        output_images_dir: Optional[DirPath] = None,
        **kwargs
    ) -> FilePath:
    if output_images_dir is None or input_images_dir is None: return None
    output_file = image_file.replace(input_images_dir, output_images_dir)
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    image_file = maybe_increment_path(output_file, **kwargs)
    maybe_make_directory(image_file)
    cv2.imwrite(image_file, image_bgr)
    logger.info(image_file)
    return image_file


def save_object(
        save_object: Any,
        object_name: str,
        image_file: FilePath,
        output_file: Optional[FilePath] = None,
        **kwargs
    ) -> None:
    if output_file is None: return None
    image_id = os.path.basename(image_file).split(".")[0]
    with h5py.File(output_file, "a") as f:
        grp = f.require_group(object_name)
        grp.create_dataset(image_id, data=save_object)


def annotate_image(image_rgb, face, i, landmarks):
    (x, y, w, h) = rect_to_bb(face)
    cv2.rectangle(image_rgb, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(image_rgb, "Face #{}".format(i + 1), (x - 10, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    for (x, y) in landmarks:
        cv2.circle(image_rgb, (x, y), 1, (0, 0, 255), -1)
    return image_rgb


def extract_faces_from_image(
        image_file: FilePath,
        predictor: Optional[Any] = None,
        recognizer: Optional[Any] = None,
        template: Optional[Any] = None,
        predictor_path: Optional[FilePath] = None,
        recognizer_path: Optional[FilePath] = None,
        template_path: Optional[FilePath] = None,
        output_face_info_file: Optional[FilePath] = None,
        show_faces_flag: bool = False,
        save_faces_flag: bool = False,
        **kwargs: Any
    ) -> ImageType:
    image_bgr = cv2.imread(image_file)
    image_bgr = enhance_image(image_bgr)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    faces = find_faces_in_image(image_rgb)
    if template is None: template = prepare_template(template_path)
    if predictor is None: predictor = dlib.shape_predictor(predictor_path)
    if recognizer is None: recognizer = dlib.face_recognition_model_v1(recognizer_path)
    image_annot = image_rgb.copy()
    for i, face in enumerate(faces):
        landmarks = extract_face_landmarks(image_rgb, face, predictor)
        embeddings = extract_face_embeddings(image_rgb, face, predictor, recognizer)
        face_norm = normalize_face(image_rgb, landmarks, template, **kwargs)
        if show_faces_flag:
            show_image(face_norm)
        if save_faces_flag: 
            output_file = save_image(face_norm, image_file, **kwargs)
            save_object(landmarks, "landmarks", output_file, output_face_info_file, **kwargs)
            save_object(embeddings, "embeddings", output_file, output_face_info_file, **kwargs)
        image_annot = annotate_image(image_annot, face, i, landmarks)        
    return image_annot


#TODO: Make asynchronous, see https://hackernoon.com/building-a-facial-recognition-pipeline-with-deep-learning-in-tensorflow-66e7645015b8
def extract_faces_from_images(
        input_images_dir: DirPath,
        predictor_path: FilePath = IMG_FACE_PREDICTOR_FILE,
        recognizer_path: FilePath = IMG_FACE_RECOGNIZER_FILE,
        template_path: FilePath = IMG_FACE_TEMPLATE_FILE,
        output_faces_dir: Optional[DirPath]=None,
        output_images_dir: Optional[DirPath]=None,
        flag_clear_faces: bool=False,
        show_image_flag: bool=True,
        save_image_flag: bool=True,
        logging_flag: bool=False,
        **kwargs: Any
    ) -> List[ImageType]:
    image_files = get_files_in_directory(input_images_dir, **kwargs)
    if flag_clear_faces: clear_directory(output_images_dir)
    predictor = dlib.shape_predictor(predictor_path)
    recognizer = dlib.face_recognition_model_v1(recognizer_path)
    template = prepare_template(template_path)
    total = len(image_files)
    start_time = time.time()
    for i, image_file in enumerate(image_files):
        image_annot = extract_faces_from_image(
            image_file=image_file,
            input_images_dir=input_images_dir,
            output_images_dir=output_faces_dir,
            predictor=predictor,
            recognizer=recognizer,
            template=template,
            **kwargs
        )
        if show_image_flag:
            show_image(image_annot)
        if save_image_flag:
            save_image(image_annot, image_file, input_images_dir, output_images_dir, **kwargs)
        if logging_flag:
            log_progress(i+1, total, start_time)


##########################################################
# Main

def main():
    extract_faces_from_images(
        input_images_dir=INPUT_IMAGE_DIR,
        output_faces_dir=OUTPUT_IMAGE_FACES_DIR,
        output_images_dir=OUTPUT_IMAGE_ANNOTATIONS_DIR,
        output_face_info_file=OUTPUT_IMAGE_DATA_FILE,
        sample_size=20,
        show_faces_flag=False,
        save_faces_flag=False,
        show_image_flag=False,
        save_image_flag=True,
        flag_clear_faces=False,
        logging_flag=True,
        overwrite=False,
        key_indices=FLAG_IMG_LANDMARK_INDICES,
        face_size=FLAG_IMG_FACE_SIZE,
        predictor_path=IMG_FACE_PREDICTOR_FILE,
        recognizer_path=IMG_FACE_RECOGNIZER_FILE,
        template_path=IMG_FACE_TEMPLATE_FILE,
    )


if __name__ == "__main__":
    setup_logging()
    setup_warnings()
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