##########################################################

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.engine import url
from sqlalchemy.exc import IntegrityError

##########################################################

from schema import Base

##########################################################

class CreateView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable

class DropView(DDLElement):
    def __init__(self, name):
        self.name = name

@compiler.compiles(CreateView)
def compile(element, compiler, **kw):
    return "CREATE VIEW %s AS %s" % \
        (element.name, compiler.sql_compiler.process(element.selectable))

@compiler.compiles(DropView)
def compile(element, compiler, **kw):
    return "DROP VIEW %s" % (element.name)

def view(name, metadata, selectable):
    t = table(name)

    for c in selectable.c:
        c._make_proxy(t)

    CreateView(name, selectable).execute_at('after-create', metadata)
    DropView(name).execute_at('before-drop', metadata)
    return t

##########################################################

def make_db_engine(db_config):
    db_url = url.URL(**db_config)
    db_engine = create_engine(db_url, convert_unicode=True)
    return db_engine

@contextmanager
def make_db_session(db_engine):
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

def make_db_tables(db_engine):
    Base.metadata.create_all(db_engine)

#TESTME:
def make_flat_table(db_engine):
    with make_db_session(db_engine) as session:
        flat_view = view("flat_view", Base.metadata,
            select_from(
                db_engine.join(Image, 
                    select_from(
                        db_engine.join(Collection, CollectionSubject, isouter=True)
                        .join(CollectionLocation, isouter=True)
                        .join(CollectionTopic, isouter=True)
                    )
                , isouter=True)
            )
        )
    Base.metadata.create_all(db_engine)

"""
DROP TABLE IF EXISTS flat;
DROP TABLE IF EXISTS collection_plus;

CREATE TABLE collection_plus
AS
    SELECT * FROM collection
    LEFT NATURAL JOIN collection_subject
	LEFT NATURAL JOIN collection_location
	LEFT NATURAL JOIN collection_topic
;

CREATE TABLE flat
AS
	SELECT * FROM image
	LEFT NATURAL JOIN collection_plus
;
"""

##########################################################
