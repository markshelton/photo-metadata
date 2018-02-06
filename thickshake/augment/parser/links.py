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

from envparse import env
from PIL import ImageFile
import requests

##########################################################
# Local Imports

from typing import Text, Optional, Dict, Any, AnyStr
FilePath = Text
Size = Dict[AnyStr, AnyStr]

##########################################################
# Environmental Variables

SLWA_BASE_URL = env.str("SLWA_BASE_URL", default = "http://purl.slwa.wa.gov.au/")

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


def get_image_dimensions(image_url, **kwargs):
    # type: (AnyStr, **Any) -> Optional[Size]
    if image_url is None: return {"width": None, "height": None} 
    try:
        with requests.get(image_url) as image_file:
            parser = ImageFile.Parser()
            while True:
                data = image_file.read(1024)
                if not data:
                    break
                parser.feed(data)
                if parser.image:
                    width, height = parser.image.size
                    return {"width": width, "height": height}
    except: logger.warning("Image not found. Size could not be determined.")
    return {"width": None, "height": None}


def get_id_from_url(image_file):
    # type: (Optional[FilePath]) -> Optional[AnyStr]
    if image_file is None: return None
    image_id = image_file.split("/")[-1].split(".")[0] # type: Optional[AnyStr]
    return image_id


def extract_image_links(text, **kwargs):
    # type: (AnyStr, **Any) -> Dict[AnyStr, AnyStr]
    image_label = get_id_from_url(text)
    image_url_raw = text + ".jpg"
    image_url_thumb = text + ".png"
    return {
        "image_label": image_label,
        "image_url_raw": image_url_raw,
        "image_url_thumb": image_url_thumb,
    }


def extract_image_dimensions(text, **kwargs):
    # type: (AnyStr, **Any) -> Dict[AnyStr, AnyStr]
    image_dimensions = get_image_dimensions(text)
    return {
        "image_height": image_dimensions.get("height", None),
        "image_width": image_dimensions.get("width", None)
    }


##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    main()


##########################################################
