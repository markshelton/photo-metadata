# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import csv
import json
import logging
import os
import time

##########################################################
# Third Party Imports

import h5py
from tqdm import tqdm

##########################################################
# Local Imports

from thickshake.storage import Store, Database
from thickshake.utils import open_file, json_serial, get_file_type, FileType

##########################################################
# Typing Configuration

from typing import List, Any, Union, Dict

FilePath = str
JSONType = Union[Dict[str, Any], List[Any]]


##########################################################
# Environmental Variables


##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


def write_csv(records, output_file, **kwargs):
    # type: (List[Any], FilePath, **Any) -> None
    if not records: return None
    with open_file(output_file, 'w+', encoding='utf-8') as outfile:
        outcsv = csv.writer(outfile)
        header = records[0].keys()
        outcsv.writerow(header)
        for record in tqdm(records, desc="Writing Records"):
            record_list = record.values()
            outcsv.writerow(record_list)


def write_json(records, output_file, **kwargs):
    # type: (List[Any], FilePath, **Any) -> None
    if not records: return None
    with open_file(output_file, 'w+', encoding='utf-8') as outfile:
        outfile.write("[")
        length = len(records)
        for i, record in enumerate(tqdm(records, desc="Writing Records")):
            json.dump(record, outfile, indent=2, default=json_serial)
            if i < length -1: outfile.write(",")
        outfile.write("]")


def write_hdf5(records, output_file, **kwargs):
    # type: (List[Any], FilePath, **Any) -> None
    with h5py.File(output_file, "a") as f:
        total = len(records)
        start_time = time.time()
        for record in tqdm(records, desc="Writing Records"):
            key = str(record["uuid"])
            grp = f.require_group(key)
            index = str(len(grp.keys()) + 1)
            dt = h5py.special_dtype(vlen=str)
            f.attrs.create("columns", list(record.keys()),dtype=dt)
            record_serial = json.dumps(record, default=json_serial)
            grp.require_dataset(index, data=record_serial, shape=(1,), dtype=dt)


def write_log(records, **kwargs):
    # type: (List[Any], **Any) -> None
    if not records: return None
    for record in records:
        logger.info(str(record))


#TODO
def write_to_store(records, store, **kwargs):
    # type: (List[Any], Store, **Any) -> None
    pass


def write_flat_file(records, output_file, force=False, **kwargs):
    # type: (List[Any], FilePath, bool, **Any) -> None
    if not force and os.path.exists(output_file): raise IOError
    file_type = get_file_type(output_file)
    if file_type == FileType.JSON:
        write_json(records, output_file, **kwargs)
    elif file_type == FileType.HDF5:
        write_hdf5(records, output_file, **kwargs)
    elif file_type == FileType.CSV:
        write_csv(records, output_file, **kwargs)
    else: raise NotImplementedError


def export_flat_file(output_file, force=False, **kwargs):
    # type: (FilePath, bool, **Any) -> None
    if not force and os.path.exists(output_file): raise IOError
    database = Database(**kwargs)
    records = database.dump(force=force, **kwargs)
    write_flat_file(records, output_file, force=force, **kwargs)


def export_database_to_store(**kwargs):
    # type: (**Any) -> None
    database = Database(**kwargs)
    records = database.dump()
    store = Store(**kwargs)
    write_to_store(records, store, **kwargs)


##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    main()


##########################################################
