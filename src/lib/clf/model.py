##########################################################
# Standard Library Imports

import logging
import requests
import zipfile
import os

##########################################################
# Third Party Imports

##########################################################
# Local Imports

from thickshake.utils import logged, setup_logging, setup_warnings
from thickshake._types import Dict, List, Optional, Any, FilePath, DirPath

##########################################################
# Environmental Variables

OUTPUT_MODEL_DIR = "/home/app/data/input/models/" # type: DirPath
SELECTED_MODEL = '20170512-110547' # type: str
SOURCE_BASE_URL = "https://drive.google.com/uc?export=download" # type: FilePath
MODEL_DICT = {
    'lfw-subset':      '1B5BQUZuJO-paxdN8UclxeHAR1WnR_Tzi', 
    '20170131-234652': '0B5MzpY9kBtDVSGM0RmVET2EwVEk',
    '20170216-091149': '0B5MzpY9kBtDVTGZjcWkzT3pldDA',
    '20170512-110547': '0B5MzpY9kBtDVZ2RpVDYwWmxoSUk'
    }

##########################################################


def download_and_extract_file(
        model_name: str,
        data_dir: DirPath,
        source_url: Url,
        model_dict: Dict[str, str]
    ) -> None:
    file_id = model_dict[model_name]
    destination = os.path.join(data_dir, model_name + '.zip')
    if not os.path.exists(destination):
        logger.info('Downloading file to %s' % destination)
        download_file_from_google_drive(file_id, destination, source_url)
        with zipfile.ZipFile(destination, 'r') as zip_ref:
            logger.info('Extracting file to %s' % data_dir)
            zip_ref.extractall(data_dir)


def download_file_from_google_drive(file_id: str, destination: FilePath, source_url: Url) -> None:
    session = requests.Session()
    response = session.get(source_url, params = { 'id' : file_id }, stream = True)
    token = get_confirm_token(response)
    if token:
        params = { 'id' : file_id, 'confirm' : token }
        response = session.get(source_url, params = params, stream = True)
    save_response_content(response, destination)    


def get_confirm_token(response: Dict[str, str]) -> Optional[str]:
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None


def save_response_content(response: Dict[str, str], destination: FilePath) -> None:
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)


def main() -> None:
    download_and_extract_file(
        model_name=SELECTED_MODEL,
        data_dir=OUTPUT_MODEL_DIR,
        source_url=SOURCE_BASE_URL,
        model_dict=MODEL_DICT
    )

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()