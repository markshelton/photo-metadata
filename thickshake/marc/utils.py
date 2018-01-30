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

import yaml

##########################################################
# Local Imports

##########################################################
# Typing Configuration

from typing import Any, Dict, Tuple
FilePath = str

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Constants

CURRENT_FILE_DIR, _ = os.path.split(__file__)
METADATA_CONFIG_FILE = "%s/config.yaml" % (CURRENT_FILE_DIR)

##########################################################
# Functions


def _load_config_file(loader_config_file: FilePath=METADATA_CONFIG_FILE) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    with open(loader_config_file) as yaml_file:
        documents = yaml.safe_load_all(yaml_file)
        loader_config = next(documents)
        loader_map = next(documents)
        return loader_map, loader_config


def load_config_file(loader_config_file):
    if loader_config_file is not None:
        return _load_config_file(loader_config_file)
    else: return _load_config_file()


##########################################################
