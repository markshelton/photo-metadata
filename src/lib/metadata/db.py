##########################################################
# Standard Library Imports

import os
import csv
import logging
import json
import pathlib
from contextlib import contextmanager
import datetime

##########################################################
# Third Party Imports

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.engine import url
from sqlalchemy.exc import IntegrityError

##########################################################
# Local Imports

from metadata.schema import Base

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Helper Methods

def check_and_make_directory(path):
    path_dir = os.path.dirname(path)
    pathlib.Path(path_dir).mkdir(parents=True, exist_ok=True) 

def open_file(path, *args, **kwargs):
    check_and_make_directory(path)
    return open(path, *args, **kwargs)

##########################################################

def make_db_tables(db_engine):
    Base.metadata.create_all(db_engine)

def make_db_engine(db_config):
    db_url = url.URL(**db_config)
    check_and_make_directory(db_config["database"])
    db_engine = create_engine(db_url, encoding='utf8', convert_unicode=True)
    return db_engine

def initialise_db(db_config):
    db_engine = make_db_engine(db_config)
    make_db_tables(db_engine)
    return db_engine

@contextmanager
def manage_db_session(db_engine):
    Session = sessionmaker(autocommit=False, autoflush=True, bind=db_engine)
    session = scoped_session(Session)
    try:
        yield session
        session.commit()
    except IntegrityError:
        session.rollback()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def export_records_to_csv(records, output_file):
    with open_file(output_file, 'w+', encoding='utf-8') as outfile:
        outcsv = csv.writer(outfile)
        header = records[0].keys()
        outcsv.writerow(header)
        for record in records:
            record_list = [getattr(record, column) for column in header]
            outcsv.writerow(record_list)

def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def export_records_to_json(records, output_file):
    with open_file(output_file, 'w+', encoding='utf-8') as outfile:
        records_list = []
        for record in records:
            header = record.keys()
            try: 
                record_dict = {column: getattr(record, column) for column in header}
            except:
                record_dict = record
            records_list.append(record_dict)
        json.dump(records_list, outfile, indent=2, default=json_serial)

def export_records_to_log(records):
    for record in records:
        logger.info(record)

def export_records(records, output_file=None):
    if output_file:
        if output_file.endswith(".json"):
            export_records_to_json(records, output_file) 
        elif output_file.endswith(".csv"):
            export_records_to_csv(records, output_file) 
        else:
            logger.error("Output file %s is of unknown type. \
                Please specify CSV or JSON.", output_file)
    else:
        export_records_to_log(records)

##########################################################
