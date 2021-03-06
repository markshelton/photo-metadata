# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Python Compatibility

from __future__ import print_function, division, absolute_import
from builtins import zip, range
from future import standard_library

standard_library.install_aliases()

##########################################################
# Standard Library Imports

import json
import logging
import os
import numbers
import random

##########################################################
# Third Party Imports

import h5py
import numpy as np
import pandas as pd
import tensorflow as tf
from tqdm import tqdm
from sklearn.model_selection import train_test_split

##########################################################
# Local Imports

from thickshake.storage import Store

##########################################################
# Typing Configuration

from typing import Text, List, Tuple, Dict, Any, AnyStr
Features = Any
Label = Any
Dataset = Any
FilePath = Any
DBConfig = Any
DataFrame = Any


##########################################################
# Constants & Initialization

logger = logging.getLogger(__name__)

##########################################################
# Functions


def decompose(dataset):
    # type: (Dataset) -> Tuple[List[Features], List[Label]]
    return zip(*[(record["features"], record["label"]) for record in dataset])


def compose(features, labels):
    # type: (List[Features], List[Label]) -> Dataset
    return [{'features': fx, "label": lx} for fx, lx in zip(features, labels)]


def filter_dataset(dataset, min_images_per_label=10):
    # type: (Dataset, int) -> Dataset
    counts = {} # type: Dict[AnyStr, int]
    for record in dataset:
        label = record["label"]
        if label in counts: counts[label] = 0
        else: counts[label] += 1
    filter_dataset = {}
    for record in dataset:
        label = record["label"]
        if counts[label] > min_images_per_label:
            filter_dataset[label] = dataset[label]
    return filter_dataset


def split_dataset(dataset, split_ratio=0.8, **kwargs):
    # type: (Dataset, float, **Any) -> Tuple[Dataset, Dataset]
    X, y = decompose(dataset)
    X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=split_ratio, stratify=y)
    dataset_train = compose(X_train, y_train)
    dataset_test = compose(X_test, y_test)
    return dataset_train, dataset_test


def get_image_ids(image_data_file, sample_size=0, **kwargs):
    # type: (FilePath, int, **Any) -> List[AnyStr]
    with h5py.File(image_data_file, "r") as f:
        face_ids = list(f["embeddings"].keys())
        if sample_size != 0:
             face_ids = random.sample(face_ids, sample_size)
        image_ids = [("_").join(face_id.split("_")[0:-2]) for face_id in face_ids]
        return image_ids


#FIXME
def get_face_columns(image_data_file):
    # type: (FilePath) -> List[AnyStr]
    with h5py.File(image_data_file, "r") as f:
        embedding_size = 128 # f["embeddings"].attrs["size"]
        face_columns = ["facial_feature_%s" % val for val in range(embedding_size)]
        return face_columns

#FIXME
def get_metadata_columns(metadata_file):
    # type: (FilePath) -> List[AnyStr]
    with h5py.File(metadata_file, "r") as f:
        metadata_columns = list(f.attrs["columns"])
        return metadata_columns


def get_face_embedddings(image_id, image_data_file, **kwargs):
    # type: (AnyStr, FilePath, **Any) -> DataFrame
    with h5py.File(image_data_file, "r") as f:
        embedding_keys = f["embeddings"].keys()
        embedding_keys_subset = [key for key in embedding_keys if key.startswith(image_id)]
        embeddings = [f["embeddings"][key].value.tolist() for key in embedding_keys_subset]
        embeddings = [x for emb  in embeddings for x in emb]
        face_columns = get_face_columns(image_data_file)
        df = pd.DataFrame(data=embeddings, columns=face_columns)
        df["face_id"] = pd.Series(embedding_keys_subset, index=df.index)
        df['image_id'] = pd.Series(image_id, index=df.index)
        df.set_index("image_id", inplace=True)
        return df


def get_metadata(image_id, metadata_file, **kwargs):
    # type: (AnyStr, FilePath, **Any) -> DataFrame
    with h5py.File(metadata_file, "r") as f:
        records = f.get(image_id, None)
        metadata_columns = get_metadata_columns(metadata_file)
        metadata = [json.loads(record.value[0]) for record in records.values()] if records else None
        df = pd.DataFrame(data=metadata, columns=metadata_columns)
        df.set_index("image_id", inplace=True)
    return df


def merge_datasets(a, b):
    # type: (DataFrame, DataFrame) -> DataFrame
    dataset = pd.merge(a, b, left_index=True, right_index=True, how="outer")
    return dataset


#FIXME:
def get_records(image_id, metadata_file, image_data_file, **kwargs):
    # type: (AnyStr, DBConfig, FilePath, **Any) -> DataFrame
    faces = get_face_embedddings(image_id, image_data_file, **kwargs)
    metadata = get_metadata(image_id, metadata_file, **kwargs)
    dataset = merge_datasets(faces, metadata)
    return dataset


#FIXME
def load_dataset(metadata_file, image_data_file, **kwargs):
    # type: (DBConfig, FilePath, **Any) -> DataFrame
    image_ids = get_image_ids(image_data_file, **kwargs)
    df = pd.DataFrame()
    for image_id in tqdm(image_ids, desc="Loading Records"):
        records = get_records(image_id, metadata_file, image_data_file, **kwargs)
        df = pd.concat([df, records])
    return df


##########################################################
# Main


def main():
    df = load_dataset(
        metadata_file=OUTPUT_METADATA_FILE,
        image_data_file=OUTPUT_IMAGE_DATA_FILE,
        label_key=FLAG_CLF_LABEL_KEY,
        logging_flag=FLAG_CLF_LOGGING,
        sample_size=FLAG_CLF_SAMPLE,
    )


if __name__ == "__main__":
    main()


##########################################################
