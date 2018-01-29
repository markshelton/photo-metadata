# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

##########################################################
# Third Party Imports

from sqlalchemy import Column, ForeignKey, Text, Boolean, Date, Integer, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

##########################################################
# Local Imports

##########################################################
# Typing Configuration

from typing import Any

##########################################################
# Environmental Variables

##########################################################
# Logging Configuration

##########################################################
# Mix-ins & Base

Base = declarative_base() # type: Any

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
    record_label = Column(Text, unique=True)
    note_title = Column(Text)
    note_general = Column(Text)
    note_summary = Column(Text)
    series_title = Column(Text)
    series_volume = Column(Text)
    date_created = Column(Text)
    date_created_approx = Column(Text)
    date_created_parsed = Column(Date)
    physical_extent = Column(Text)
    physical_details = Column(Text)

    images = relationship("Image")
    subjects = relationship("RecordSubject", back_populates="record")
    topics = relationship("RecordTopic", back_populates="record")
    locations = relationship("RecordLocation", back_populates="record")


class Subject(Constructor, Base):
    __tablename__ = "subject"

    uuid = Column(Integer, primary_key=True, autoincrement=True)
    subject_name = Column(Text, unique=True)
    subject_type = Column(Text)  # Building | Person
    subject_dates = Column(Text)
    subject_start_date = Column(Date)
    subject_end_date = Column(Date)

    records = relationship("RecordSubject", back_populates="subject")


class Image(Constructor, Base):
    __tablename__ = "image"

    uuid = Column(Integer, primary_key=True, autoincrement=True)
    image_label = Column(Text)
    image_url = Column(Text, unique=True, nullable=False)
    image_url_raw = Column(Text)
    image_url_thumb = Column(Text)
    image_note = Column(Text, nullable=False)
    image_height = Column(Integer)
    image_width = Column(Integer)
    image_date_created = Column(Date)
    record_uuid = Column(Integer, ForeignKey("record.uuid"))

    record = relationship("Record", back_populates="images")
    locations = relationship("ImageLocation", back_populates="image")


class Location(Constructor, Base):
    __tablename__ = "location"

    uuid = Column(Integer, primary_key=True, autoincrement=True)
    location_name = Column(Text)
    location_division = Column(Text)
    building_name = Column(Text)
    street_number = Column(Text)
    street_name = Column(Text)
    street_type = Column(Text)
    suburb = Column(Text)
    state = Column(Text)
    post_code = Column(Text)
    latitude = Column(Numeric)
    longitude = Column(Numeric)
    confidence = Column(Numeric)
    location_type = Column(Text)

    images = relationship("ImageLocation", back_populates="location")
    records = relationship("RecordLocation", back_populates="location")


class Topic(Constructor, Base):
    __tablename__ = "topic"

    uuid = Column(Integer, primary_key=True)
    topic_term = Column(Text, unique=True, nullable=False)

    records = relationship("RecordTopic", back_populates="topic")


##########################################################
# Relationship Tables


class RecordSubject(Constructor, Base):
    __tablename__ = "record_subject"

    record_uuid = Column(Integer, ForeignKey("record.uuid"), primary_key=True)
    subject_uuid = Column(Integer, ForeignKey("subject.uuid"), primary_key=True)
    subject_is_main = Column(Boolean, primary_key=True)
    subject_relation = Column(Text)

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