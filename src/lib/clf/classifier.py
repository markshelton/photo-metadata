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

OUTPUT_METADATA_FILE = env.str("OUTPUT_METADATA_FILE")
OUTPUT_IMAGE_DATA_FILE = env.str("OUTPUT_IMAGE_DATA_FILE")
OUTPUT_CLASSIFIER_MODEL_FILE = env.str("OUTPUT_CLASSIFIER_MODEL_FILE")

FLAG_CLF_BATCH_SIZE = env.int("FLAG_CLF_BATCH_SIZE")
FLAG_CLF_NUM_THREADS = env.int("FLAG_CLF_NUM_THREADS")
FLAG_CLF_NUM_EPOCHS = env.int("FLAG_CLF_NUM_EPOCHS")
FLAG_CLF_MIN_IMAGES_PER_LABEL = env.int("FLAG_CLF_MIN_IMAGES_PER_LABEL")
FLAG_CLF_SPLIT_RATIO = env.int("FLAG_CLF_SPLIT_RATIO")
FLAG_CLF_IS_TRAIN = env.bool("FLAG_CLF_IS_TRAIN")
FLAG_CLF_IS_TEST = env.bool("FLAG_CLF_IS_TEST")
FLAG_CLF_LOGGING = env.bool("FLAG_CLF_LOGGING")
FLAG_CLF_LABEL_KEY = env.str("FLAG_CLF_LABEL_KEY")
FLAG_CLF_FEATURE_LIST = env.list("FLAG_CLF_FEATURE_LIST")

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


def apply_constraints(df: pd.DataFrame) -> pd.DataFrame:
    if label_key == "subject_name": 
        df = df[df["subject_type"] != "Company"] # remove companies
        df = df[~df['subject_relation'].str.contains("photo", na=False)] # remove photographers
        df = df[~df['subject_name'].str.contains("photo", na=False)] # remove photographers
    return df

#TODO:
def run_classifier(
        metadata_file: DBConfig,
        image_data_file: FilePath,
        label_key: Optional[str],
        classifier_file: FilePath,
        is_train: bool = True,
        is_test: bool = True,
        **kwargs: Any
    ) -> None:
    df = load_dataset(metadata_file, image_data_file, **kwargs)
    df = apply_constraints(df, label_key)
    X, y = df[df.columns.drop(label_key)], df[label_key]
    class_names = set(y)
    dataset_train, dataset_test = dataset, dataset
    #dataset_train, dataset_test = split_dataset(dataset, **kwargs)
    if is_train:
        train_classifier(dataset_train, class_names, classifier_file)
    if is_test:
        test_classifier(dataset_test, classifier_file)


def main():
    run_classifier(
        metadata_file=OUTPUT_METADATA_FILE,
        image_data_file=OUTPUT_IMAGE_DATA_FILE,
        classifier_file=OUTPUT_CLASSIFIER_MODEL_FILE,
        label_key=FLAG_CLF_LABEL_KEY,
        feature_list=FLAG_CLF_FEATURE_LIST,
        batch_size=FLAG_CLF_BATCH_SIZE,
        num_threads=FLAG_CLF_NUM_THREADS,
        num_epochs=FLAG_CLF_NUM_EPOCHS,
        min_images_per_labels=FLAG_CLF_MIN_IMAGES_PER_LABEL,
        split_ratio=FLAG_CLF_SPLIT_RATIO,
        is_train=FLAG_CLF_IS_TRAIN,
        is_test=FLAG_CLF_IS_TEST,
        logging_flag=FLAG_CLF_LOGGING
    )


if __name__ == '__main__':
    setup_logging()
    setup_warnings()
    main()
