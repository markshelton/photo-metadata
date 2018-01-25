##########################################################
# Standard Library Imports

##########################################################
# Third Party Imports

from envparse import env

##########################################################
# Local Imports

from thickshake.metadata.parse import load_marcxml
from thickshake.image.faces import extract_faces_from_images
from thickshake.classifier.classifier import run_classifier
from thickshake.utils import setup_warnings, setup_logging
from thickshake._types import *

##########################################################
# Environmental Variables

INPUT_METADATA_FILE = env.str("INPUT_METADATA_FILE") # type: FilePath
INPUT_IMAGE_DIR = env.str("INPUT_IMAGE_DIR")

OUTPUT_METADATA_FILE = env.str("OUTPUT_METADATA_FILE")
OUTPUT_IMAGE_DATA_FILE = env.str("OUTPUT_IMAGE_DATA_FILE")
OUTPUT_IMAGE_FACES_DIR = env.str("OUTPUT_IMAGE_FACES_DIR")
OUTPUT_CLASSIFIER_MODEL_FILE = env.str("OUTPUT_CLASSIFIER_MODEL_FILE")
OUTPUT_CLASSIFIER_RESULTS_FILE = env.str("OUTPUT_CLASSIFIER_RESULTS_FILE")

FLAG_MTD_GEOCODING = env.bool("FLAG_MTD_GEOCODING")
FLAG_MTD_DIMENSIONS = env.bool("FLAG_MTD_DIMENSIONS")
FLAG_MTD_LOGGING = env.bool("FLAG_MTD_LOGGING")
FLAG_MTD_SAMPLE = env.int("FLAG_MTD_SAMPLE")

FLAG_IMG_CLEAR_FACES = env.bool("FLAG_IMG_CLEAR_FACES")
FLAG_IMG_OVERWRITE_FACES = env.bool("FLAG_IMG_OVERWRITE_FACES")
FLAG_IMG_SAVE_FACES = env.bool("FLAG_IMG_SAVE_FACES")
FLAG_IMG_SHOW_FACES = env.bool("FLAG_IMG_SHOW_FACES")
FLAG_IMG_FACE_SIZE = env.int("FLAG_IMG_FACE_SIZE")
FLAG_IMG_LOGGING = env.bool("FLAG_IMG_LOGGING")
FLAG_IMG_LANDMARK_INDICES = env.list("FLAG_IMG_FACE_SIZE", sub_cast=int)
FLAG_IMG_SAMPLE = env.int("FLAG_IMG_SAMPLE")

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

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["drivername"] = env.str("DB_DRIVER")
DB_CONFIG["host"] = env.str("DB_HOST")
DB_CONFIG["database"] = env.str("POSTGRES_DB")
DB_CONFIG["username"] = env.str("POSTGRES_USER")
DB_CONFIG["password"] = env.str("POSTGRES_PASSWORD")

##########################################################
# Main


def main() -> None:
    load_marcxml(
        input_file=INPUT_METADATA_FILE,
        metadata_file=OUTPUT_METADATA_FILE,
        db_config=DB_CONFIG,
        geocoding=FLAG_MTD_GEOCODING,
        dimensions=FLAG_MTD_DIMENSIONS,
        logging_flag=FLAG_MTD_LOGGING,
        sample_size=FLAG_MTD_SAMPLE
    )
    extract_faces_from_images(
        input_images_dir=INPUT_IMAGE_DIR,
        output_images_dir=OUTPUT_IMAGE_FACES_DIR,
        output_face_info_file=OUTPUT_IMAGE_DATA_FILE,
        sample_size=FLAG_IMG_SAMPLE,
        show_flag=FLAG_IMG_SHOW_FACES,
        save_flag=FLAG_IMG_SAVE_FACES,
        flag_clear_faces=FLAG_IMG_CLEAR_FACES,
        logging_flag=FLAG_IMG_LOGGING,
        overwrite=FLAG_IMG_OVERWRITE_FACES,
        key_indices=FLAG_IMG_LANDMARK_INDICES,
        face_size=FLAG_IMG_FACE_SIZE,
        predictor_path=IMG_FACE_PREDICTOR_FILE,
        recognizer_path=IMG_FACE_RECOGNIZER_FILE,
        template_path=IMG_FACE_TEMPLATE_FILE
    )
    run_classifier(
        metadata_file=OUTPUT_METADATA_FILE,
        image_data_file=OUTPUT_IMAGE_DATA_FILE,
        classifier_file=OUTPUT_CLASSIFIER_MODEL_FILE,
        results_file=OUTPUT_CLASSIFIER_RESULTS_FILE,
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

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()


##########################################################