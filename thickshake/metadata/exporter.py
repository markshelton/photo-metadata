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

import pymarc
import yaml

##########################################################
# Local Imports

from thickshake.database import Database
from thickshake.utils import setup_warnings, setup_logging

##########################################################
# Typing Configuration

from typing import Optional, Union, List, Dict, Any

##########################################################
# Constants

CURRENT_FILE_DIR, _ = os.path.split(__file__)
METADATA_CONFIG_FILE = "%s/deps/loader.yaml" % (CURRENT_FILE_DIR)
METADATA_CONFIG_TABLE_PREFIX="$"
METADATA_CONFIG_TABLE_DELIMITER="."
METADATA_CONFIG_TAG_DELIMITER="$"

##########################################################
# Database Configuration

database = Database()

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


def dump_database():
    sql_text =  "SELECT *\n"
    sql_text += "FROM image\n"
    sql_text += "NATURAL LEFT JOIN image_location\n"
    sql_text += "NATURAL LEFT JOIN location\n"
    sql_text += "NATURAL LEFT JOIN record\n"
    sql_text += "NATURAL LEFT JOIN record_subject\n"
    sql_text += "NATURAL LEFT JOIN subject\n"
    sql_text += "NATURAL LEFT JOIN record_location\n"
    sql_text += "NATURAL LEFT JOIN record_topic\n"
    sql_text += "NATURAL LEFT JOIN topic\n"
    sql_text += ";"
    results = database.execute_text_query(sql_text)
    return results


def export_to_pymarc():
    pass

##########################################################
# Main

def main() -> None:
    pass


if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()

##########################################################
