##########################################################
# Standard Library Imports

##########################################################
# Third Party Imports

from sqlalchemy import (
    Column, ForeignKey,
    String, Boolean, Date, Integer,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

##########################################################
# Local Imports

from _types import Any

##########################################################

Base = declarative_base() # type: Any

##########################################################


class Collection(Base):
    __tablename__ = "collection"

    collection_id = Column(String(30), primary_key=True)
    note_title = Column(String(255))
    note_general = Column(String(255))
    note_summary = Column(String(255))
    series_title = Column(String(255))
    series_volume = Column(String(30))
    date_created = Column(Date)
    physical_extent = Column(String(255))
    physical_details = Column(String(255))

    images = relationship("Image")
    subjects = relationship("CollectionSubject", back_populates="collection")
    topics = relationship("CollectionTopic", back_populates="collection")
    locations = relationship("CollectionLocation", back_populates="collection")

    def __repr__(self):
        return "<Collection(id='%s', title='%s')>" % \
            (self.collection_id, self.note_title)


class Subject(Base):
    __tablename__ = "subject"

    subject_name = Column(String(255), primary_key=True)
    subject_type = Column(String(30))  # Building | Person
    subject_start_date = Column(Date)
    subject_end_date = Column(Date)

    collections = relationship("CollectionSubject", back_populates="subject")

    def __repr__(self):
        return "<Subject(name='%s', type='%s', dates='%s'-'%s')>" % \
            (self.subject_name,
             self.subject_type,
             self.subject_start_date,
             self.subject_end_date)


class Image(Base):
    __tablename__ = "image"

    image_id = Column(String(30), primary_key=True)
    image_url_main = Column(String(255))
    image_url_raw = Column(String(255))
    image_url_thumb = Column(String(255))
    image_note = Column(String(255), nullable=False)
    image_height = Column(Integer)
    image_width = Column(Integer)
    image_latitude = Column(String(30))
    image_longitude = Column(String(30))
    image_date_created = Column(Date)
    collection_id = Column(String(30), ForeignKey("collection.collection_id"))

    collection = relationship("Collection", back_populates="images")

    def __repr__(self):
        return "<Image(name='%s', note='%s', url='%s', collection='%s')>" % \
            (self.image_id, self.image_note, self.image_url, self.collection)


class CollectionSubject(Base):
    __tablename__ = "collection_subject"

    collection_id = Column(
        String(30),
        ForeignKey("collection.collection_id"),
        primary_key=True)
    subject_name = Column(
        String(255),
        ForeignKey("subject.subject_name"),
        primary_key=True)
    subject_is_main = Column(Boolean, primary_key=True)
    subject_relation = Column(String(255))

    collection = relationship("Collection", back_populates="subjects")
    subject = relationship("Subject", back_populates="collections")


class CollectionTopic(Base):
    __tablename__ = "collection_topic"

    collection_id = Column(
        String(30),
        ForeignKey("collection.collection_id"),
        primary_key=True)
    topic = Column(String(255), primary_key=True)

    collection = relationship("Collection", back_populates="topics")


class CollectionLocation(Base):
    __tablename__ = "collection_location"

    collection_id = Column(
        String(30),
        ForeignKey("collection.collection_id"),
        primary_key=True)
    location = Column(String(255), primary_key=True)

    collection = relationship("Collection", back_populates="locations")

##########################################################
