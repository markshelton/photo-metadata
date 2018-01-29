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
from sqlalchemy import create_engine, text, func, inspect
from sqlalchemy.engine import url
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.orm import scoped_session, sessionmaker, load_only

##########################################################
# Local Imports

from thickshake.storage.schema import Base
from thickshake.helpers import maybe_make_directory

##########################################################
# Typing Configuration

from mypy_extensions import TypedDict
from typing import (
    Optional, Union, List, Dict,
    Any, Tuple, Iterator, Iterable,
)

DBConfig = TypedDict("DBConfig", {
    'database': str, 'drivername': str, 'host': Optional[str],
    'username': Optional[str], 'password': Optional[str],
    }, total=False
)
DBEngine = Any
DBSession = Any
DBObject = Any
Series = Iterable[Any]
DataFrame = Dict[str, Series]

##########################################################
# Constants

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["drivername"] = env.str("DB_DRIVER", default="postgres")
DB_CONFIG["host"] = env.str("DB_HOST", default="thickshake_db")
DB_CONFIG["database"] = env.str("POSTGRES_DB", default="thickshake")
DB_CONFIG["username"] = env.str("POSTGRES_USER", default="postgres")
DB_CONFIG["password"] = env.str("POSTGRES_PASSWORD", default="thickshake")

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Functions

class Database:
    engine = None
    session = None
    base = None
    
    def __init__(self, db_config: DBConfig = DB_CONFIG, force: bool=False, **kwargs: Any) -> None:
        if self.engine is None:
            self.engine = self.make_engine(db_config)
            self.base = Base
            if force: self.remove_db_tables()
            self.make_db_tables()
            

    def make_engine(self, db_config: DBConfig) -> DBEngine:
        db_url = url.URL(**db_config)
        if db_config["database"] is None: return None
        maybe_make_directory(db_config["database"])
        db_engine = create_engine(db_url, encoding='utf8', convert_unicode=True)
        return db_engine


    def make_db_tables(self) -> None:
        self.base.metadata.create_all(self.engine)


    def remove_db_tables(self) -> None:
        self.base.metadata.drop_all(self.engine)


    @contextmanager
    def manage_db_session(self, dry_run: bool = False, **kwargs: Any) -> Iterator[DBSession]:
        Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = scoped_session(Session)
        try:
            yield self.session
            if not dry_run: self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            raise e
        except BaseException:
            self.session.rollback()
            raise
        finally:
            self.session.close()


    def merge_record(self, table_name: str, parsed_record: Dict[str, Any], **kwargs: Any) -> DBObject:
        model = self.get_class_by_table_name(table_name)
        db_object = model(**parsed_record)
        try: 
            self.session.add(db_object)
            self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            unique_columns = self.get_unique_columns(table_name)
            q = self.session.query(model)
            for col in unique_columns:
                try: q = q.filter(getattr(model, col).like(getattr(db_object, col)))
                except: q = q.filter(getattr(model, col) == getattr(db_object, col))
            matched_obj = q.first()
            db_object = matched_obj
        return db_object


    def get_class_by_table_name(self, table_name: str) -> Any:
        for c in self.base._decl_class_registry.values():
            if hasattr(c, '__tablename__') and c.__tablename__ == table_name:
                return c


    def get_primary_keys(self, table_name: str = None, model: Any = None) -> List[str]:
        assert model is not None or table_name is not None
        if model is None and table_name is not None: 
            model = self.get_class_by_table_name(table_name)
        pk_columns = inspect(model).primary_key
        return [pk.name for pk in pk_columns]


    def get_unique_columns(self, table_name: str) -> List[str]:
        insp = inspect(self.engine)
        unique_constraints = insp.get_unique_constraints(table_name)
        return [unique_constraint["column_names"][0] for unique_constraint in unique_constraints]

    def execute_text_query(self, sql_text: str) -> List[Dict[str, Any]]:
        with self.manage_db_session() as session:
            result = session.execute(text(sql_text)).fetchall()
            result = [dict(record) for record in result]
            return result


    #Convert to sqlalchemy ORM
    def dump(self) -> List[Dict[str, Any]]:
        sql_text =  "SELECT *\n"
        sql_text += "FROM image\n"
        sql_text += "NATURAL LEFT JOIN image_location\n"
        sql_text += "NATURAL LEFT JOIN location\n"
        sql_text += "NATURAL LEFT JOIN record\n"
        sql_text += "NATURAL LEFT JOIN record_subject\n"
        sql_text += "NATURAL LEFT JOIN subject\n"
        sql_text += "NATURAL LEFT JOIN record_location\n"
        sql_text += "NATURAL LEFT JOIN record_topic\n"
        sql_text += "NATURAL LEFT JOIN topic\n"
        sql_text += ";"
        result = self.execute_text_query(sql_text)
        return result


    def load_column(self, table: str, column: str) -> Series:
        with self.manage_db_session() as session:
            model = self.get_class_by_table_name(table)
            result = session.query(model).all()
            pk = self.get_primary_keys(model=model)
            records = [record.__dict__ for record in result]
            df = pd.DataFrame(data=records)
            df.set_index(keys=pk, inplace=True)
            series = df[column]
            return series


    #TODO
    def save_column(self, table: str, column: str, series: Series) -> None:
        with self.manage_db_session() as session:
            model = get_class_by_table_name(table)
            pass #TODO


    def save_columns(self, output_map: Dict[str, Tuple[str, str]], data: DataFrame) -> None:
        for column in data:
            if column in output_map:
                pass #TODO


    def inspect_database(self) -> None:
        with self.manage_db_session() as session:
            for table_name in self.engine.table_names():
                model = self.get_class_by_table_name(table_name)
                num_records = session.query(func.count('*')).select_from(model).scalar()
                logger.info("Table: %s, Records: %s", table_name, num_records)


##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()


##########################################################
