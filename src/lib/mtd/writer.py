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
import numpy as np
import os
import time
from contextlib import contextmanager

##########################################################
# Third Party Imports

from sqlalchemy import create_engine, text
from sqlalchemy.engine import url
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.orm import scoped_session, sessionmaker

##########################################################
# Local Imports

from thickshake.mtd.schema import Base
from thickshake.utils import maybe_make_directory, open_file, json_serial, log_progress
from thickshake._types import *

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions

def write_csv(records: List[ParsedRecord], output_file: FilePath) -> None:
    if not records: return None
    with open_file(output_file, 'w+', encoding='utf-8') as outfile:
        outcsv = csv.writer(outfile)
        header = records[0].keys()
        outcsv.writerow(header)
        for record in records:
            record_list = record.values()
            outcsv.writerow(record_list)


def write_json(records: JSONType, output_file: FilePath) -> None:
    if not records: return None
    with open_file(output_file, 'w+', encoding='utf-8') as outfile:
        json.dump(records, outfile, indent=2, default=json_serial)


def write_hdf5(records: List[Record], output_file: FilePath) -> None:
    with h5py.File(output_file, "a") as f:
        total = len(result)
        start_time = time.time()
        for i, record in enumerate(result):
            key = record["image_id"]
            grp = f.require_group(key)
            index = str(len(grp.keys()) + 1)
            record_serial = json.dumps(record, default=json_serial)
            dt = h5py.special_dtype(vlen=str)
            grp.require_dataset(index, data=record_serial, shape=(1,), dtype=dt)
            log_progress(i+1, total, start_time, interval=100)


def write_marc21(records: List[Record], output_file: FilePath) -> None:
    pass


def write_marcxml(records: List[Record], output_file: FilePath) -> None:
    pass


def write_log(records: List[Any]) -> None:
    if not records: return None
    for record in records:
        logger.info(str(record))