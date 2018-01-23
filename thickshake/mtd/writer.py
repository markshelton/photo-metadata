# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import csv
import json
import logging
import time

##########################################################
# Third Party Imports

import h5py

##########################################################
# Local Imports

from thickshake.utils import (
    open_file, json_serial, log_progress,
    setup_logging, setup_warnings, get_file_type,
)

##########################################################
# Typing Configuration

from typing import List, Any, Union, Dict

FilePath = str
JSONType = Union[Dict[str, Any], List[Any]]


##########################################################
# Environmental Variables

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
# Functions


def write_csv(records: List[Any], output_file: FilePath, **kwargs: Any) -> None:
    if not records: return None
    with open_file(output_file, 'w+', encoding='utf-8') as outfile:
        outcsv = csv.writer(outfile)
        header = records[0].keys()
        outcsv.writerow(header)
        for record in records:
            record_list = record.values()
            outcsv.writerow(record_list)


def write_json(records: JSONType, output_file: FilePath, **kwargs: Any) -> None:
    if not records: return None
    with open_file(output_file, 'w+', encoding='utf-8') as outfile:
        json.dump(records, outfile, indent=2, default=json_serial)


def write_hdf5(records: List[Any], output_file: FilePath, logging_flag: bool = True, **kwargs: Any) -> None:
    with h5py.File(output_file, "a") as f:
        total = len(records)
        start_time = time.time()
        for i, record in enumerate(records):
            key = record["image_id"]
            grp = f.require_group(key)
            index = str(len(grp.keys()) + 1)
            dt = h5py.special_dtype(vlen=str)
            f.attrs.create("columns", list(record.keys()),dtype=dt)
            record_serial = json.dumps(record, default=json_serial)
            grp.require_dataset(index, data=record_serial, shape=(1,), dtype=dt)
            if logging_flag: log_progress(i+1, total, start_time, interval=100)


def write_marc21(records: List[Any], output_file: FilePath, **kwargs: Any) -> None:
    pass


def write_marcxml(records: List[Any], output_file: FilePath, **kwargs: Any) -> None:
    pass


def write_log(records: List[Any], **kwargs: Any) -> None:
    if not records: return None
    for record in records:
        logger.info(str(record))


def write_file(records: List[Any], output_file: FilePath, **kwargs: Any) -> None:
    file_type = get_file_type(output_file) #DONE
    if file_type == FileType.JSON:
        write_json(records, output_file, **kwargs) #DONE
    elif file_type == FileType.HDF5:
        write_hdf5(records, output_file, **kwargs) #DONE
    elif file_type == FileType.MARC21:
        write_marc21(records, output_file, **kwargs) #TODO
    elif file_type == FileType.MARCXML:
        write_marcxml(records, output_file, **kwargs) #TODO
    elif file_type == FileType.CSV:
        write_csv(records, output_file, **kwargs) #DONE
    else: raise NotImplementedError


##########################################################
# Main


def main():
    pass

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()

##########################################################
