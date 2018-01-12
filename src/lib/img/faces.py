##########################################################
# Standard Library Imports

import glob
import os
import errno
import shutil
import functools
import operator
import random
import logging

##########################################################
# Third Party Imports

from matplotlib import pyplot as plt
import numpy as np
import dlib
import cv2
import h5py

##########################################################
# Local Imports

from thickshake.utils import (
    logged, setup_logging, setup_warnings,
    clear_directory, maybe_increment_path, get_files_in_directory
)
from thickshake._types import (
    Dict, List, Pattern, Optional, Any,
    FilePath, DirPath, Face,
    Image, Rectangle, BoundingBox, Shape,
)

##########################################################
# Environmental Variables

INPUT_IMAGE_DIR = "/home/app/data/input/images/JPEG_Convert_Resolution_1024" # type: DirPath
OUTPUT_FACES_IMAGE_DIR = "/home/app/data/output/face_recognition/images/faces" # type: DirPath
OUTPUT_FACE_INFO_FILE = "/home/app/data/output/face_recognition/faces.hdf5" # type: FilePath

FACE_SIZE = 200

INPUT_SAMPLE_SIZE = 20

RESET_FILES_FLAG = True
CLEAR_FACES_FLAG=True
OVERWRITE_FACES_FLAG = True
SAVE_FLAG = True
SHOW_FACES_FLAG = False
LIST_FILES_FLAG = False

##########################################################
# Face Configuration

CURRENT_DIR, _ = os.path.split(__file__)
FACE_PREDICTOR_PATH = "%s/shape_predictor_68_face_landmarks.dat" % CURRENT_DIR
FACE_RECOGNIZER_PATH = "%s/dlib_face_recognition_resnet_model_v1.dat" % CURRENT_DIR

FACIAL_LANDMARKS_IDXS = {
	"mouth": (48, 68),
	"right_eyebrow": (17, 22),
	"left_eyebrow": (22, 27),
	"right_eye": (36, 42),
	"left_eye": (42, 48),
	"nose": (27, 36),
	"jaw": (0, 17)
}

INNER_EYES_AND_BOTTOM_LIP = [39, 42, 57]
OUTER_EYES_AND_NOSE = [36, 45, 33]

FACE_TEMPLATE = np.float32([
    (0.0792396913815, 0.339223741112), (0.0829219487236, 0.456955367943),
    (0.0967927109165, 0.575648016728), (0.122141515615, 0.691921601066),
    (0.168687863544, 0.800341263616), (0.239789390707, 0.895732504778),
    (0.325662452515, 0.977068762493), (0.422318282013, 1.04329000149),
    (0.531777802068, 1.06080371126), (0.641296298053, 1.03981924107),
    (0.738105872266, 0.972268833998), (0.824444363295, 0.889624082279),
    (0.894792677532, 0.792494155836), (0.939395486253, 0.681546643421),
    (0.96111933829, 0.562238253072), (0.970579841181, 0.441758925744),
    (0.971193274221, 0.322118743967), (0.163846223133, 0.249151738053),
    (0.21780354657, 0.204255863861), (0.291299351124, 0.192367318323),
    (0.367460241458, 0.203582210627), (0.4392945113, 0.233135599851),
    (0.586445962425, 0.228141644834), (0.660152671635, 0.195923841854),
    (0.737466449096, 0.182360984545), (0.813236546239, 0.192828009114),
    (0.8707571886, 0.235293377042), (0.51534533827, 0.31863546193),
    (0.516221448289, 0.396200446263), (0.517118861835, 0.473797687758),
    (0.51816430343, 0.553157797772), (0.433701156035, 0.604054457668),
    (0.475501237769, 0.62076344024), (0.520712933176, 0.634268222208),
    (0.565874114041, 0.618796581487), (0.607054002672, 0.60157671656),
    (0.252418718401, 0.331052263829), (0.298663015648, 0.302646354002),
    (0.355749724218, 0.303020650651), (0.403718978315, 0.33867711083),
    (0.352507175597, 0.349987615384), (0.296791759886, 0.350478978225),
    (0.631326076346, 0.334136672344), (0.679073381078, 0.29645404267),
    (0.73597236153, 0.294721285802), (0.782865376271, 0.321305281656),
    (0.740312274764, 0.341849376713), (0.68499850091, 0.343734332172),
    (0.353167761422, 0.746189164237), (0.414587777921, 0.719053835073),
    (0.477677654595, 0.706835892494), (0.522732900812, 0.717092275768),
    (0.569832064287, 0.705414478982), (0.635195811927, 0.71565572516),
    (0.69951672331, 0.739419187253), (0.639447159575, 0.805236879972),
    (0.576410514055, 0.835436670169), (0.525398405766, 0.841706377792),
    (0.47641545769, 0.837505914975), (0.41379548902, 0.810045601727),
    (0.380084785646, 0.749979603086), (0.477955996282, 0.74513234612),
    (0.523389793327, 0.748924302636), (0.571057789237, 0.74332894691),
    (0.672409137852, 0.744177032192), (0.572539621444, 0.776609286626),
    (0.5240106503, 0.783370783245), (0.477561227414, 0.778476346951)])

TPL_MIN, TPL_MAX = np.min(FACE_TEMPLATE, axis=0), np.max(FACE_TEMPLATE, axis=0)
MINMAX_TEMPLATE = (FACE_TEMPLATE - TPL_MIN) / (TPL_MAX - TPL_MIN)

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
#Helpers


def show_image(image_rgb: Image) -> None:
    plt.imshow(image_rgb)
    plt.show()


##########################################################
# Functions

def adjust_gamma(image, gamma=1.0):
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)


def enhance_image(image):
    image_YCrCb = cv2.cvtColor(image, cv2.COLOR_BGR2YCR_CB)
    Y, Cr, Cb = cv2.split(image_YCrCb)
    Y = cv2.equalizeHist(Y)
    image_YCrCb = cv2.merge([Y, Cr, Cb])
    image = cv2.cvtColor(image_YCrCb, cv2.COLOR_YCR_CB2BGR)
    image = adjust_gamma(image)
    return image


def find_faces_in_image(image: Image) -> List[Rectangle]:
    detector = dlib.get_frontal_face_detector()
    faces = detector(image, 1)
    return faces


def extract_face_landmarks(image: Image, face: Rectangle, predictor: Any) -> np.float32:
    points = predictor(image, face)
    landmarks = list(map(lambda p: (p.x, p.y), points.parts()))
    landmarks_np = np.float32(landmarks)
    return landmarks_np


def extract_face_embeddings(image: Image, face: Rectangle, predictor: Any, recognizer: Any) -> np.float32:
    points = predictor(image, face)
    embeddings = recognizer.compute_face_descriptor(image, points)
    embeddings_np = np.float32(embeddings)[np.newaxis, :]
    return embeddings_np


def normalize_face(
        image: Image,
        landmarks: np.float32,
        key_indices: List[int] = INNER_EYES_AND_BOTTOM_LIP,
        face_template: np.array = MINMAX_TEMPLATE,
        face_size: int = 200,
        **kwargs
    ) -> Image:
    key_indices_np = np.array(key_indices)
    H = cv2.getAffineTransform(landmarks[key_indices_np], face_size * face_template[key_indices_np])
    face_norm = cv2.warpAffine(image, H, (face_size, face_size))
    return face_norm


def save_image(
        image_rgb: Image,
        image_file: FilePath,
        input_images_dir: Optional[DirPath] = None,
        output_images_dir: Optional[DirPath] = None,
        **kwargs
    ) -> FilePath:
    if output_images_dir is None or input_images_dir is None: return None
    output_file = image_file.replace(input_images_dir, output_images_dir)
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    image_file = maybe_increment_path(output_file, **kwargs)
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
    f = h5py.File(output_file, "a")
    grp = f.require_group(object_name)
    grp.create_dataset(image_id, data=save_object)
    f.close()


def extract_faces_from_image(
        image_file: FilePath,
        predictor: Optional[Any] = None,
        recognizer: Optional[Any] = None,
        predictor_path: Optional[FilePath] = None,
        recognizer_path: Optional[FilePath] = None,
        output_face_info_file: Optional[FilePath] = None,
        show_flag: bool = False,
        save_flag: bool = False,
        **kwargs: Any
    ) -> List[Image]:
    image_bgr = cv2.imread(image_file)
    image_bgr = enhance_image(image_bgr)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    faces = find_faces_in_image(image_rgb)
    if predictor is None: predictor = dlib.shape_predictor(predictor_path)
    if recognizer is None: recognizer = dlib.face_recognition_model_v1(recognizer_path)
    faces_norm = [] # type: List[Image]
    for face in faces:
        landmarks = extract_face_landmarks(image_rgb, face, predictor)
        embeddings = extract_face_embeddings(image_rgb, face, predictor, recognizer)
        face_norm = normalize_face(image_rgb, landmarks, **kwargs)
        if show_flag: show_image(image_rgb)
        if save_flag: 
            output_file = save_image(face_norm, image_file, **kwargs)
            save_object(landmarks, "landmarks", output_file, output_face_info_file, **kwargs)
            save_object(embeddings, "embeddings", output_file, output_face_info_file, **kwargs)
        faces_norm.append(face_norm)
    return faces_norm


#TODO: Make asynchronous, see https://hackernoon.com/building-a-facial-recognition-pipeline-with-deep-learning-in-tensorflow-66e7645015b8
def extract_faces_from_images(
        input_images_dir: DirPath,
        predictor_path: FilePath,
        recognizer_path: FilePath,
        output_images_dir: Optional[DirPath]=None,
        flag_clear_faces: bool=False,
        **kwargs: Any
    ) -> List[Image]:
    image_files = get_files_in_directory(input_images_dir, **kwargs)
    if flag_clear_faces: clear_directory(output_images_dir)
    predictor = dlib.shape_predictor(predictor_path)
    recognizer = dlib.face_recognition_model_v1(recognizer_path)
    for image_file in image_files:
        extract_faces_from_image(
            image_file=image_file,
            input_images_dir=input_images_dir,
            output_images_dir=output_images_dir,
            predictor=predictor,
            recognizer=recognizer,
            **kwargs
        )


##########################################################
# Main

def main():
    extract_faces_from_images(
        input_images_dir=INPUT_IMAGE_DIR,
        output_images_dir=OUTPUT_FACES_IMAGE_DIR,
        output_face_info_file=OUTPUT_FACE_INFO_FILE,
        sample_size=INPUT_SAMPLE_SIZE,
        show_flag=SHOW_FACES_FLAG,
        save_flag=SAVE_FLAG,
        flag_clear_faces=CLEAR_FACES_FLAG,
        overwrite=OVERWRITE_FACES_FLAG,
        predictor_path=FACE_PREDICTOR_PATH,
        recognizer_path=FACE_RECOGNIZER_PATH,
        key_indices=INNER_EYES_AND_BOTTOM_LIP,
        face_size=FACE_SIZE
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