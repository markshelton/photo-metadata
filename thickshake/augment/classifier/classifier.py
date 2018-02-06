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

from thickshake.augment.classifier.dataset import load_dataset, split_dataset, decompose

##########################################################
# Typing Configuration

from typing import List, Tuple, Dict, Any
Features = Any
Label = Any
Dataset = Any
FilePath = Any
DBConfig = Any
DataFrame = Any

##########################################################
# Constants

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


def train_classifier(dataset, class_names, classifier_file):
    # type: (Dataset, List[str], FilePath) -> None
    features, labels = decompose(dataset)
    logger.info('Training classifier on {} images'.format(len(labels)))
    model = SVC(kernel='linear', probability=True, verbose=False)
    model.fit(features, labels)
    with open(classifier_file, 'wb') as outfile:
        pickle.dump((model, class_names), outfile)
    logger.info('Saved classifier model to file "%s"' % classifier_file)


def test_classifier(dataset, classifier_file):
    # type: (Dataset, FilePath) -> None
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


def apply_constraints(df, label_key):
    # type: (DataFrame, str) -> DataFrame
    if label_key == "subject_name": 
        df = df[df["subject_type"] != "Company"] # remove companies
        df = df[~df['subject_relation'].str.contains("photo", na=False)] # remove photographers
        df = df[~df['subject_name'].str.contains("photo", na=False)] # remove photographers
    return df


#TODO:
def run_classifier(label_key, classifier_file, is_train=True, is_test=True, **kwargs):
    # type: (str, FilePath, bool, bool, **Any) -> None
    df = load_dataset(**kwargs)
    df = apply_constraints(df, label_key)
    X, y = df[df.columns.drop(label_key)], df[label_key]
    class_names = list(set(y))
    dataset_train, dataset_test = split_dataset(df, **kwargs)
    if is_train: train_classifier(dataset_train, class_names, classifier_file)
    if is_test: test_classifier(dataset_test, classifier_file)


#TODO
def run_face_classifier(**kwargs):
    pass


##########################################################


def main():
    run_classifier()


if __name__ == '__main__':
    main()


##########################################################
