##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

##########################################################
# Local Imports

from thickshake.storage.store import Store
from thickshake.helpers import setup

##########################################################
# Typing Configuration

from typing import Any
FilePath = str

##########################################################
# Constants


##########################################################
# Initialization

logger = logging.get_logger(__name__)

##########################################################
# Functions


def caption_images(image_file: FilePath, **kwargs: Any) -> None:
    pass



##########################################################
# Main


def main() -> None:
    pass


if __name__ == "__main__":
    setup()
    main()


##########################################################
# Notes

"""
https://github.com/tensorflow/models/tree/master/research/im2txt
"""