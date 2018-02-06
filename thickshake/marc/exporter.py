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
import os

##########################################################
# Third Party Imports

from envparse import env
import pymarc
from tqdm import tqdm
import yaml

##########################################################
# Local Imports

from thickshake.marc.utils import load_config_file, split_tag_key, get_loaders
from thickshake.storage import Database

##########################################################
# Typing Configuration

from typing import Text, Optional, Union, List, Dict, Any, AnyStr
PymarcField = Any
PymarcRecord = Any
FilePath = Text 
DBObject = Any

##########################################################
# Constants

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Functions


def get_generated_fields(loader, config):
    # type: (Dict[AnyStr, Any], Dict[AnyStr, Any]) -> Dict[AnyStr, Any]
    generated_fields = {} # type: Dict[AnyStr, Any]
    for k,v in loader.items():
        if k.startswith(config["GENERATED_FIELD_PREFIX"]):
            field = k[1:]
            tag_dict = split_tag_key(v, config["TAG_DELIMITER"])
            if tag_dict is not None:
                tag, code = tag_dict["field"], tag_dict["subfield"]
            generated_fields[tag] = {}
            if code is not None:
                generated_fields[tag][code] = field
    return generated_fields


def store_record(db_object, pymarc_record, generated_fields):
    # type: (DBObject, PymarcRecord, Dict[AnyStr, Any]) -> PymarcRecord
    for tag, code_dict in generated_fields.items():
        pymarc_field = pymarc.Field(tag, indicators=["#", "#"])
        for code, ref in code_dict.items():
            column = ref.split(".")[1]
            if hasattr(db_object, column):
                value = getattr(db_object, column)
                pymarc_field.add_subfield(code, value)
        pymarc_record.add_field(pymarc_field)
    return pymarc_record


def export_record(parent, database, loader, config, pymarc_record=None, **kwargs):
    # type: (DBObject, Database, Dict[AnyStr, Any], Dict[AnyStr, Any], PymarcRecord, **Any) -> PymarcRecord
    if pymarc_record is None: pymarc_record = pymarc.Record()
    generated_fields = get_generated_fields(loader, config)
    if generated_fields: pymarc_record = store_record(parent, pymarc_record, generated_fields)
    sub_loaders = get_loaders(loader, config)
    for child_table, sub_loader in sub_loaders.items():
        for sub_loader_i in sub_loader:
            child_table = child_table[1:].lower()
            try: children = [getattr(parent, child_table)]
            except: 
                try: children = getattr(parent, child_table + "s")
                except: continue
            for child in children:
                export_record(child, database, sub_loader_i, config, pymarc_record)
    return pymarc_record


def export_database(loader_config_file=None, **kwargs):
    # type: (FilePath, **Any) -> List[PymarcRecord]
    database = Database(**kwargs)
    with database.manage_db_session(**kwargs) as session:
        records = database.get_records(**kwargs)
        loader_map, loader_config = load_config_file(loader_config_file)
        pymarc_records = []
        for record in tqdm(records, desc="Exporting Records"):
            pymarc_record = export_record(record, database, loader_map, loader_config, **kwargs)
            pymarc_records.append(pymarc_record)
    return pymarc_records


##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    main()


##########################################################
