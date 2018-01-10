##########################################################
# Standard Library Imports

import logging
import os
import pathlib
import time
from functools import reduce, wraps
import datetime

##########################################################
# Third Party Imports


##########################################################
# Local Imports

from thickshake._types import (
    Dict, Optional, List, Any,
    FilePath, File,
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
        except:
            elapsed_time = time.time() - start_time
            logger.error("{0} | Failed | {1:.2f}".format(f.__name__,elapsed_time), exc_info=True)
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