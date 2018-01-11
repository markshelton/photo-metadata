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

##########################################################
# Local Imports

from thickshake.utils import (
    logged, setup_logging, setup_warnings
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

FACE_SIZE = 200

INPUT_SAMPLE_SIZE = None

RESET_FILES_FLAG = True
CLEAR_FACES_FLAG=True
OVERWRITE_FACES_FLAG = True
SAVE_FACES_FLAG = True
SHOW_FACES_FLAG = False
LIST_FILES_FLAG = False

##########################################################
# Face Configuration

FACE_PREDICTOR_PATH = "/home/app/data/input/models/shape_predictor_68_face_landmarks.dat"

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


def rect_to_bb(rect: Rectangle) -> BoundingBox:
	x = rect.left()
	y = rect.top()
	w = rect.right() - x
	h = rect.bottom() - y
	return Face(x=x, y=y, w=w, h=h)


def shape_to_np(shape: Shape, dtype="int") -> List[int]:
	coords = np.zeros((68, 2), dtype=dtype)
	for i in range(0, 68):
		coords[i] = (shape.part(i).x, shape.part(i).y)
	return coords


def resize_image(
        image_original: Image,
        width_target: Optional[int] = None,
        height_target: Optional[int] = None,
        interpolation_type: str = cv2.INTER_AREA
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


def clear_directory(dir_path: Optional[DirPath]) -> None:
    if dir_path is None: return None
    try:
        shutil.rmtree(dir_path)
    except FileNotFoundError:
        logger.info("Output directory already empty.")
    os.makedirs(dir_path, exist_ok=True)


def get_files_in_directory(
        dir_path: DirPath,
        ext: Optional[str]="jpg",
        sample_size: Optional[int]= None,
        **kwargs
    ) -> List[FilePath]:
    files = [os.path.join(dir_path,fn) for fn in next(os.walk(dir_path))[2]]
    if ext: files = [f for f in files if f.endswith(ext)]
    if sample_size: files = random.sample(files, sample_size)
    return files


def maybe_increment_path(
        file_path: FilePath,
        sep: str = "_",
        flag_overwrite_faces: bool = False,
        **kwargs
    ) -> Optional[FilePath]:
    file_path_base, file_ext = os.path.splitext(file_path)
    directory_path = os.path.dirname(file_path)
    i = 1
    while True:
        full_file_path = "%s%s%s%s" % (file_path_base, sep, i, file_ext)
        if not os.path.exists(full_file_path):
            return full_file_path
        i += 1


def show_image(image_rgb: Image) -> None:
    plt.imshow(image_rgb)
    plt.show()


def save_image(
        image_rgb: Image,
        image_file: FilePath,
        input_dir: DirPath,
        output_dir: Optional[DirPath]=None,
        **kwargs
    ) -> None:
    if output_dir is None: return None
    output_file = image_file.replace(input_dir, output_dir)
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    image_file = maybe_increment_path(output_file, **kwargs)
    print(image_file)
    cv2.imwrite(image_file, image_bgr)


##########################################################
# Functions


def find_faces_in_image(image: Image) -> List[Rectangle]:
    detector = dlib.get_frontal_face_detector()
    faces = detector(image, 1)
    return faces


def detect_facial_landmarks(image: Image, face: Rectangle, predictor_path: FilePath) -> List[int]:
    predictor = dlib.shape_predictor(predictor_path)
    points = predictor(image, face)
    landmarks = list(map(lambda p: (p.x, p.y), points.parts()))
    landmarks_np = np.float32(landmarks)
    return landmarks_np


def normalize_face(
        image: Image,
        landmarks: np.array,
        key_indices: List[int] = INNER_EYES_AND_BOTTOM_LIP,
        face_template: np.array = MINMAX_TEMPLATE,
        face_size: int = 200,
        **kwargs
    ) -> Image:
    key_indices_np = np.array(key_indices)
    H = cv2.getAffineTransform(landmarks[key_indices_np], face_size * face_template[key_indices_np])
    face_norm = cv2.warpAffine(image, H, (face_size, face_size))
    return face_norm


def extract_faces_from_image(
        image_file: FilePath,
        predictor_path: FilePath,
        show_flag: bool = False,
        save_flag: bool = False,
        **kwargs: Any
    ) -> List[Image]:
    image_bgr = cv2.imread(image_file)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    faces = find_faces_in_image(image_rgb)
    faces_norm = [] # type: List[Image]
    for face in faces:
        landmarks = detect_facial_landmarks(image_rgb, face, predictor_path)
        face_norm = normalize_face(image_rgb, landmarks, **kwargs)
        if show_flag: show_image(image_rgb)
        if save_flag: save_image(face_norm, image_file, **kwargs)
        faces_norm.append(face_norm)
    return faces_norm

#TODO: Make asynchronous, see https://hackernoon.com/building-a-facial-recognition-pipeline-with-deep-learning-in-tensorflow-66e7645015b8
def extract_faces_from_images(
        image_dir: DirPath,
        output_dir: Optional[DirPath]=None,
        flag_clear_faces: bool=False,
        **kwargs: Any
    ) -> List[Image]:
    image_files = get_files_in_directory(image_dir, **kwargs)
    if flag_clear_faces: clear_directory(output_dir)
    for image_file in image_files:
        extract_faces_from_image(image_file, input_dir=image_dir, output_dir=output_dir, **kwargs)





##########################################################
# Main

def main():
    extract_faces_from_images(
        INPUT_IMAGE_DIR,
        output_dir=OUTPUT_FACES_IMAGE_DIR,
        sample_size=INPUT_SAMPLE_SIZE,
        show_flag=SHOW_FACES_FLAG,
        save_flag=SAVE_FACES_FLAG,
        flag_clear_faces=CLEAR_FACES_FLAG,
        flag_overwrite_faces=OVERWRITE_FACES_FLAG,
        predictor_path=FACE_PREDICTOR_PATH,
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