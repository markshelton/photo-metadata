# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import logging
import random

##########################################################
# Third Party Imports

from pymarc import parse_xml_to_array
from pymarc.reader import MARCReader, JSONReader

##########################################################
# Local Imports

from thickshake.helpers import open_file, get_file_type, sample_items

##########################################################
# Typing Configuration

from typing import List, Any, Union, Dict, Callable, Optional

FilePath = str
File = Any
PymarcRecord = Any

##########################################################
# Constants

class FileType:
    JSON = ".json"
    MARC = ".marc"
    XML = ".xml"

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Functions


def read_marc(input_file: FilePath, **kwargs) -> List[PymarcRecord]:
    return list(MARCReader(open_file(input_file)))


def read_marc_xml(input_file: str, sample_size: int = 0, **kwargs) -> List[PymarcRecord]:
    return parse_xml_to_array(input_file)


def read_marc_json(input_file: FilePath, **kwargs) -> List[PymarcRecord]:
    return list(JSONReader(open_file(input_file)))


def read_file(input_metadata_file: FilePath, sample: Optional[int]=None, **kwargs: Any) -> List[PymarcRecord]:
    file_type = get_file_type(input_metadata_file)
    if file_type == FileType.MARC: records = read_marc(input_metadata_file)
    elif file_type == FileType.XML: records = read_marc_xml(input_metadata_file)
    elif file_type == FileType.JSON: records = read_marc_json(input_metadata_file)
    else: raise NotImplementedError
    if sample is not None: records = sample_items(records, sample)
    return records


##########################################################
# Scripts


def main():
    pass


if __name__ == "__main__":
    main()


##########################################################
