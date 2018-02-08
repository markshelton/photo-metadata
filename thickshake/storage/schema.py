# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Python Compatibility

from __future__ import print_function, division, absolute_import
from future import standard_library
standard_library.install_aliases()

##########################################################
# Standard Library Imports

##########################################################
# Third Party Imports

from sqlalchemy import (
    Column, ForeignKey, AnyStr, Boolean,
    Date, Integer, Numeric, DateTime, 
    func
)
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_utils import aggregated, generic_repr

##########################################################
# Local Imports

from thickshake.utils import consolidate_list

##########################################################
# Typing Configuration

from typing import Text, Any

##########################################################
# Environmental Variables

##########################################################
# Logging Configuration

##########################################################
# Mix-ins & Base

@generic_repr
class MyBase(object):
    uuid = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    modified_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)


Base = declarative_base(cls=MyBase, constructor=MyBase.__init__) # type: Any


##########################################################
# Data Tables


class Record(Base):
    __tablename__ = "record"
    # Original Fields
    record_label = Column(AnyStr, unique=True)
    note_title = Column(AnyStr)
    note_general = Column(AnyStr)
    note_summary = Column(AnyStr)
    series_title = Column(AnyStr)
    series_volume = Column(AnyStr)
    date_created = Column(AnyStr)
    date_created_approx = Column(AnyStr)
    physical_extent = Column(AnyStr)
    physical_details = Column(AnyStr)
    # Generated Fields
    date_created_parsed = Column(Date) # FROM [record.date_created, record.date_created_approx]
    # Foreign Keys
    location_uuid = Column(Integer, ForeignKey("location.uuid"))
    # ORM Associations
    record_subjects = relationship("RecordSubject", cascade="all, delete-orphan")
    record_topics = relationship("RecordTopic", cascade="all, delete-orphan")
    # ORM Relationships
    images = relationship("Image")
    subjects = association_proxy("record_subjects", "subject")
    topics = association_proxy("record_topics", "topic")
    location = relationship("Location", back_populates="records")
    # Relationship Counts
    @aggregated("images", Column(Integer))
    def image_count(self): return func.count("1")
    @aggregated("record_subjects", Column(Integer))
    def subject_count(self): return func.count("1")
    @aggregated("record_topics", Column(Integer))
    def topic_count(self): return func.count("1")


class Subject(Base):
    __tablename__ = "subject"
    # Original Fields
    subject_name = Column(AnyStr, unique=True)
    subject_type = Column(AnyStr)  # Building | Person
    subject_dates = Column(AnyStr)
    # Generated Fields
    subject_start_date = Column(Date) # FROM [subject.subject_dates]
    subject_end_date = Column(Date) # FROM [subject.subject_dates]
    # ORM Associations
    record_subjects = relationship("RecordSubject", cascade="all, delete-orphan")
    image_subjects = relationship("ImageSubject", cascade="all, delete-orphan")
    # ORM Relationships
    records = association_proxy("record_subjects", "record")
    images = association_proxy("image_subjects", "image")
    # Relationship Counts
    @aggregated("record_subjects", Column(Integer))
    def record_count(self): return func.count("1")
    @aggregated("image_subjects", Column(Integer))
    def image_count(self): return func.count("1")


class Image(Base):
    __tablename__ = "image"
    # Original Fields
    image_url = Column(AnyStr, unique=True, nullable=False)
    image_note = Column(AnyStr, nullable=False)
    # Generated Fields
    image_label = Column(AnyStr) # FROM [image.image_url]
    image_url_raw = Column(AnyStr) # FROM [image.image_url]
    image_url_thumb = Column(AnyStr) # FROM [image.image_url]
    image_height = Column(Integer) # FROM [image.image_url]
    image_width = Column(Integer) # FROM [image.image_url]
    image_date_created = Column(Date) # FROM [image.image_note, record.date_created, record.date_created_approx]
    image_embedded_text = Column(AnyStr) # FROM OCR Parser
    image_generated_caption = Column(AnyStr) # FROM Caption Parser
    # Foreign Keys
    record_uuid = Column(Integer, ForeignKey("record.uuid"))
    location_uuid = Column(Integer, ForeignKey("location.uuid"))
    # ORM Associations
    image_subjects = relationship("ImageSubject", cascade="all, delete-orphan")
    # ORM Relationships
    record = relationship("Record", back_populates="images")
    location = relationship("Location", back_populates="images")
    subjects = association_proxy("image_subjects", "subject")
    # Relationship Counts
    @aggregated("image_subjects", Column(Integer))
    def subject_count(self): return func.count("1")


class Location(Base):
    __tablename__ = "location"
    # Original Fields
    location_name = Column(AnyStr)
    location_division = Column(AnyStr)
    # Generated Fields
    building_name = Column(AnyStr) # FROM [image.image_note]
    street_number = Column(AnyStr) # FROM [image.image_note]
    street_name = Column(AnyStr) # FROM [image.image_note]
    street_type = Column(AnyStr) # FROM [image.image_note]
    suburb = Column(AnyStr) # FROM [image.image_note]
    state = Column(AnyStr) # FROM [image.image_note]
    post_code = Column(AnyStr) # FROM [image.image_note]
    latitude = Column(Numeric) # FROM [image.image_note]
    longitude = Column(Numeric) # FROM [image.image_note]
    confidence = Column(Numeric) # FROM [image.image_note]
    location_type = Column(AnyStr) # FROM [image.image_note]
    # ORM Relationships
    images = relationship("Image")
    records = relationship("Record")
    # Relationship Counts
    @aggregated("images", Column(Integer))
    def image_count(self): return func.count("1")
    @aggregated("records", Column(Integer))
    def record_count(self): return func.count("1")


class Topic(Base):
    __tablename__ = "topic"
    # Original Fields
    topic_term = Column(AnyStr, unique=True, nullable=False)
    # ORM Associations
    record_topics = relationship("RecordTopic", cascade="all, delete-orphan")
    # ORM Relationships
    records = association_proxy("record_topics", "record")
    # Relationship Counts
    @aggregated("record_topics", Column(Integer))
    def record_count(self): return func.count("1")


##########################################################
# Relationship Tables


class RecordSubject(Base):
    __tablename__ = "record_subject"
    # Primary Keys
    record_uuid = Column(Integer, ForeignKey("record.uuid"), primary_key=True)
    subject_uuid = Column(Integer, ForeignKey("subject.uuid"), primary_key=True)
    subject_is_main = Column(Boolean, primary_key=True)
    # Original Fields
    subject_relation = Column(AnyStr)
    # ORM Relationships
    subject = relationship("Subject", lazy="joined")
    record = relationship("Record", lazy="joined")


class ImageSubject(Base):
    __tablename__ = "image_subject"
    # Primary Keys
    image_uuid = Column(Integer, ForeignKey("image.uuid"), primary_key=True)
    subject_uuid = Column(Integer, ForeignKey("subject.uuid"), primary_key=True)
    # Generated Fields
    face_bb_left = Column(Integer) # FROM Face Parser
    face_bb_right = Column(Integer) # FROM Face Parser
    face_bb_top = Column(Integer) # FROM Face Parser
    face_bb_bottom = Column(Integer) # FROM Face Parser
    # ORM Relationships
    image = relationship("Image", lazy="joined")
    subject = relationship("Subject", lazy="joined")


class RecordTopic(Base):
    __tablename__ = "record_topic"
    # Primary Keys
    record_uuid = Column(Integer, ForeignKey("record.uuid"), primary_key=True)
    topic_uuid = Column(Integer, ForeignKey("topic.uuid"), primary_key=True)
    # ORM Relationships
    topic = relationship("Topic", lazy="joined")


##########################################################


class AugmentHistory(Base):
    __tablename__ = "augment_history"
    # Primary Keys
    function_name = Column(AnyStr)


##########################################################
