# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Python Compatibility

from __future__ import print_function, division, absolute_import
from future import standard_library
standard_library.install_aliases()

##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

##########################################################
# Local Imports

from thickshake.storage import Store

##########################################################
# Typing Configuration

from typing import Text, Any, AnyStr
FilePath = Text

##########################################################
# Constants


##########################################################
# Initialization

logger = logging.getLogger(__name__)

##########################################################
# Functions


def caption_images(image_file, **kwargs):
    # type: (FilePath, **Any) -> None
    pass



##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    main()


##########################################################
# Notes

"""
https://github.com/tensorflow/models/tree/master/research/im2txt
"""