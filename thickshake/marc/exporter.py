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
from tqdm import tqdm
import yaml

##########################################################
# Local Imports

from thickshake.storage.database import Database
from thickshake.marc.utils import load_config_file, split_tag_key

##########################################################
# Typing Configuration

from typing import Optional, Union, List, Dict, Any
PymarcField = Any
PymarcRecord = Any
FilePath = str 

##########################################################
# Constants

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Functions


def get_loaders(loader: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    loaders = {k:v for k,v in loader.items() if k.startswith(config["TABLE_PREFIX"])}
    return loaders


def get_generated_fields(loader: Dict[str, Any], config: Dict[str, Any]) -> Optional[str]:
    generated_fields = {}
    for k,v in loader.items():
        if k.startswith(config["GENERATED_FIELD_PREFIX"]):
            field = k[1:]
            tag_dict = split_tag_key(v, config["TAG_DELIMITER"])
            if tag_dict is not None:
                tag, code = tag_dict["field"], tag_dict["subfield"]
            generated_fields[tag] = {}
            if code is not None: generated_fields[tag][code] = field
    return generated_fields


def store_record(db_object, pymarc_record, generated_fields):
    for tag, code_dict in generated_fields.items():
        #print(tag, code_dict)
        pymarc_field = pymarc.Field(tag, indicators=["0", "1"])
        for code, ref in code_dict.items():
            column = ref.split(".")[1]
            if hasattr(db_object, column):
                value = getattr(db_object, column)
                pymarc_field.add_subfield(code, value)
        pymarc_record.add_field(pymarc_field)
    return pymarc_record


def export_record(parent, database, loader, config, pymarc_record: Any = None, **kwargs):
    if pymarc_record is None: pymarc_record = pymarc.Record()
    #input(pymarc_record)
    generated_fields = get_generated_fields(loader, config)
    if generated_fields: pymarc_record = store_record(parent, pymarc_record, generated_fields)
    sub_loaders = get_loaders(loader, config)
    for child_table, sub_loader in sub_loaders.items():
        child_table = child_table[1:].lower()
        try: children = [getattr(parent, child_table)]
        except: 
            try: children = getattr(parent, child_table + "s")
            except: continue
        for child in children:
            export_record(child, database, sub_loader, config, pymarc_record)
    return pymarc_record


def export_database(loader_config_file: FilePath=None, **kwargs) -> List[PymarcRecord]:
    database = Database(**kwargs)
    with database.manage_db_session(**kwargs) as session:
        records = database.get_records(**kwargs)
        loader_map, loader_config = load_config_file(loader_config_file)
        pymarc_records = []
        for record in tqdm(records, desc="Exporting Records"):
            pymarc_record = export_record(record, database, loader_map, loader_config, **kwargs)
            pymarc_records.append(pymarc_record)
    input(pymarc_records)
    return pymarc_records

##########################################################
# Main

def main() -> None:
    pass


if __name__ == "__main__":
    main()

##########################################################
