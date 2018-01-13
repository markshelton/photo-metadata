##########################################################
# Standard Library Imports

import logging
import os
import pickle
import sys

##########################################################
# Third Party Imports

import numpy as np
import tensorflow as tf
from sklearn.svm import SVC

##########################################################
# Local Imports

from thickshake.utils import logged, setup_logging, setup_warnings
from thickshake.clf.dataset import load_dataset, split_dataset, decompose
from thickshake._types import *

##########################################################
# Environmental Variables

IMAGE_DATA_FILE_PATH = "/home/app/data/output/face_recognition/faces.hdf5"
CLASSIFIER_FILE_PATH = "/home/app/data/output/face_recognition/models/face_recognition.pkl" # type = FilePath

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["database"] = "/home/app/data/output/face_recognition/metadata/face_recognition.sqlite3"
DB_CONFIG["drivername"] = "sqlite"
DB_CONFIG["host"] = None
DB_CONFIG["username"] = None
DB_CONFIG["password"] = None


FEATURE_LIST = None # type = Optional[List[str]]
LABEL_KEY = "subject.subject_name"

FLAG_BATCH_SIZE = 1 # type = int
FLAG_NUM_THREADS = 4 # type = int
FLAG_NUM_EPOCHS = 5 # type = int
FLAG_MIN_IMAGES_PER_LABEL = 3 # type = int
FLAG_SPLIT_RATIO = 2 # type = int
FLAG_IS_TRAIN = True # type = bool
FLAG_IS_TEST = True # type = bool

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


def train_classifier(dataset: Dataset, class_names: List[str], classifier_file: FilePath) -> None:
    features, labels = decompose(dataset)
    logger.info('Training classifier on {} images'.format(len(labels)))
    model = SVC(kernel='linear', probability=True, verbose=False)
    model.fit(features, labels)
    with open(classifier_file, 'wb') as outfile:
        pickle.dump((model, class_names), outfile)
    logger.info('Saved classifier model to file "%s"' % classifier_file)


def test_classifier(dataset: Dataset, classifier_file: FilePath) -> None:
    features, labels = decompose(dataset)
    logger.info('Evaluating classifier on {} images'.format(len(labels)))
    if not os.path.exists(classifier_file):
        raise ValueError('Pickled classifier not found, have you trained first?')
    with open(classifier_file, 'rb') as f:
        model, class_names = pickle.load(f)
        predictions = model.predict_proba(features, )
        best_class_indices = np.argmax(predictions, axis=1)
        best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]
        for i in range(len(best_class_indices)):
            logger.info('%4d  %s: %.3f' % (i, class_names[best_class_indices[i]], best_class_probabilities[i]))
        accuracy = np.mean(np.equal(best_class_indices, labels))
        logger.info('Accuracy: %.3f' % accuracy)

#TODO:
def run_classifier(metadata_file: DBConfig, image_data_file: FilePath, classifier_file: FilePath, label_key: Optional[str], is_train: bool = True, is_test: bool = True, **kwargs: Any) -> None:
    dataset = load_dataset(metadata_file, image_data_file, label_key, **kwargs)
    class_names = set([record["label"] for record in dataset])
    dataset_train, dataset_test = dataset, dataset
    #dataset_train, dataset_test = split_dataset(dataset, **kwargs)
    if is_train:
        train_classifier(dataset_train, class_names, classifier_file)
    if is_test:
        test_classifier(dataset_test, classifier_file)


def main():
    run_classifier(
        metadata_file=DB_CONFIG,
        image_data_file=IMAGE_DATA_FILE_PATH,
        classifier_file=CLASSIFIER_FILE_PATH,
        label_key=LABEL_KEY,
        feature_list=FEATURE_LIST,
        batch_size=FLAG_BATCH_SIZE,
        num_threads=FLAG_NUM_THREADS,
        num_epochs=FLAG_NUM_EPOCHS,
        min_images_per_labels=FLAG_MIN_IMAGES_PER_LABEL,
        split_ratio=FLAG_SPLIT_RATIO,
        is_train=FLAG_IS_TRAIN,
        is_test=FLAG_IS_TEST
    )


if __name__ == '__main__':
    setup_logging()
    setup_warnings()
    main()
