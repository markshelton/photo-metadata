# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import datetime
import logging
import re
import random
import urllib.request
import urllib.error
import time
from envparse import env

##########################################################
# Third Party Imports

import datefinder
import pymarc
import sqlalchemy.engine
import yaml
from PIL import ImageFile

##########################################################
# Local Imports

from thickshake.mtd.database import manage_db_session, initialise_db, get_class_by_table_name, inspect_database
from thickshake.utils import consolidate_list, log_progress, setup_warnings, setup_logging, get_file_type, open_file
from thickshake.types import *

##########################################################
# Parser Configuration

INPUT_METADATA_FILE = env.str("INPUT_METADATA_FILE") # type: FilePath

OUTPUT_METADATA_FILE = env.str("OUTPUT_METADATA_FILE")

FLAG_MTD_GEOCODING = env.bool("FLAG_MTD_GEOCODING", default=False)
FLAG_MTD_DIMENSIONS = env.bool("FLAG_MTD_DIMENSIONS", default=False)
FLAG_MTD_LOGGING = env.bool("FLAG_MTD_LOGGING", default=True)
FLAG_MTD_SAMPLE = env.int("FLAG_MTD_SAMPLE", default=0)

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["drivername"] = env.str("DB_DRIVER")
DB_CONFIG["host"] = env.str("DB_HOST")
DB_CONFIG["database"] = env.str("POSTGRES_DB")
DB_CONFIG["username"] = env.str("POSTGRES_USER")
DB_CONFIG["password"] = env.str("POSTGRES_PASSWORD")

class FileType:
    JSON = ".json"
    HDF5 = ".hdf5"
    MARC21 = ".marc"
    MARCXML = ".xml"
    CSV = ".csv"

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


def get_subfields(record: PymarcRecord, field_key: str, subfield_key: str) -> List[Optional[str]]:
    fields = record.get_fields(field_key) # type: List[PymarcField]
    subfields = [get_subfield_from_field(field, subfield_key) for field in fields]
    return subfields


def split_tag_key(tag_key: str) -> Tag:
    """Split tag into a tuple of the field and subfield."""
    tag_key = tag_key.split("$")
    if len(tag_key) == 2:
        tag = Tag(field=tag_key[0], subfield=tag_key[1])
    elif len(tag_key) == 1:
        tag = Tag(field=tag_key[0], subfield=None)
    else: tag = None
    return tag


def get_subfield_from_tag(record_or_field: Union[PymarcRecord, PymarcField], tag_key: str) -> Optional[str]:
    tag = split_tag_key(tag_key)
    field_key = tag["field"]
    subfield_key = tag["subfield"]
    if isinstance(record_or_field, PymarcRecord):
        subfield = get_subfield_from_record(record_or_field, field_key, subfield_key)
    elif isinstance(record_or_field, PymarcField):
        subfield = get_subfield_from_field(record_or_field, subfield_key)
    else: subfield = None
    return subfield


def get_subfields_from_tag(record: PymarcRecord, tag_key: str) -> List[str]:
    tag = split_tag_key(tag_key)
    field_key = tag["field"]
    subfield_key = tag["subfield"]
    subfields_raw = get_subfields(record, field_key, subfield_key)
    subfields = consolidate_list(subfields_raw)
    return subfields


def get_fields_from_tag(record: PymarcRecord, tag_key: str) -> List[PymarcField]:
    tag = split_tag_key(tag_key)
    field_key = tag["field"]
    fields = record.get_fields(field_key) # type: List[PymarcField]
    return fields


##########################################################
# MARC Loader

def split_loader(data, loader, temp_uids: Dict[str, str] = None):
    table_name = ""
    parsed_data = {}
    sub_loaders = []
    for k,v in loader.items():
        if not k.startswith("$"):
            table_name, column = k.split(".")
            if "$" in str(v):
                parsed_value = get_subfield_from_tag(data, v)
            elif "." in str(v):
                parsed_value = temp_uids.get(v, None)
            else:
                parsed_value = v
            parsed_data[column] = parsed_value
        else: sub_loaders.append(v)
    return table_name, parsed_data, sub_loaders


#Fix so it can parse multiple relations per record
#fields = get_fields_from_tag(record, FIRST_TAG)
#values = [get_subfield_from_tag(field) for field in fields]

def load_record(data, loader, engine, temp_uids: Dict[str, str] = None, **kwargs: Any) -> None:
    if temp_uids is None: temp_uids = {}
    table_name, parsed_data, sub_loaders = split_loader(data, loader, temp_uids)
    if parsed_data:
        with manage_db_session(engine) as session:
            model = get_class_by_table_name(table_name)
            db_object = model(**parsed_data)
            session.add(db_object)
            if hasattr(db_object, "uuid"):
                temp_uids[table_name + ".uuid"] = db_object.uuid
    if sub_loaders:
        for sub_loader in sub_loaders:
            load_record(data, sub_loader, engine, temp_uids)


def load_database(records: List[PymarcRecord], db_config: DBConfig, logging_flag: bool = True, **kwargs: Any) -> None:
    db_engine = initialise_db(db_config, **kwargs)
    total = len(records)
    start_time = time.time()
    with open_file("/home/app/config/marc_loader.yaml") as yaml_file:
        loader = yaml.load(yaml_file)
    for i, record in enumerate(records):
        load_record(record, loader, engine=db_engine, **kwargs)
        if logging_flag: log_progress(i+1, total, start_time)


##########################################################
# Reader IO Functions


def sample_records(records: List[PymarcRecord], sample_size: int = 0) -> List[PymarcRecord]:
    return records if sample_size == 0 else random.sample(records, sample_size)


def read_marcxml(input_file: str, sample_size: int = 0, **kwargs: Any) -> List[PymarcRecord]:
    return pymarc.parse_xml_to_array(input_file)


def read_marc21(input_file: FilePath, **kwargs: Any) -> List[PymarcRecord]:
    return list(pymarc.reader.MARCReader(file(input_file)))


def read_json(input_file: FilePath, **kwargs: Any) -> List[PymarcRecord]:
    return list(pymarc.reader.JSONReader(file(input_file)))


def read_file(input_file: FilePath, sample_size: int = 0, **kwargs: Any) -> List[PymarcRecord]:
    file_type = get_file_type(input_file)
    if file_type == FileType.JSON:
        records = read_json(input_file, **kwargs)
    elif file_type == FileType.MARC21:
        records = read_marc21(input_file, **kwargs)
    elif file_type == FileType.MARCXML:
        records = read_marcxml(input_file, **kwargs)
    else: raise NotImplementedError
    records = sample_records(records, sample_size=sample_size)
    return records


##########################################################
# Main

def main():
    records = read_file(
        input_file=INPUT_METADATA_FILE,
        sample_size=FLAG_MTD_SAMPLE
    )
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