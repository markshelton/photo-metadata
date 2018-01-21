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

SLWA_BASE_URL = env.str("SLWA_BASE_URL", default = "http://purl.slwa.wa.gov.au/")

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


def get_image_url(image_id: str, method: str = None, base_url: Optional[str] = SLWA_BASE_URL) -> Union[str, Dict[str, str]]:
    image_urls = {
        "main": base_url + image_id,
        "raw": base_url + image_id + ".jpg",
        "thumb": base_url + image_id + ".png",
    }
    if method: return image_urls["method"]
    else: return image_urls


##########################################################
# Main

def main():
    pass

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()

