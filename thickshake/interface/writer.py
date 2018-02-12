# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Python Compatibility

from __future__ import print_function, division, absolute_import
from future import standard_library
standard_library.install_aliases()

##########################################################
# Standard Library Imports

import logging
import os
import time

##########################################################
# Third Party Imports

from pymarc.writer import MARCWriter, XMLWriter, JSONWriter
from tqdm import tqdm

##########################################################
# Local Imports

from thickshake.utils import open_file, get_file_type, sample_items, FileType

##########################################################
# Typing Configuration

from typing import Text, Any, List, Union, Dict, Callable, Optional, AnyStr

FilePath = Text
File = Any
PymarcRecord = Any

##########################################################
# Constants

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Functions


def _write_file(records, output_file, writer, force=False, dry_run=False, sample=0, **kwargs):
    # type: (List[PymarcRecord], FilePath, Any, bool, bool, int, **Any) -> None
    if not force and os.path.exists(output_file): raise IOError
    records = sample_items(records, sample)
    for record in tqdm(records, desc="Writing Records"):
        if not dry_run: writer.write(record)
    writer.close()


def write_file(records, output_file, **kwargs):
    # type: (List[PymarcRecord], FilePath, **Any) -> None
    file_type = get_file_type(output_file)
    if file_type == FileType.MARC: writer = MARCWriter(open_file(output_file, "wb+"))
    elif file_type == FileType.XML: writer = XMLWriter(open_file(output_file, "wb+"))
    elif file_type == FileType.JSON: writer = JSONWriter(open_file(output_file, "w+", encoding="utf-8"))
    else: raise NotImplementedError
    _write_file(records, output_file, writer, **kwargs)


##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    main()


##########################################################
