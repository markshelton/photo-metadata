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

##########################################################
# Typing Configuration

from typing import Any, Dict, Tuple, Optional, Union
FilePath = str
Tag = Dict[str, Optional[str]]
PymarcField = Any
PymarcRecord = Any


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
        head = next(iter(loader_map))
        loader_map = loader_map[head]
        return loader_map, loader_config


def load_config_file(loader_config_file):
    if loader_config_file is not None:
        return _load_config_file(loader_config_file)
    else: return _load_config_file()


def get_subfield_from_field(field: PymarcField, subfield_key: str) -> Optional[str]:
    if subfield_key not in field: return None
    subfield = field[subfield_key]
    return subfield


def get_subfield_from_record(record: PymarcRecord, field_key: str, subfield_key: str) -> Optional[str]:
    if field_key not in record: return None
    field = record[field_key]
    subfield = get_subfield_from_field(field, subfield_key)
    return subfield


def get_subfield_from_tag(record_or_field: Union[PymarcRecord, PymarcField], tag_key: str, tag_delimiter: str = "$") -> Optional[str]:
    tag = split_tag_key(tag_key, tag_delimiter)
    if tag is None: return None
    field_key = tag["field"]
    subfield_key = tag["subfield"]
    if isinstance(record_or_field, pymarc.Record):
        if field_key is None or subfield_key is None: return None
        return get_subfield_from_record(record_or_field, field_key, subfield_key)
    elif isinstance(record_or_field, pymarc.Field):
        if subfield_key is None: return None
        return get_subfield_from_field(record_or_field, subfield_key)
    else: return None


def split_tag_key(tag_key: str, tag_delimiter: str = "$") -> Optional[Tag]:
    """Split tag into a tuple of the field and subfield."""
    tag_list = tag_key.split(tag_delimiter)
    if len(tag_list) == 2:
        return dict(field=tag_list[0], subfield=tag_list[1])
    elif len(tag_list) == 1:
        return dict(field=tag_list[0], subfield=None)
    else: return None



##########################################################
