# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import logging
import os
import time

##########################################################
# Third Party Imports

import pymarc
import yaml

##########################################################
# Local Imports

from thickshake.database import Database
from thickshake.utils import (
    setup_warnings, setup_logging,
    log_progress, open_file,
)

##########################################################
# Typing Configuration

from typing import Optional, Union, List, Dict, Any

Tag = Dict[str, Optional[str]]
PymarcField = Any
PymarcRecord = Any

##########################################################
# Constants

CURRENT_FILE_DIR, _ = os.path.split(__file__)
METADATA_CONFIG_FILE = "%s/deps/marc_map.yaml" % (CURRENT_FILE_DIR)
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
# Helper Functions


def get_subfield_from_field(field: PymarcField, subfield_key: str) -> Optional[str]:
    if subfield_key not in field: return None
    subfield = field[subfield_key]
    return subfield


def get_subfield_from_record(record: PymarcRecord, field_key: str, subfield_key: str) -> Optional[str]:
    if field_key not in record: return None
    field = record[field_key]
    subfield = get_subfield_from_field(field, subfield_key)
    return subfield


def get_subfield_from_tag(record_or_field: Union[PymarcRecord, PymarcField], tag_key: str) -> Optional[str]:
    tag = split_tag_key(tag_key)
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


def split_tag_key(tag_key: str) -> Optional[Tag]:
    """Split tag into a tuple of the field and subfield."""
    tag_list = tag_key.split(MTD_LOADER_TAG_DELIMITER)
    if len(tag_key) == 2:
        return Tag(field=tag_list[0], subfield=tag_list[1])
    elif len(tag_key) == 1:
        return Tag(field=tag_list[0], subfield=None)
    else: return None


##########################################################
# Functions


def get_data(
        data: Union[PymarcField, PymarcRecord],
        loader: Dict[str, Any]
    ) -> Union[List[PymarcField], List[PymarcRecord]]:
    fields = [] # type: List[str]
    if not isinstance(data, pymarc.Field): 
        for k,v in loader.items():
            if not k.startswith(MTD_LOADER_TABLE_PREFIX):
                if MTD_LOADER_TAG_DELIMITER in str(v):
                    field = str(v).split(MTD_LOADER_TAG_DELIMITER)[0]
                    fields.append(field)
        if len(set(fields)) == 1:
            return data.get_fields(fields[0])
    return [data]


def get_loaders(loader: Dict[str, Any]) -> List[Dict[str, Any]]:
    loaders = [v for k,v in loader.items() if k.startswith(MTD_LOADER_TABLE_PREFIX)]
    return loaders


def get_table_name(loader: Dict[str, Any]) -> Optional[str]:
    for k,v in loader.items():
        if not k.startswith(MTD_LOADER_TABLE_PREFIX):
            table_name = k.split(MTD_LOADER_TABLE_DELIMITER)[0]
            return table_name
    return None


def parse_record(
        record: Union[PymarcField, PymarcRecord],
        loader: Dict[str, Any],
        temp_uids: Dict[str, str]
    ) -> Dict[str, Any]:
    parsed_record = {} # type: Dict[str, Optional[str]]
    for k,v in loader.items():
        if not k.startswith(MTD_LOADER_TABLE_PREFIX):
            table_name, column = k.split(".")
            if MTD_LOADER_TAG_DELIMITER in str(v):
                parsed_value = get_subfield_from_tag(record, v)
            elif MTD_LOADER_TABLE_DELIMITER in str(v):
                parsed_value = temp_uids.get(v, None)
            else: parsed_value = v
            parsed_record[column] = parsed_value
    return parsed_record


#What happens if a unique constraint is violated on a data table?
#How do I give the existing uuid to the relationship table? 
def store_record(
        parsed_record: Dict[str, Any],
        temp_uids: Dict[str, str],
        table_name: str
    ) -> Dict[str, str]:
    with database.manage_db_session() as session:
        model = database.get_class_by_table_name(table_name)
        db_object = model(**parsed_record)
        session.add(db_object)
        session.flush()
        if hasattr(db_object, "uuid"):
            temp_uids[table_name + ".uuid"] = db_object.uuid
    return temp_uids


def load_record(
        data: Union[PymarcField, PymarcRecord],
        loader: Dict[str, Any],
        temp_uids: Dict[str, str] = None,
        **kwargs: Any
    ) -> None:
    if temp_uids is None: temp_uids = {}
    records = get_data(data, loader)
    sub_loaders = get_loaders(loader)
    table_name = get_table_name(loader)
    for record in records:
        if table_name:
            parsed_record = parse_record(record, loader, temp_uids)
            temp_uids = store_record(parsed_record, engine, temp_uids, table_name)
        for sub_loader in sub_loaders:
            load_record(data=record, loader=sub_loader, temp_uids=temp_uids)


def load_database(
        records: List[PymarcRecord],
        loader_config_file: str,
        logging_flag: bool = True,
        **kwargs: Any
    ) -> None:
    total = len(records)
    start_time = time.time()
    with open_file(loader_config_file) as yaml_file:
        loader = yaml.load(yaml_file)
    for i, record in enumerate(records):
        load_record(data=record, loader=loader, **kwargs)
        if logging_flag: log_progress(i+1, total, start_time)


##########################################################
# Main


def main():
    load_database(
        records=records,
        db_config=DB_CONFIG,
        clear_flag=True,
        logging_flag=True,
    )


if __name__ == "__main__":
    setup_warnings()
    setup_logging()
    main()


##########################################################
