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
import warnings

##########################################################
# Third Party Imports

import sqlalchemy.exc

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
# Functions


def maybe_make_directory(path: FilePath) -> None:
    path_dir = os.path.dirname(path)
    pathlib.Path(path_dir).mkdir(parents=True, exist_ok=True)


def open_file(path: FilePath, *args: Any, **kwargs: Any) -> File:
    maybe_make_directory(path)
    return open(path, *args, **kwargs)


def deep_get(dictionary: Dict[str, Any], *keys: str) -> Optional[Any]:
    return reduce(lambda d, key: d.get(key, None) if isinstance(d, dict) else None, keys, dictionary)


def consolidate_list(full_list: List[Any]) -> List[Any]:
    """Remove null entries from list and return sub-list."""
    consolidated_list = [x for x in full_list if x is not None]
    return consolidated_list


def json_serial(obj: Any) -> str:
    if isinstance(obj, (datetime.datetime, datetime.date)): return obj.isoformat()
    else: raise TypeError("Type %s not serializable" % type(obj))


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
        **kwargs: Any
    ) -> List[FilePath]:
    files = [os.path.join(dir_path,fn) for fn in next(os.walk(dir_path))[2]]
    if ext: files = [f for f in files if f.endswith(ext)]
    return files


def maybe_increment_path(
        file_path: FilePath,
        sep: str = "_",
        overwrite: bool = False,
        **kwargs: Any
    ) -> Optional[FilePath]:
    file_path_base, file_ext = os.path.splitext(file_path)
    directory_path = os.path.dirname(file_path)
    i = 1
    while True:
        full_file_path = "%s%s%s%s" % (file_path_base, sep, i, file_ext)
        if not os.path.exists(full_file_path):
            return full_file_path
        i += 1


def log_progress(logger, i: int, total: int, start_time: Time, interval: int = 1) -> None:
    if i % interval != 0: return None
    digits = len(str(total))
    perc = i / float(total)
    current_time = time.time()
    elapsed_time = datetime.timedelta(seconds=int(current_time - start_time))
    exp_time = datetime.timedelta(seconds=int(elapsed_time.total_seconds() / perc))
    logger.info("Records:{curr_count:0{width}}/{total_count} | Time:{elapsed_time}/{exp_time} | {perc:>2.2f}%".format(
            curr_count=i, total_count=total, width=digits, perc=perc*100,
            elapsed_time=str(elapsed_time), exp_time=str(exp_time), 
    ))


def get_file_type(path: FilePath) -> str:
    return os.path.splitext(path)[1]



def generate_output_path(input_path: FilePath) -> FilePath:
    output_path = input_path.replace("input", "output")
    logger.info("Generated output path: {path}".format(path=output_path))
    return output_path


def sample_items(items: List[Any], sample: int = 0, **kwargs) -> List[Any]:
    if sample == 0: return items
    else: return random.sample(items, sample)


##########################################################