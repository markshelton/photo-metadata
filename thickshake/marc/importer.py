# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

from collections import defaultdict
import logging
import os
from pprint import pprint

##########################################################
# Third Party Imports

import pymarc
from tqdm import tqdm

##########################################################
# Local Imports

from thickshake.marc.reader import read_file
from thickshake.marc.utils import load_config_file, get_subfield_from_tag, get_loaders
from thickshake.storage import Database

##########################################################
# Typing Configuration

from typing import Optional, Union, List, Dict, Any, Tuple

Tag = Dict[str, Optional[str]]
PymarcField = Any
PymarcRecord = Any
FilePath = str
DBSession = Any
DBObject = Any

##########################################################
# Constants


##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


def get_data(data, loader, config):
    # type: (Union[PymarcField, PymarcRecord], Dict[str, Any], Dict[str, Any]) -> List[Union[PymarcField, PymarcRecord]]
    fields = [] # type: List[str]
    if not isinstance(data, pymarc.Field): 
        for k,v in loader.items():
            if not k.startswith(config["GENERATED_FIELD_PREFIX"]) and not k.startswith(config["TABLE_PREFIX"]):
                if config["TAG_DELIMITER"] in str(v):
                    field = str(v).split(config["TAG_DELIMITER"])[0]
                    fields.append(field)
        if len(set(fields)) == 1:
            return data.get_fields(fields[0])
    return [data]


def parse_record(record, loader, config, foreign_keys):
    # type: (Union[PymarcField, PymarcRecord], Dict[str, Any], Dict[str, Any], Dict[str, str]) -> Dict[str, Any]
    parsed_record = {} # type: Dict[str, Optional[str]]
    for k,v in loader.items():
        if not k.startswith(config["TABLE_PREFIX"]):
            table_name, column = k.split(".")
            if k.startswith(config["GENERATED_FIELD_PREFIX"]):
                parsed_value = None
            elif str(v).startswith(config["TABLE_PREFIX"]):
                table = str(v).replace(config["TABLE_PREFIX"], "").lower()
                if foreign_keys[table]:
                    parsed_value = foreign_keys[table][-1]
                else: parsed_value = None
            elif config["TAG_DELIMITER"] in str(v):
                parsed_value = get_subfield_from_tag(record, v, tag_delimiter=config["TAG_DELIMITER"])
            else: parsed_value = v
            parsed_record[column] = parsed_value
    return parsed_record


def store_record(parsed_record, foreign_keys, table_name, database, **kwargs):
    # type: (Dict[str, Any], Dict[str, str], str, Database, **Any) -> Dict[str, str]
    with database.manage_db_session(**kwargs) as session:
        db_object = database.merge_record(table_name, parsed_record, foreign_keys, **kwargs)
        if hasattr(db_object, "uuid"): return db_object.uuid
    return None


def load_record(data, loader, config, database, table_name="record", foreign_keys=None, **kwargs):
    # type: (Union[PymarcField, PymarcRecord], Dict[str, Any], Dict[str, Any], Database, str, Dict[str, Any], **Any) -> None
    if foreign_keys is None: foreign_keys = defaultdict(list)
    records = get_data(data, loader, config)
    sub_loaders = get_loaders(loader, config)
    for record in records:
        parsed_record = parse_record(record, loader, config, foreign_keys)
        new_primary_key = store_record(parsed_record, foreign_keys, table_name, database, **kwargs) if parsed_record else None
        foreign_keys[table_name].append(new_primary_key)
        for sub_table, sub_loader in sub_loaders.items():
            for sub_loader_i in sub_loader:
                load_record(data=record, table_name=sub_table, loader=sub_loader_i, config=config, database=database, foreign_keys=foreign_keys)
        foreign_keys[table_name].pop()


def load_database(records, loader_config_file, **kwargs):
    # type: (List[PymarcRecord], FilePath, **Any) -> None
    database = Database(**kwargs)
    loader_map, loader_config = load_config_file(loader_config_file)
    for record in tqdm(records, desc="Loading Records"):
        load_record(data=record, loader=loader_map, config=loader_config, database=database, **kwargs)


##########################################################
# Scripts


def main():
    records = read_file(input_metadata_file="/home/app/data/input/metadata/marc21.xml", sample=20)
    load_database(records, verbosity="DEBUG")


if __name__ == "__main__":
    main()


##########################################################
