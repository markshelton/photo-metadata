# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import logging
import time

##########################################################
# Third Party Imports

from pymarc.writer import MARCWriter, XMLWriter, JSONWriter

##########################################################
# Local Imports

from thickshake.helpers import setup, open_file, log_progress, get_file_type

##########################################################
# Typing Configuration

from typing import List, Any, Union, Dict, Callable

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


def _write_file(
        records: List[PymarcRecord],
        output_file: FilePath,
        PymarcWriter: Callable[[File], None],
        verbose: bool=False,
        force: bool=False,
        dry_run: bool=False,
        sample: Optional[int]=None,
        **kwargs: Any
    ) -> None:
    if not force and os.path.exists(output_file): raise IOError
    if sample is not None: records = sample_items(records, sample)
    with PymarcWriter(open_file(output_file, "wb")) as writer:
        total = len(records)
        start_time = time.time()
        if verbose: logger.info("Writing %s records to %s.", total, output_file)
        for i, record in enumerate(records):
            if not dry_run: writer.write(record)
            if verbose: log_progress(i, total, start_time)


def write_file(records: List[PymarcRecord], output_file: FilePath, **kwargs: Any) -> None:
    file_type = get_file_type(output_file)
    if file_type == FileType.MARC: PymarcWriter = MARCWriter
    elif file_type == FileType.XML: PymarcWriter = XMLWriter
    elif file_type == FileType.JSON: PymarcWriter = JSONWriter
    _write_file(records, output_file, PymarcWriter, **kwargs)
    else: raise NotImplementedError


##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    setup()
    main()


##########################################################
