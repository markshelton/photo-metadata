##########################################################
# Standard Library Imports

import logging
import os
import pickle
import sys
import time

##########################################################
# Third Party Imports

import numpy as np
import tensorflow as tf
from sklearn.svm import SVC
from tensorflow.python.platform import gfile

##########################################################
# Local Imports

from thickshake.utils import logged, setup_logging, setup_warnings
from thickshake._types import Dict, List, Optional, Any, FilePath, DirPath

##########################################################
# Environmental Variables

MODEL_FILE_PATH = "/home/app/data/input/models/20170512-110547" # type = FilePath
DATASET_FILE_PATH = "/home/app/data/output/face_recognition/metadata/face_recognition.csv" # type = FilePath
FACES_IMAGE_DIR = "/home/app/data/output/face_recognition/images/faces" # type = DirPath
CLASSIFIER_OUTPUT_PATH = "/home/app/data/output/face_recognition/models/face_recognition.pkl" # type = FilePath
FLAG_BATCH_SIZE = 1 # type = int
FLAG_NUM_THREADS = 4 # type = int
FLAG_NUM_EPOCHS = 5 # type = int
FLAG_MIN_IMAGES_PER_LABEL = 3 # type = int
FLAG_SPLIT_RATIO = 2 # type = int
FLAG_IS_TRAIN = True # type = bool

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


def run_classifier(
        input_directory: DirPath,
        model_path: FilePath,
        classifier_path: FilePath,
        batch_size: int = 1,
        num_threads: int = 4,
        num_epochs: int = 5,
        min_images_per_labels: int = 3,
        split_ratio: int = 2,
        is_train: bool = True
    ) -> None:
    """
    Loads images from :param input_dir, creates embeddings using a model defined at :param model_path, and trains
     a classifier outputted to :param output_path
     
    :param input_directory: Path to directory containing pre-processed images
    :param model_path: Path to protobuf graph file for facenet model
    :param classifier_output_path: Path to write pickled classifier
    :param batch_size: Batch size to create embeddings
    :param num_threads: Number of threads to utilize for queuing
    :param num_epochs: Number of epochs for each image
    :param min_images_per_labels: Minimum number of images per class
    :param split_ratio: Ratio to split train/test dataset
    :param is_train: bool denoting if training or evaluate
    """

    start_time = time.time()
    with tf.Session() as sess:
        emb_array, label_array =  generate_embeddings(
            image_dir=FACES_IMAGE_DIR,
            dataset_file=DATASET_FILE_PATH,
            model_file=MODEL_FILE_PATH,
            sess=sess
        )
        if is_train:
            train_and_save_classifier(emb_array, label_array, class_names, classifier_path)
        else:
            evaluate_classifier(emb_array, label_array, classifier_path)
        logger.info('Completed in {} seconds'.format(time.time() - start_time))


def _get_test_and_train_set(input_dir, min_num_images_per_label, split_ratio=0.7):
    """
    Load train and test dataset. Classes with < :param min_num_images_per_label will be filtered out.
    :param input_dir: 
    :param min_num_images_per_label: 
    :param split_ratio: 
    :return: 
    """
    dataset = get_dataset(input_dir)
    dataset = filter_dataset(dataset, min_images_per_label=min_num_images_per_label)
    train_set, test_set = split_dataset(dataset, split_ratio=split_ratio)

    return train_set, test_set


def train_and_save_classifier(emb_array, label_array, class_names, classifier_filename_exp):
    logger.info('Training Classifier')
    model = SVC(kernel='linear', probability=True, verbose=False)
    model.fit(emb_array, label_array)
    with open(classifier_filename_exp, 'wb') as outfile:
        pickle.dump((model, class_names), outfile)
    logging.info('Saved classifier model to file "%s"' % classifier_filename_exp)


def evaluate_classifier(emb_array, label_array, classifier_filename):
    logger.info('Evaluating classifier on {} images'.format(len(emb_array)))
    if not os.path.exists(classifier_filename):
        raise ValueError('Pickled classifier not found, have you trained first?')
    with open(classifier_filename, 'rb') as f:
        model, class_names = pickle.load(f)
        predictions = model.predict_proba(emb_array, )
        best_class_indices = np.argmax(predictions, axis=1)
        best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]
        for i in range(len(best_class_indices)):
            print('%4d  %s: %.3f' % (i, class_names[best_class_indices[i]], best_class_probabilities[i]))
        accuracy = np.mean(np.equal(best_class_indices, label_array))
        print('Accuracy: %.3f' % accuracy)


def main():
    run_classifier(
        input_directory=FACES_IMAGE_DIR,
        model_path=MODEL_FILE_PATH,
        classifier_output_path=CLASSIFIER_OUTPUT_PATH,
        batch_size=FLAG_BATCH_SIZE,
        num_threads=FLAG_NUM_THREADS,
        num_epochs=FLAG_NUM_EPOCHS,
        min_images_per_labels=FLAG_MIN_IMAGES_PER_LABEL,
        split_ratio=FLAG_SPLIT_RATIO,
        is_train=FLAG_IS_TRAIN
    )

if __name__ == '__main__':
    setup_logging()
    setup_warnings()
    main()
