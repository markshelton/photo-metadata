##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

from envparse import env

##########################################################
# Local Imports

from thickshake.utils import setup_warnings, setup_logging
from thickshake.types import *

##########################################################
# Environmental Variables


##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions

def get_image_dimensions(field: PymarcField, tag: str, dimensions_flag: bool = True) -> Optional[Size]:
    if dimensions_flag is False: return None
    image_url_raw = get_subfield_from_tag(field, tag)
    if image_url_raw is None: return None
    image_url = image_url_raw + ".jpg"
    try:
        with urllib.request.urlopen(image_url) as image_file:
            parser = ImageFile.Parser()
            while True:
                data = image_file.read(1024)
                if not data:
                    break
                parser.feed(data)
                if parser.image:
                    width, height = parser.image.size
                    return Size({"width": width, "height": height})
    except urllib.error.URLError:
        logger.warning("Image not found. Size could not be determined.")
    return None


##########################################################
# Main

def main():
    pass

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()

