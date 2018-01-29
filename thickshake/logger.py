# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
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

FilePath = str

##########################################################
# Constants

CURRENT_FILE_DIR, _ = os.path.split(__file__)
CONFIG_LOGGING_FILE = env.str("CONFIG_LOGGING_FILE", default="%s/logging.yaml" % (CURRENT_FILE_DIR))

##########################################################


def setup_logging(config_path: FilePath=CONFIG_LOGGING_FILE) -> None:
    logging.captureWarnings(True)
    if os.path.exists(config_path):
        with open(config_path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)


##########################################################