##########################################################
# Standard Library Imports

import datetime
from functools import reduce, wraps
import logging
import os
import pathlib
import random
import shutil
import time

##########################################################
# Third Party Imports

##########################################################
# Local Imports

##########################################################
# Typing Configuration

from typing import Any, Dict, List, Optional, Callable

FilePath = str
DirPath = str
File = Any
Time = Any

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Classes

class FileType:
    JSON = ".json"
    MARC = ".marc"
    XML = ".xml"
    HDF5 = ".hdf5"
    CSV = ".csv"


class Borg:
    _shared_state = {} # type: Dict[Any, Any]
    def __init__(self):
        # type: () -> None
        self.__dict__ = self._shared_state


##########################################################
# Functions


def maybe_make_directory(path):
    # type: (FilePath) -> None
    path_dir = os.path.dirname(path)
    pathlib.Path(path_dir).mkdir(parents=True, exist_ok=True)


def open_file(path, *args, **kwargs):
    # type: (FilePath, *Any, **Any) -> File
    maybe_make_directory(path)
    return open(path, *args, **kwargs)


def deep_get(dictionary, *keys):
    # type: (Dict[str, Any], *str) -> Optional[Any]
    return reduce(lambda d, key: d.get(key, None) if isinstance(d, dict) else None, keys, dictionary)


def consolidate_list(full_list):
    # type: (List[Any]) -> List[Any]
    """Remove null entries from list and return sub-list."""
    consolidated_list = [x for x in full_list if x is not None]
    return consolidated_list


def json_serial(obj):
    # type: (Any) -> str
    if isinstance(obj, (datetime.datetime, datetime.date)): return obj.isoformat()
    else: raise TypeError("Type %s not serializable" % type(obj))


def clear_directory(dir_path):
    # type: (DirPath) -> None
    if dir_path is None: return None
    try: shutil.rmtree(dir_path)
    except EnvironmentError: logger.info("Output directory already empty.")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def get_files_in_directory(dir_path, ext="jpg", **kwargs):
    # type: (DirPath, Optional[str], **Any) -> List[FilePath]
    files = [os.path.join(dir_path,fn) for fn in next(os.walk(dir_path))[2]]
    if ext: files = [f for f in files if f.endswith(ext)]
    files = sample_items(files, **kwargs)
    return files


def maybe_increment_path(file_path, sep="_", overwrite=False, **kwargs):
    # type: (FilePath, str, bool, **Any) -> Optional[FilePath]
    file_path_base, file_ext = os.path.splitext(file_path)
    directory_path = os.path.dirname(file_path)
    i = 1
    while True:
        full_file_path = "%s%s%s%s" % (file_path_base, sep, i, file_ext)
        if not os.path.exists(full_file_path):
            return full_file_path
        i += 1


def get_file_type(path):
    # type: (FilePath) -> str
    return os.path.splitext(path)[1]


def convert_file_type(path, file_type):
    # type: (FilePath, str) -> FilePath
    return path.replace(get_file_type(path), file_type)


def generate_output_path(input_path, output_dir=None, sub_folder=None):
    # type: (FilePath, DirPath, str) -> FilePath
    if output_dir is not None:
        base = os.path.basename(input_path)
        if sub_folder is not None:
            return output_dir + "/" + sub_folder + "/" + base
        return output_dir + "/" + base
    return input_path.replace("input", "output")


def sample_items(items, sample=0, **kwargs):
    # type: (List[Any], int, **Any) -> List[Any]
    if sample == 0: return items
    else: return random.sample(items, sample)


def check_output_directory(output_dir=None, force=True, **kwargs):
    # type: (DirPath, bool, **Any) -> None
    if not force and output_dir is not None:
        if len(get_files_in_directory(output_dir)) > 0:
            raise IOError
    clear_directory(output_dir) 


##########################################################