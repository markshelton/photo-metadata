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


def make_db_tables(db_engine: Engine) -> None:
    Base.metadata.create_all(db_engine)


def make_db_engine(db_config: DBConfig) -> Engine:
    db_url = url.URL(**db_config)
    maybe_make_directory(db_config["database"])
    db_engine = create_engine(db_url, encoding='utf8', convert_unicode=True)
    return db_engine


def initialise_db(db_config: DBConfig, **kwargs: Any) -> Engine:
    db_engine = make_db_engine(db_config)
    make_db_tables(db_engine)
    return db_engine


@contextmanager
def manage_db_session(db_engine: Engine) -> Iterator[Session]:
    Session = sessionmaker(autocommit=False, autoflush=True, bind=db_engine)
    session = scoped_session(Session)
    try:
        yield session
        session.commit()
    except (IntegrityError, DataError) as e:
        session.rollback()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


def dump_database(db_config: DBConfig) -> List[Dict[str, Any]]:
    db_engine = initialise_db(db_config)
    with manage_db_session(db_engine) as session:
        sql_text =  "SELECT *\n"
        sql_text += "FROM image\n"
        sql_text += "NATURAL LEFT JOIN collection\n"
        sql_text += "NATURAL LEFT JOIN collection_subject\n"
        sql_text += "NATURAL LEFT JOIN collection_location\n"
        sql_text += "NATURAL LEFT JOIN collection_topic\n"
        sql_text += "NATURAL LEFT JOIN subject;"
        result = session.execute(text(sql_text)).fetchall()
        result = [dict(record) for record in result]
        return result  #Total = 52,672 -- Check?


def export_records_to_csv(records: List[ParsedRecord], output_file: FilePath) -> None:
    if not records: return None
    with open_file(output_file, 'w+', encoding='utf-8') as outfile:
        outcsv = csv.writer(outfile)
        header = records[0].keys()
        outcsv.writerow(header)
        for record in records:
            record_list = record.values()
            outcsv.writerow(record_list)


def export_records_to_json(records: JSONType, output_file: FilePath) -> None:
    if not records: return None
    with open_file(output_file, 'w+', encoding='utf-8') as outfile:
        json.dump(records, outfile, indent=2, default=json_serial)


def export_records_to_log(records: List[Any]) -> None:
    if not records: return None
    for record in records:
        logger.info(str(record))


def export_records_to_hdf5(db_config: DBConfig, metadata_file: FilePath) -> None:
    result = dump_database(db_config)
    with h5py.File(metadata_file, "a") as f:
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


##########################################################
