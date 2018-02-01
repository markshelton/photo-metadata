##########################################################
# Standard Library Imports

import logging
import os
from functools import partial

##########################################################
# Third Party Imports

import cv2
from envparse import env
import hyperopt
from PIL import Image
import numpy as np
import pyocr

##########################################################
# Local Imports

from thickshake.image.image import crop
from thickshake.storage.store import Store

##########################################################
# Typing Configuration

from typing import Any, Set, List
FilePath = str
ImageType = Any
Rect = Any

##########################################################
# Constants

CURRENT_FILE_DIR, _ = os.path.split(__file__)
DATA_DIR_PATH = "%s/../_data/image/ocr" % CURRENT_FILE_DIR
DICTIONARY_PATH = env.str("DICTIONARY_PATH", default="%s/dictionary.txt" % DATA_DIR_PATH)
CLASSIFIER_NM1_PATH = env.str("CLASSIFIER_NM1_PATH", default="%s/trained_classifierNM1.xml" % DATA_DIR_PATH)
CLASSIFIER_NM2_PATH = env.str("CLASSIFIER_NM2_PATH", default="%s/trained_classifierNM2.xml" % DATA_DIR_PATH)
CLASSIFIER_ER_GROUP_PATH = env.str("CLASSIFIER_ER_GROUP_PATH", default="%s/trained_classifier_erGrouping.xml" % DATA_DIR_PATH)

SEARCH_SPACE = hyperopt.hp.choice('params',[
    {
        "bleed": hyperopt.hp.uniform("bleed", 0, 50),
        "binary": hyperopt.hp.uniform("binary", 0, 255),
    }
])

##########################################################
# Initialization

logger = logging.getLogger(__name__)

##########################################################
# Functions

#TODO: Load from most common words stored in database
def load_dictionary(dictionary_file: FilePath = DICTIONARY_PATH) -> Set:
    with open(dictionary_file) as f:
        dictionary = set()
        dictionary.update([word.strip().lower() for word in f])
        dictionary.update(["Perth", "Western", "Australia"])
        return dictionary


def get_text_boxes(image: Image) -> List[Rect]:
    channels = cv2.text.computeNMChannels(image)
    cn = len(channels)-1
    for c in range(0,cn):
        channels.append((255-channels[c]))
    rects_array = []
    for channel in channels:
        erc1 = cv2.text.loadClassifierNM1(CLASSIFIER_NM1_PATH)
        er1 = cv2.text.createERFilterNM1(erc1,4,0.00015,0.15,0.2,True,0.1)
        erc2 = cv2.text.loadClassifierNM2(CLASSIFIER_NM2_PATH)
        er2 = cv2.text.createERFilterNM2(erc2,0.5)
        regions = cv2.text.detectRegions(channel,er1,er2)
        rects = cv2.text.erGrouping(image, channel, [x.tolist() for x in regions],
            cv2.text.ERGROUPING_ORIENTATION_ANY,CLASSIFIER_ER_GROUP_PATH,0.5)
        rects_array.extend(rects)
    return rects_array
    

def calc_accuracy(text, dictionary):
    text = text.strip().lower()
    length = len(text.replace(" ", ""))
    if length == 0:return 0
    valid_characters = 0
    for word in text.split(" "):
        if word in dictionary:
            valid_characters += len(word)
    score = valid_characters / float(length)
    return score


def image_to_string(image) -> str:
    tools = pyocr.get_available_tools()
    tool = tools[0]
    text = tool.image_to_string(image)
    return text


def extract_text(params, image, box):
    image_crop = crop(image, box, params["bleed"])
    image_binary = image_crop.point(lambda x: 0 if x < params["binary"] else 255)
    text = image_to_string(image_binary)
    return text


def _objective(params, image, box, dictionary):
    #print(params)
    text = extract_text(params, image, box)
    score = calc_accuracy(text, dictionary)
    return score * -1


def read_text(image_file: FilePath, **kwargs: Any) -> None:
    dictionary = load_dictionary()
    image = cv2.imread(image_file)
    boxes = get_text_boxes(image)
    image = Image.open(image_file)
    text_image = []
    boxes = set(map(tuple, boxes))
    for box in boxes:
        objective = partial(_objective, image=image, box=box, dictionary=dictionary)
        best_params = hyperopt.fmin(
            objective,
            space=SEARCH_SPACE,
            algo=hyperopt.tpe.suggest,
            max_evals=25
        )
        text_box = extract_text(best_params, image, box)
        try: text_box = text_box.encode("utf8")
        except: pass
        if text_box: text_image.append(text_box)
        print(box, text_box)
    return text_image


##########################################################
# Main


def main() -> None:
    test_image = "/home/app/data/input/images/JPEG_Convert_Resolution_1024/slwa_b3104339_3_master.jpg"
    text = read_text(test_image)
    print(text)

if __name__ == "__main__":
    main()

##########################################################
