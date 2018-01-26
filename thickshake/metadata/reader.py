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

import pymarc

##########################################################
# Local Imports

from thickshake.utils import setup_warnings, setup_logging, get_file_type

##########################################################
# Typing Configuration

from typing import List, Any

FilePath = str
DirPath = str
PymarcRecord = Any

##########################################################
# Constants

FILETYPE_JSON = ".json"
FILETYPE_MARC21 = ".marc"
FILETYPE_MARCXML = ".xml"

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Functions


def sample_records(records: List[Any], sample_size: int = 0) -> List[Any]:
    return records if sample_size == 0 else random.sample(records, sample_size)


def read_marcxml(input_file: str, sample_size: int = 0, **kwargs) -> List[PymarcRecord]:
    return pymarc.parse_xml_to_array(input_file)


def read_marc21(input_file: FilePath, **kwargs) -> List[PymarcRecord]:
    return list(pymarc.reader.MARCReader(input_file))


def read_json(input_file: FilePath, **kwargs) -> List[PymarcRecord]:
    return list(pymarc.reader.JSONReader(input_file))


def read_file(input_metadata_file: FilePath, **kwargs) -> List[PymarcRecord]:
    file_type = get_file_type(input_file)
    if file_type == FILETYPE_JSON:
        records = read_json(input_file)
    elif file_type == FILETYPE_MARC21:
        records = read_marc21(input_file)
    elif file_type == FILETYPE_MARCXML:
        records = read_marcxml(input_file)
    else: raise NotImplementedError
    records = sample_records(records, sample_size)
    return records


##########################################################
# Scripts

def main():
    read_file()


if __name__ == "__main__":
    setup_warnings()
    setup_logging()
    main()


##########################################################
