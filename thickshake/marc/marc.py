# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import logging
import os

##########################################################
# Third Party Imports


##########################################################
# Local Imports

from thickshake.marc.reader import read_file
from thickshake.marc.importer import load_database
from thickshake.marc.exporter import export_database
from thickshake.marc.writer import write_file
from thickshake.helpers import convert_file_type, generate_output_path, FileType

##########################################################
# Typing Configuration

from typing import Any, List
FilePath = str
PymarcRecord = Any

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Functions


def combine_records(records_new: List[PymarcRecord], records_out: List[PymarcRecord], **kwargs) -> List[PymarcRecord]:
    pass


# Import metadata files from any format to RDBMS
def import_metadata(input_metadata_file: FilePath, **kwargs) -> None:
    assert os.path.exists(input_metadata_file)
    records = read_file(input_metadata_file, **kwargs)
    load_database(records, **kwargs)


# Export metadata records from RDBMS to any format
def export_metadata(output_metadata_file: FilePath, input_metadata_file: FilePath=None, partial: bool=True, force: bool=True, **kwargs) -> None:
    if not force: assert not os.path.exists(output_metadata_file)
    if not partial: assert input_metadata_file is not None
    records = export_database(force=False, **kwargs)
    if not partial:
        records_old = read_file(input_metadata_file, force=force, **kwargs)
        records = combine_records(records, records_old, force=force, **kwargs)
    write_file(records, output_metadata_file, force=force, **kwargs)


# Convert metadata files from one format to another
# e.g. MARCXML -> SQL Dump, MARC21 -> HDF5
def convert_metadata(
        input_metadata_file: FilePath,
        output_metadata_file: FilePath=None,
        output_metadata_type: str=None,
        **kwargs
    ) -> FilePath:
    records = read_file(input_metadata_file, **kwargs)
    if output_metadata_file is None:
        output_metadata_file = generate_output_path(input_metadata_file)
        output_metadata_file = convert_file_type(output_metadata_file, output_metadata_type) 
    write_file(records, output_metadata_file, **kwargs)
    return output_metadata_file

##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    main()


##########################################################
