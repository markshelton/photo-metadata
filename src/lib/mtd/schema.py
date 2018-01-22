# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

##########################################################
# Third Party Imports

from sqlalchemy import Column, ForeignKey, String, Boolean, Date, Integer, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

##########################################################
# Local Imports

from thickshake.types import Any

##########################################################

Base = declarative_base() # type: Any

##########################################################
# Mix-ins

class Constructor(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

##########################################################
# Data Tables

class Record(Constructor, Base):
    __tablename__ = "record"

    uuid = Column(Integer, primary_key=True, autoincrement=True)
    record_label = Column(String(30))
    note_title = Column(String(255))
    note_general = Column(String(255))
    note_summary = Column(String(255))
    series_title = Column(String(255))
    series_volume = Column(String(30))
    date_created = Column(String(255))
    date_created_approx = Column(String(255))
    date_created_parsed = Column(Date)
    physical_extent = Column(String(255))
    physical_details = Column(String(255))

    images = relationship("Image")
    subjects = relationship("RecordSubject", back_populates="record")
    topics = relationship("RecordTopic", back_populates="record")
    locations = relationship("RecordLocation", back_populates="record")


class Subject(Constructor, Base):
    __tablename__ = "subject"

    uuid = Column(Integer, primary_key=True, autoincrement=True)
    subject_name = Column(String(255))
    subject_type = Column(String(30))  # Building | Person
    subject_dates = Column(String(255))
    subject_start_date = Column(Date)
    subject_end_date = Column(Date)

    records = relationship("RecordSubject", back_populates="subject")


class Image(Constructor, Base):
    __tablename__ = "image"

    uuid = Column(Integer, primary_key=True, autoincrement=True)
    image_label = Column(String(30))
    image_url = Column(String(255), nullable=False)
    image_url_raw = Column(String(255))
    image_url_thumb = Column(String(255))
    image_note = Column(String(255), nullable=False)
    image_height = Column(Integer)
    image_width = Column(Integer)
    image_latitude = Column(String(30))
    image_longitude = Column(String(30))
    image_address = Column(String(255))
    image_date_created = Column(Date)
    record_uuid = Column(Integer, ForeignKey("record.uuid"))

    record = relationship("Record", back_populates="images")
    locations = relationship("ImageLocation", back_populates="image")


class Location(Constructor, Base):
    __tablename__ = "location"

    uuid = Column(Integer, primary_key=True, autoincrement=True)
    location_name = Column(String(255))
    location_division = Column(String(255))
    building_name = Column(String(255))
    street_number = Column(String(30))
    street_name = Column(String(255))
    street_type = Column(String(30))
    suburb = Column(String(255))
    state = Column(String(30))
    post_code = Column(String(30))
    latitude = Column(Numeric)
    longitude = Column(Numeric)
    confidence = Column(Numeric)
    location_type = Column(String(30))

    images = relationship("ImageLocation", back_populates="location")
    records = relationship("RecordLocation", back_populates="location")


class Topic(Constructor, Base):
    __tablename__ = "topic"

    uuid = Column(Integer, primary_key=True)
    topic_term = Column(String(255))

    records = relationship("RecordTopic", back_populates="topic")


##########################################################
# Relationship Tables


class RecordSubject(Constructor, Base):
    __tablename__ = "record_subject"

    record_uuid = Column(Integer, ForeignKey("record.uuid"), primary_key=True)
    subject_uuid = Column(Integer, ForeignKey("subject.uuid"), primary_key=True)
    subject_is_main = Column(Boolean, primary_key=True)
    subject_relation = Column(String(255))

    record = relationship("Record", back_populates="subjects")
    subject = relationship("Subject", back_populates="records")


class RecordTopic(Constructor, Base):
    __tablename__ = "record_topic"

    record_uuid = Column(Integer, ForeignKey("record.uuid"), primary_key=True)
    topic_uuid = Column(Integer, ForeignKey("topic.uuid"), primary_key=True)

    record = relationship("Record", back_populates="topics")
    topic = relationship("Topic", back_populates="records")


class RecordLocation(Constructor, Base):
    __tablename__ = "record_location"

    record_uuid = Column(Integer, ForeignKey("record.uuid"), primary_key=True)
    location_uuid = Column(Integer, ForeignKey("location.uuid"), primary_key=True)

    record = relationship("Record", back_populates="locations")
    location = relationship("Location", back_populates="records")


class ImageLocation(Constructor, Base):
    __tablename__ = "image_location"

    image_uuid = Column(Integer, ForeignKey("image.uuid"), primary_key=True)
    location_uuid = Column(Integer, ForeignKey("location.uuid"), primary_key=True)

    image = relationship("Image", back_populates="locations")
    location = relationship("Location", back_populates="images")


##########################################################