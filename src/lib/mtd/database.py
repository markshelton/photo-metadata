# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import logging
from contextlib import contextmanager

##########################################################
# Third Party Imports

import pandas as pd
from envparse import env
from sqlalchemy import create_engine, text, func
from sqlalchemy.engine import url
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import scoped_session, sessionmaker, load_only

##########################################################
# Local Imports

from thickshake.mtd.schema import Base
from thickshake.utils import maybe_make_directory, setup_logging, setup_warnings
from thickshake.types import *

##########################################################
# Environmental Variables

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


def get_class_by_table_name(table_name: str) -> Any:
  for c in Base._decl_class_registry.values():
    if hasattr(c, '__tablename__') and c.__tablename__ == table_name:
      return c

def get_primary_key(table_name: str = None, model: Any = None) -> List[str]:
    assert model is not None or table_name is not None
    if model is None: model = get_class_by_table_name(table_name)
    pk_columns = inspect(model).primary_key
    return [pk.name for pk in pk_columns]

def make_db_tables(db_engine: Engine) -> None:
    Base.metadata.create_all(db_engine)


def remove_db_tables(db_engine: Engine) -> None:
    Base.metadata.drop_all(db_engine)


def make_db_engine(db_config: DBConfig=DB_CONFIG) -> Engine:
    db_url = url.URL(**db_config)
    maybe_make_directory(db_config["database"])
    db_engine = create_engine(db_url, encoding='utf8', convert_unicode=True)
    return db_engine


def initialise_db(db_config: DBConfig=DB_CONFIG, clear_flag: bool = False, **kwargs: Any) -> Engine:
    db_engine = make_db_engine(db_config)
    if clear_flag: remove_db_tables(db_engine)
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


def dump_database(db_config: DBConfig=DB_CONFIG, **kwargs: Any) -> List[Dict[str, Any]]:
    db_engine = initialise_db(db_config, **kwargs)
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
        return result


def load_column(table: str, column: str, db_config: DBConfig=DB_CONFIG) -> Series:
    db_engine = initialise_db(db_config)
    with manage_db_session(db_engine) as session:
        model = get_class_by_table_name(table)
        result = session.query(model).all()
        pk = get_primary_key(model=model)
        records = [record.__dict__ for record in result]
        df = pd.DataFrame(data=records)
        df.set_index(keys=pk, inplace=True)
        series = df[column]
        return series

#TODO
def save_column(table: str, column: str, series: Series, db_config: DBConfig=DB_CONFIG) -> None:
    db_engine = initialise_db(db_config)
    with manage_db_session(db_engine) as session:
        model = get_class_by_table_name(table)
        pass #TODO


def save_columns(output_map: Dict[str, Tuple[str, str]], data: DataFrame, db_config: DBConfig=DB_CONFIG) -> None:
    for column in data:
        if column in output_map:
            save_column(*output_map[column], series=data[column], db_config=db_config)


def inspect_database(db_config: DBConfig=DB_CONFIG) -> None:
    db_engine = initialise_db(db_config)
    with manage_db_session(db_engine) as session:
        for table_name in db_engine.table_names():
            model = get_class_by_table_name(table_name)
            num_records = session.query(func.count('*')).select_from(model).scalar()
            logger.info("Table: %s, Records: %s", table_name, num_records)


##########################################################
# Main


def main():
    load_column()


if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()

