# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import csv
import h5py
import json
import logging
import os
import time
from envparse import env

##########################################################
# Third Party Imports

##########################################################
# Local Imports

from thickshake.utils import open_file, json_serial, log_progress, setup_logging, setup_warnings
from thickshake.types import *

##########################################################
# Environmental Variables

OUTPUT_IMAGE_DATA_FILE =  env.str("OUTPUT_IMAGE_DATA_FILE", default="/home/app/data/output/faces.hdf5")
OUTPUT_METADATA_FILE =  env.str("OUTPUT_METADATA_FILE", default="/home/app/data/output/metadata.hdf5")

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["drivername"] = env.str("DB_DRIVER")
DB_CONFIG["host"] = env.str("DB_HOST")
DB_CONFIG["database"] = env.str("POSTGRES_DB")
DB_CONFIG["username"] = env.str("POSTGRES_USER")
DB_CONFIG["password"] = env.str("POSTGRES_PASSWORD")

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


def write_hdf5(records: List[Any], output_file: FilePath, logging_flag: bool = True, **kwargs) -> None:
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


##########################################################
# Main


def main():
    pass

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()