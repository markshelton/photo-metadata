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

from metadata.schema import (
    Base, Image, Collection, 
    CollectionLocation, CollectionSubject, CollectionTopic,
)

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
    make_db_tables(db_engine)
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


def get_flat_view(session):
    collection_plus = (
        session.query(
            Collection, CollectionSubject, CollectionLocation, CollectionTopic
        )
        .join(CollectionSubject, isouter=True)
        .join(CollectionLocation, isouter=True)
        .join(CollectionTopic, isouter=True)
        .subquery()
    )
    flat_view = session.query(
        session.query(Image, collection_plus)
        .join(collection_plus, isouter=True)
        .subquery()
    )
    return flat_view

def prepare_query_for_export(query):
    columns = query.column_descriptions
    header = [column["name"] for column in columns]
    records = query.all()
    return records, columns, header

def export_query_to_csv(query, output_file):
    records, columns, header = prepare_query_for_export(query)
    with open_file(output_file, 'w+', encoding='utf-8') as outfile:
        outcsv = csv.writer(outfile)
        outcsv.writerow(header)
        for record in records:
            record_list = [getattr(record, column["name"]) for column in columns]
            outcsv.writerow(record_list)

def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def export_query_to_json(query, output_file):
    records, columns, _ = prepare_query_for_export(query)
    with open_file(output_file, 'w+', encoding='utf-8') as outfile:
        records_list = []
        for record in records:
            record_dict = {column["name"]:getattr(record, column["name"]) for column in columns}
            records_list.append(record_dict)
        json.dump(records_list, outfile, indent=2,default=json_serial)

def export_query_to_log(query):
    records, _, _ = prepare_query_for_export(query)
    for record in records:
        logger.info(record)

def export_query(query, output_file=None):
    if output_file:
        if output_file.endswith(".json"):
            export_query_to_json(query, output_file) 
        elif output_file.endswith(".csv"):
            export_query_to_csv(query, output_file) 
        else:
            logger.error("Output file %s is of unknown type. \
                Please specify CSV or JSON.", output_file)
    else:
        export_query_to_log(query)

def export_flat_view(db_engine, output_file):
    with manage_db_session(db_engine) as session:
        query = get_flat_view(session)
        export_query(query, output_file)

##########################################################
