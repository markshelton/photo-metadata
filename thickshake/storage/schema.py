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
    # Primary Key
    uuid = Column(Integer, primary_key=True, autoincrement=True)
    # Original Fields
    record_label = Column(Text, unique=True)
    note_title = Column(Text)
    note_general = Column(Text)
    note_summary = Column(Text)
    series_title = Column(Text)
    series_volume = Column(Text)
    date_created = Column(Text)
    date_created_approx = Column(Text)
    physical_extent = Column(Text)
    physical_details = Column(Text)
    # Generated Fields
    date_created_parsed = Column(Date) # FROM [record.date_created, record.date_created_approx]
    # ORM Relationships
    images = relationship("Image")
    subjects = relationship("RecordSubject", back_populates="record")
    topics = relationship("RecordTopic", back_populates="record")
    locations = relationship("RecordLocation", back_populates="record")


class Subject(Constructor, Base):
    __tablename__ = "subject"
    # Primary Key
    uuid = Column(Integer, primary_key=True, autoincrement=True)
    # Original Fields
    subject_name = Column(Text, unique=True)
    subject_type = Column(Text)  # Building | Person
    subject_dates = Column(Text)
    # Generated Fields
    subject_start_date = Column(Date) # FROM [subject.subject_dates]
    subject_end_date = Column(Date) # FROM [subject.subject_dates]
    # ORM Relationships
    records = relationship("RecordSubject", back_populates="subject")


class Image(Constructor, Base):
    __tablename__ = "image"
    # Primary Key
    uuid = Column(Integer, primary_key=True, autoincrement=True)
    # Original Fields
    image_url = Column(Text, unique=True, nullable=False)
    image_note = Column(Text, nullable=False)
    # Generated Fields
    image_label = Column(Text) # FROM [image.image_url]
    image_url_raw = Column(Text) # FROM [image.image_url]
    image_url_thumb = Column(Text) # FROM [image.image_url]
    image_height = Column(Integer) # FROM [image.image_url]
    image_width = Column(Integer) # FROM [image.image_url]
    image_date_created = Column(Date) # FROM [image.image_note, record.date_created, record.date_created_approx]
    # Foreign Keys
    record_uuid = Column(Integer, ForeignKey("record.uuid"))
    # ORM Relationships
    record = relationship("Record", back_populates="images")
    locations = relationship("ImageLocation", back_populates="image")


class Location(Constructor, Base):
    __tablename__ = "location"
    # Primary Key
    uuid = Column(Integer, primary_key=True, autoincrement=True)
    # Original Fields
    location_name = Column(Text)
    location_division = Column(Text)
    # Generated Fields
    building_name = Column(Text) # FROM [image.image_note]
    street_number = Column(Text) # FROM [image.image_note]
    street_name = Column(Text) # FROM [image.image_note]
    street_type = Column(Text) # FROM [image.image_note]
    suburb = Column(Text) # FROM [image.image_note]
    state = Column(Text) # FROM [image.image_note]
    post_code = Column(Text) # FROM [image.image_note]
    latitude = Column(Numeric) # FROM [image.image_note]
    longitude = Column(Numeric) # FROM [image.image_note]
    confidence = Column(Numeric) # FROM [image.image_note]
    location_type = Column(Text) # FROM [image.image_note]
    # ORM Relationships
    images = relationship("ImageLocation", back_populates="location")
    records = relationship("RecordLocation", back_populates="location")


class Topic(Constructor, Base):
    __tablename__ = "topic"
    # Primary Key
    uuid = Column(Integer, primary_key=True)
    # Original Fields
    topic_term = Column(Text, unique=True, nullable=False)
    # ORM Relationships
    records = relationship("RecordTopic", back_populates="topic")


##########################################################
# Relationship Tables


class RecordSubject(Constructor, Base):
    __tablename__ = "record_subject"
    # Primary Keys
    record_uuid = Column(Integer, ForeignKey("record.uuid"), primary_key=True)
    subject_uuid = Column(Integer, ForeignKey("subject.uuid"), primary_key=True)
    subject_is_main = Column(Boolean, primary_key=True)
    # Original Fields
    subject_relation = Column(Text)
    # ORM Relationships
    record = relationship("Record", back_populates="subjects")
    subject = relationship("Subject", back_populates="records")


class RecordTopic(Constructor, Base):
    __tablename__ = "record_topic"
    # Primary Keys
    record_uuid = Column(Integer, ForeignKey("record.uuid"), primary_key=True)
    topic_uuid = Column(Integer, ForeignKey("topic.uuid"), primary_key=True)
    # ORM Relationships
    record = relationship("Record", back_populates="topics")
    topic = relationship("Topic", back_populates="records")


class RecordLocation(Constructor, Base):
    __tablename__ = "record_location"
    # Primary Keys
    record_uuid = Column(Integer, ForeignKey("record.uuid"), primary_key=True)
    location_uuid = Column(Integer, ForeignKey("location.uuid"), primary_key=True)
    # ORM Relationships
    record = relationship("Record", back_populates="locations")
    location = relationship("Location", back_populates="records")


class ImageLocation(Constructor, Base):
    __tablename__ = "image_location"
    # Primary Keys
    image_uuid = Column(Integer, ForeignKey("image.uuid"), primary_key=True)
    location_uuid = Column(Integer, ForeignKey("location.uuid"), primary_key=True)
    # ORM Relationships
    image = relationship("Image", back_populates="locations")
    location = relationship("Location", back_populates="images")


##########################################################