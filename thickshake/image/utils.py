##########################################################
# Standard Library Imports

import logging
import os

##########################################################
# Third Party Imports

import cv2

##########################################################
# Local Imports

from thickshake.utils import maybe_increment_path, maybe_make_directory

##########################################################
# Typing Configuration

from typing import Any, Optional
ImageType = Any
FilePath = str 
DirPath = str

##########################################################
# Constants


##########################################################
# Initialization

logger = logging.getLogger(__name__)

##########################################################
# Functions

def rect_to_bb(rect):
	x = rect.left()
	y = rect.top()
	w = rect.right() - x
	h = rect.bottom() - y
	return (x, y, w, h)


def crop(image, box, bleed):
    return image.crop((
        box[0] - bleed,
        box[1] - bleed,
        box[0] + box[2] + bleed,
        box[1] + box[3] + bleed
    ))


def show_image(image_rgb: ImageType) -> None:
    plt.imshow(image_rgb)
    plt.show()


def enhance_image(image: ImageType) -> ImageType:
    image_YCrCb = cv2.cvtColor(image, cv2.COLOR_BGR2YCR_CB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    channels = [clahe.apply(channel) for channel in cv2.split(image_YCrCb)]
    image = cv2.merge(channels)
    image = cv2.cvtColor(image_YCrCb, cv2.COLOR_YCR_CB2BGR)
    return image


def save_image(
        image_rgb: ImageType,
        image_file: FilePath,
        input_images_dir: Optional[DirPath] = None,
        output_images_dir: Optional[DirPath] = None,
        **kwargs: Any
    ) -> FilePath:
    if output_images_dir is None or input_images_dir is None: return None
    output_file = image_file.replace(input_images_dir, output_images_dir)
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    image_file = maybe_increment_path(output_file, **kwargs)
    maybe_make_directory(image_file)
    cv2.imwrite(image_file, image_bgr)
    return image_file


##########################################################