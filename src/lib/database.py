##########################################################
# Standard Library Imports

import os
import csv
import logging
import json
from contextlib import contextmanager

##########################################################
# Third Party Imports

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.engine import url
from sqlalchemy.exc import IntegrityError

##########################################################
# Local Imports

from thickshake.schema import Base
from thickshake.utils import (
    check_and_make_directory, open_file, json_serial
)
from thickshake._types import (
    List, Optional, Dict, Any, Iterator, TypedDict,
    ParsedRecord, DBConfig, FilePath, JSONType,
    Engine, Session, File, 
)

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


def make_db_tables(db_engine: Engine) -> None:
    Base.metadata.create_all(db_engine)


def make_db_engine(db_config: DBConfig) -> Engine:
    db_url = url.URL(**db_config)
    check_and_make_directory(db_config["database"])
    db_engine = create_engine(db_url, encoding='utf8', convert_unicode=True)
    return db_engine


def initialise_db(db_config: DBConfig) -> Engine:
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
    except IntegrityError as e:
        session.rollback()
        print(str(e))
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


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


##########################################################
