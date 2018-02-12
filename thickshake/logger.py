# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Python Compatibility

from __future__ import print_function, division, absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()

##########################################################
# Standard Library Imports

import logging.config
import os

##########################################################
# Third Party Imports

from envparse import env
import yaml

##########################################################
# Local Imports

##########################################################
# Typing Configuration

from typing import AnyStr, Text
FilePath = Text

##########################################################
# Constants

CURRENT_FILE_DIR, _ = os.path.split(__file__)
CONFIG_DIR_PATH = "%s/_config" % CURRENT_FILE_DIR
CONFIG_LOGGING_FILE = env.str("CONFIG_LOGGING_FILE", default="%s/logging.yaml" % (CONFIG_DIR_PATH))

##########################################################


def setup_logging(config_path=CONFIG_LOGGING_FILE):
    # type: (FilePath) -> None
    """Load logging config from file, fall back to basic config if file doesn't exist."""
    logging.captureWarnings(True)
    if os.path.exists(config_path):
        with open(config_path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else: logging.basicConfig(level=logging.INFO)


##########################################################
