##########################################################
# Standard Library Imports

import logging
import os
import pathlib
import time
from functools import reduce, wraps
import datetime
import warnings
import random
import shutil

##########################################################
# Third Party Imports

import sqlalchemy.exc

##########################################################
# Local Imports

from thickshake._types import (
    Dict, Optional, List, Any,
    FilePath, File, DirPath
)

##########################################################
# Helper Methods


def check_and_make_directory(path: FilePath) -> None:
    path_dir = os.path.dirname(path)
    pathlib.Path(path_dir).mkdir(parents=True, exist_ok=True)


def open_file(path: FilePath, *args: Any, **kwargs: Any) -> File:
    check_and_make_directory(path)
    return open(path, *args, **kwargs)


def logged(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger()
        logger.info("{0} | Started".format(f.__name__))
        start_time = time.time()
        try: result = f(*args, **kwargs)
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error("{0} | Failed | {1:.2f}".format(f.__name__,elapsed_time), exc_info=True)
            raise e
        else:
            elapsed_time = time.time() - start_time
            logger.info("{0} | Passed | {1:.2f}".format(f.__name__,elapsed_time))
            return result
    return wrapper    


def deep_get(dictionary: Dict, *keys: str) -> Optional[Any]:
    return reduce(lambda d, key: d.get(key, None) if isinstance(d, dict) else None, keys, dictionary)


def consolidate_list(full_list: List[Any]) -> List[Any]:
    """Remove null entries from list and return sub-list."""
    consolidated_list = [x for x in full_list if x is not None]
    return consolidated_list


def json_serial(obj: Any) -> str:
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def setup_logging() -> None:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
    logging.getLogger("PIL.Image").setLevel(logging.INFO)
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)
    logging.getLogger("datefinder").setLevel(logging.INFO)


def setup_warnings() -> None:
    warnings.filterwarnings("ignore", category=sqlalchemy.exc.SAWarning)

def clear_directory(dir_path: Optional[DirPath]) -> None:
    if dir_path is None: return None
    try:
        shutil.rmtree(dir_path)
    except FileNotFoundError:
        logger.info("Output directory already empty.")
    os.makedirs(dir_path, exist_ok=True)


def get_files_in_directory(
        dir_path: DirPath,
        ext: Optional[str]="jpg",
        sample_size: Optional[int]= None,
        **kwargs
    ) -> List[FilePath]:
    files = [os.path.join(dir_path,fn) for fn in next(os.walk(dir_path))[2]]
    if ext: files = [f for f in files if f.endswith(ext)]
    if sample_size: files = random.sample(files, sample_size)
    return files


def maybe_increment_path(
        file_path: FilePath,
        sep: str = "_",
        overwrite: bool = False,
        **kwargs
    ) -> Optional[FilePath]:
    file_path_base, file_ext = os.path.splitext(file_path)
    directory_path = os.path.dirname(file_path)
    i = 1
    while True:
        full_file_path = "%s%s%s%s" % (file_path_base, sep, i, file_ext)
        if not os.path.exists(full_file_path):
            return full_file_path
        i += 1