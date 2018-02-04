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

from typing import Any, Optional, List
ImageType = Any
Rect = Any
FilePath = str 
DirPath = str

##########################################################
# Constants


##########################################################
# Initialization

logger = logging.getLogger(__name__)

##########################################################
# Functions


def rect_to_bb(rect: Rect) -> List[float]:
	x = rect.left()
	y = rect.top()
	w = rect.right() - x
	h = rect.bottom() - y
	return (x, y, w, h)


def crop(image: ImageType, box: List[float], bleed: float) -> ImageType:
    return image.crop((
        box[0] - bleed,
        box[1] - bleed,
        box[0] + box[2] + bleed,
        box[1] + box[3] + bleed
    ))


def show_image(image_rgb: ImageType) -> None:
    from matplotlib import pyplot as plt
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
        sub_folder: str = None,
        output_file: Optional[FilePath] = None,
        input_file: Optional[FilePath] = None,
        output_image_dir: Optional[DirPath] = None,
        **kwargs: Any
    ) -> FilePath:
    if output_file is None and (input_file is not None and output_image_dir is not None):
        output_file = generate_output_path(input_file, output_dir=output_image_dir, sub_folder=sub_folder)  
    output_file = maybe_increment_path(output_file, **kwargs)
    maybe_make_directory(output_file)
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_file, image_bgr)
    return output_file


def handle_image(image, input_file, graphics, dry_run, **kwargs) -> None:
    if graphics: show_image(image)
    if not dry_run: save_image(image, input_file=input_file, **kwargs)


def get_image(image_file):
    image_bgr = cv2.imread(image_file)
    image_bgr = enhance_image(image_bgr)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    return image_rgb


##########################################################


def main():
    process_images()


if __name__ == "__main__":
    main()


##########################################################
