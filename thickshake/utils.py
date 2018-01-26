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


def logged(f: Callable[..., Any]) -> Any:
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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
    else:
        raise TypeError("Type %s not serializable" % type(obj))


def setup_logging(internal: int=logging.DEBUG, external: int=logging.WARN) -> None:
    logging.basicConfig(level=internal)
    logging.getLogger("sqlalchemy.engine").setLevel(external)
    logging.getLogger("PIL.Image").setLevel(external)
    logging.getLogger("PIL.PngImagePlugin").setLevel(external)
    logging.getLogger("datefinder").setLevel(external)


def setup_warnings() -> None:
    warnings.filterwarnings("ignore", category=sqlalchemy.exc.SAWarning)


def setup(internal: int=logging.DEBUG, external: int=logging.WARN) -> None:
    setup_logging(internal, external)
    setup_warnings()


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
        sample_size: int= 0,
        **kwargs: Any
    ) -> List[FilePath]:
    files = [os.path.join(dir_path,fn) for fn in next(os.walk(dir_path))[2]]
    if ext: files = [f for f in files if f.endswith(ext)]
    if sample_size != 0: files = random.sample(files, sample_size)
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


def log_progress(i: int, total: int, start_time: Time, interval: int = 1) -> None:
    if i % interval != 0: return None
    digits = len(str(total))
    perc = i / float(total)
    current_time = time.time()
    elapsed_time = datetime.timedelta(seconds=int(current_time - start_time))
    exp_time = datetime.timedelta(seconds=int(elapsed_time.total_seconds() / perc))
    logger.info("|Records:{curr_count:0{width}}/{total_count}|Time:{elapsed_time}/{exp_time}|{perc:>2.2f}%".format(
            curr_count=i, total_count=total, width=digits, perc=perc*100,
            elapsed_time=str(elapsed_time), exp_time=str(exp_time), 
    ))


def get_file_type(path: FilePath) -> str:
    return os.path.splitext(path)[1]


def generate_diff(input_path: FilePath, output_path: FilePath) -> FilePath:
    pass


def generate_output_path(input_path: FilePath) -> FilePath:
    output_path = input_path.replace("input", "output")
    logger.info("Generated output path: {path}".format(path=output_path))
    return output_path


##########################################################