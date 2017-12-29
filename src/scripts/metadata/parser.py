##########################################################

from random import sample
from pymarc import parse_xml_to_array

##########################################################

from schema import (
    Collection, Subject, Image,
    CollectionSubject, CollectionTopic, CollectionLocation,
)
from db import (
    make_db_engine,
    make_db_session,
    make_db_tables
)

##########################################################

TAG_DELIMITER = "$"
TAG_COLLECTION_ID = "035$a"

##########################################################

INPUT_MARCXML_FILE = "/home/app/data/input/metadata/marc21.xml"
INPUT_SAMPLE_SIZE = 10
DATABASE_CONFIG = {
    'drivername': "sqlite",
    'host': None,
    'username': None,
    'password': None,
    'database': ":memory:",
} 

##########################################################

def get_subfield(record, field_key, subfield_key):
    field = record.get_fields(field_key)
    if subfield_key:
        subfield = field[subfield_key]
    else:
        subfield = field.value()
    return subfield

def get_subfield_from_tag(record, tag_key):
    if TAG_DELIMITER in tag_key: 
        field_key, subfield_key = tag_key.split(TAG_DELIMITER)
    else:
        field_key, subfield_key = tag_key, None
    subfield = get_subfield(record, field_key, subfield_key)
    return subfield

def get_collection_id(record):
    collection_id = get_subfield_from_tag(record, TAG_COLLECTION_ID)
    return collection_id

def get_subjects(record):
    subjects = []
    #TODO:
    return subjects

def get_images(record):
    images = []
    #TODO:
    return images

##########################################################

def parse_collection_data(record, session):
    db_collection = Collection() #TODO:
    session.add(db_collection)

def parse_collection_topic(image, session):
    db_ct = CollectionTopic() #TODO:
    session.add(db_ct)

def parse_collection_location(image, session):
    db_cl = CollectionLocation() #TODO:
    session.add(db_cl)

def parse_subject_data(subject, session):
    db_subject = Subject() #TODO:
    session.add(db_subject)

def parse_subject_collection(subject, collection_id, session):
    db_cs = CollectionSubject() #TODO:
    session.add(db_cs)

def parse_image(image, session):
    db_image = Image() #TODO:
    session.add(db_image)

##########################################################

def parse_images(record, session):
    images = get_images(record)
    for image in images:
        parse_image(image, session)

def parse_subject(subject, collection_id, session):
    parse_subject_data(subject, session)
    parse_subject_collection(subject, collection_id, session)

def parse_subjects(record, session):
    subjects = get_subjects(record)
    collection_id = get_collection_id(record)
    for subject in subjects:
        parse_subject(subject, collection_id, session)

def parse_collection(record, session):
    parse_collection_data(record, session)
    parse_collection_topic(record, session)
    parse_collection_location(record, session)

def parse_record(record, session):
    parse_collection(record, session)
    parse_subjects(record, session)
    parse_images(record, session)

def sample_records(records, sample_size=None):
    if sample_size:
        records_sample = records
    else:
        records_sample = sample(records, sample_size)
    return records_sample

def parse_records(records, db_engine):
    for record in records:
        with make_db_session(db_engine) as session:
            parse_record(record, session)

def parse_marcxml(input_file, sample_size=None, db_config=None):
    records = parse_xml_to_array(input_file)
    records = sample_records(records, sample_size)
    db_engine = make_db_engine(db_config)
    make_db_tables(db_engine)
    parse_records(records, db_engine)

##########################################################

parse_marcxml(INPUT_MARCXML_FILE, INPUT_SAMPLE_SIZE, DATABASE_CONFIG)

##########################################################
