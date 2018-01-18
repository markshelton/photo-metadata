# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import logging
from contextlib import contextmanager
from envparse import env

##########################################################
# Third Party Imports

from sqlalchemy import create_engine, text
from sqlalchemy.engine import url
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.orm import scoped_session, sessionmaker

##########################################################
# Local Imports

from thickshake.mtd.schema import Base
from thickshake.utils import maybe_make_directory
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
        return result


##########################################################
