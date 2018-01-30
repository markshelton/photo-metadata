# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
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

from thickshake.helpers import open_file, get_file_type, sample_items, FileType

##########################################################
# Typing Configuration

from typing import List, Any, Union, Dict, Callable, Optional

FilePath = str
File = Any
PymarcRecord = Any

##########################################################
# Constants

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Functions


def _write_file(
        records: List[PymarcRecord],
        output_file: FilePath,
        writer: Any,
        force: bool=False,
        dry_run: bool=False,
        sample: Optional[int]=None,
        **kwargs: Any
    ) -> None:
    if not force and os.path.exists(output_file): raise IOError
    if sample is not None: records = sample_items(records, sample)
    for record in tqdm(records, desc="Writing Records"):
        if not dry_run: writer.write(record)
    writer.close()


def write_file(records: List[PymarcRecord], output_file: FilePath, **kwargs: Any) -> None:
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
