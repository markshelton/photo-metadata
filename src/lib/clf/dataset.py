##########################################################
# Standard Library Imports

import logging
import os
import numbers

##########################################################
# Third Party Imports

import numpy as np
import tensorflow as tf
from tensorflow.python.framework import ops
from sklearn.model_selection import train_test_split
from sqlalchemy import text
import h5py

##########################################################
# Local Imports

from thickshake.mtd.database import manage_db_session, initialise_db
from thickshake.utils import setup_logging, setup_warnings
from thickshake._types import *

##########################################################
# Environmental Variables

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["database"] = "/home/app/data/output/face_recognition/metadata/face_recognition.sqlite3"
DB_CONFIG["drivername"] = "sqlite"
DB_CONFIG["host"] = None
DB_CONFIG["username"] = None
DB_CONFIG["password"] = None

IMAGE_DATA_FILE_PATH = "/home/app/data/output/face_recognition/faces.hdf5"

FEATURE_LIST = None
LABEL_KEY = "subject.subject_name"

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


def decompose(dataset: Dataset) -> Tuple[List[Features], List[Label]]:
    return zip(*[(record["features"], record["label"]) for record in dataset])


def compose(features: List[Features], labels: List[Label]) -> Dataset:
    return [{'features': fx, "label": lx} for fx, lx in zip(features, labels)]


def filter_dataset(dataset: Dataset, min_images_per_label: int = 10) -> Dataset:
    counts = {}
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


def split_dataset(dataset: Dataset, split_ratio: float = 0.8, **kwargs) -> Tuple[Dataset, Dataset]:
    X, y = decompose(dataset)
    X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=split_ratio, stratify=y)
    dataset_train = compose(X_train, y_train)
    dataset_test = compose(X_test, y_test)
    return dataset_train, dataset_test


def get_face_ids(image_data_file: DirPath) -> List[FilePath]:
    with h5py.File(image_data_file, "r") as f:
        return list(f["embeddings"].keys())


def get_image_id_from_face_id(face_id: str) -> str:
    return ("_").join(face_id.split("_")[0:-2])


def get_face_embedddings(
        image_id: str,
        image_data_file: DirPath,
        feature_list: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[List[List[Any]]]:
    if feature_list is not None and "facial_features" not in feature_list: return None
    with h5py.File(image_data_file, "r") as f:
        embedding_keys = f["embeddings"].keys()
        embeddings = [f["embeddings"][key].value.tolist() for key in embedding_keys if key.startswith(image_id)]
        embeddings = [x for emb  in embeddings for x in emb]
        return embeddings


def check_table(table: str, columns: List[str]) -> bool:
    if len(columns) == 1: return True
    for column in columns:
        if ("%s." % table) in column:
            return True
    return False


def get_metadata(
        image_id: str,
        metadata_file: DBConfig,
        label_key: str,
        feature_list: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[List[List[Any]]]:
    db_engine = initialise_db(metadata_file)
    with manage_db_session(db_engine) as session:
        if feature_list is None: 
            columns = [label_key]
            sql_text = "SELECT *\n"
        else: 
            columns = [*feature_list, label_key]
            sql_text = "SELECT %s\n" % ",".join(columns)
        sql_text += "FROM image\n"
        if check_table("Collection", columns):
            sql_text += "LEFT NATURAL OUTER JOIN collection\n"
        if check_table("CollectionSubject", columns):
            sql_text += "LEFT NATURAL OUTER JOIN collection_subject\n"
        if check_table("CollectionLocation", columns):
            sql_text += "LEFT NATURAL OUTER JOIN collection_location\n"
        if check_table("CollectionTopic", columns):
            sql_text += "LEFT NATURAL OUTER JOIN collection_topic\n"
        if check_table("Subject", columns):
            sql_text += "LEFT NATURAL OUTER JOIN subject\n"
        sql_text += "WHERE image.image_id = '%s';" % (image_id)
        result = session.execute(text(sql_text)).fetchall()
        result = [dict(record) for record in result]
    if result:
        features = [[v for k,v in record.items() if k != label_key] for record in result]
        labels = [record[label_key.split(".")[-1]] for record in result]
    else: return None
    return features, labels


def merge_features(a: List[Features], b: List[Features]) -> List[Features]:
    merge = [[i for j in record for i in j] for record in zip(a, b)]
    return merge


def get_features_and_labels(
        image_id: str,
        metadata_file: DBConfig,
        image_data_file: FilePath,
        label_key: str,
        **kwargs
    ) -> Optional[Tuple[Features, str]]:
    features_face = get_face_embedddings(image_id, image_data_file, **kwargs)
    metadata = get_metadata(image_id, metadata_file, label_key, **kwargs)
    if metadata is None: return None
    else: features_metadata, labels = metadata
    features = merge_features(features_face, features_metadata)
    return features, labels


def load_dataset(metadata_file: DBConfig, image_data_file: FilePath, label_key: str, **kwargs) -> Tuple[Dataset, List[str]]:
    face_ids = get_face_ids(image_data_file)
    dataset = []
    for face_id in face_ids:
        image_id = get_image_id_from_face_id(face_id)
        image_info = get_features_and_labels(image_id, metadata_file, image_data_file, label_key, **kwargs)
        if image_info is None: continue
        else: features, labels = image_info
        for label in labels:
            dataset.append({"label": label, "features": features[0]})
    return dataset


##########################################################
# Main

def main():
    dataset = load_dataset(
        metadata_file=DB_CONFIG,
        image_data_file=IMAGE_DATA_FILE_PATH,
        label_key=LABEL_KEY
    )
    print(dataset)

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()