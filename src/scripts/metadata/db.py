##########################################################

from contextlib import contextmanager
from sqlalchemy import create_engine, engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import url

##########################################################

from schema import Base

##########################################################

def make_db_engine(db_config):
    db_url = url.URL(**db_config)
    db_engine = create_engine(db_url, echo=True)
    return db_engine

@contextmanager
def make_db_session(db_engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def make_db_tables(db_engine):
    Base.metadata.create_all(db_engine)

##########################################################
