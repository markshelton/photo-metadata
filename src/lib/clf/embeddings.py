##########################################################
# Standard Library Imports

import argparse
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

from thickshake.clf.dataset import get_image_paths, read_data, load_dataset
from thickshake.utils import logged, setup_logging, setup_warnings
from thickshake._types import Any, List, Tuple, FilePath, Tensor, Array

##########################################################
# Environmental Variables

MODEL_FILE_PATH = "/home/app/data/input/models/20170512-110547"
DATASET_FILE_PATH = "/home/app/data/output/face_recognition/metadata/face_recognition.csv"
FACES_IMAGE_DIR = "/home/app/data/output/face_recognition/images/faces"

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions

def load_images_and_labels(
        image_dir: DirPath,
        dataset_file: FilePath,
        **kwargs: Any
    ) -> Tuple(List[Tensor[Any]], List[str], List[str]):
    image_paths = thickshake.clf.dataset.get_image_paths(image_dir)
    image_paths, labels = thickshake.clf.dataset.load_dataset(dataset_file, image_paths)
    class_names = set(labels)
    images, labels = thickshake.clf.dataset.read_data(image_paths, labels, **kwargs)
    return images, labels, class_names


def load_model(model_filepath: FilePath) -> None:
    """Load frozen protobuf graph"""
    model_exp = os.path.expanduser(model_filepath)
    logging.info('Model filename: %s' % model_exp)
    with gfile.FastGFile(model_exp, 'rb') as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
        tf.import_graph_def(graph_def, name='')


def create_embeddings(
        embedding_layer,
        images: List[Tensor[Any]],
        labels: List[str],
        images_placeholder,
        phase_train_placeholder,
        sess
    ) -> Tuple(List[Any], List[str]):
    """
    Uses model to generate embeddings from :param images.
    :param embedding_layer: 
    :param images: 
    :param labels: 
    :param images_placeholder: 
    :param phase_train_placeholder: 
    :param sess: 
    :return: (tuple): image embeddings and labels
    """
    emb_array = None
    label_array = None
    try:
        i = 0
        while True:
            batch_images, batch_labels = sess.run([images, labels])
            logger.info('Processing iteration {} batch of size: {}'.format(i, len(batch_labels)))
            feed_dict = {images_placeholder: batch_images, phase_train_placeholder: False}
            emb = sess.run(embedding_layer, feed_dict=feed_dict)
            emb_array = np.concatenate([emb_array, emb]) if emb_array is not None else emb
            label_array = np.concatenate([label_array, batch_labels]) if label_array is not None else batch_labels
            i += 1
    except tf.errors.OutOfRangeError: pass
    return emb_array, label_array


def generate_embeddings(
        image_dir: DirPath,
        dataset_file: FilePath,
        model_file: FilePath,
        sess: Optional[Any]=None
    ) -> Tuple(Any, List[str]):
    if sess is None: sess = tf.Session()
    images, labels, class_names = load_images_and_labels(image_dir, dataset_file)
    load_model(model_file)
    init_op = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())
    sess.run(init_op)
    images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
    embedding_layer = tf.get_default_graph().get_tensor_by_name("embeddings:0")
    phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(coord=coord, sess=sess)
    emb_array, label_array = create_embeddings(
        embedding_layer, images, labels, images_placeholder,
        phase_train_placeholder, sess
    )
    coord.request_stop()
    coord.join(threads=threads)
    logger.info('Created {} embeddings'.format(len(emb_array)))
    sess.close()
    return emb_array, label_array


##########################################################
# Main


def main() -> None:
    emb_array, label_array = generate_embeddings(
        image_dir=FACES_IMAGE_DIR,
        dataset_file=DATASET_FILE_PATH,
        model_file=MODEL_FILE_PATH
    )
    logger.info(emb_array)
    logger.info(label_array)


if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()
