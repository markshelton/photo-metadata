# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import logging
import os

##########################################################
# Third Party Imports

from envparse import env
import pymarc
import yaml

##########################################################
# Local Imports

from thickshake.database import Database
from thickshake.helpers import setup

##########################################################
# Typing Configuration

from typing import Optional, Union, List, Dict, Any

##########################################################
# Constants

CURRENT_FILE_DIR, _ = os.path.split(__file__)
METADATA_CONFIG_FILE = env.str("METADATA_CONFIG_FILE", default="%s/config.yaml" % (CURRENT_FILE_DIR))

##########################################################
# Database Configuration

database = Database()

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions

def export_to_pymarc():
    pass

##########################################################
# Main

def main() -> None:
    pass


if __name__ == "__main__":
    setup()
    main()

##########################################################
