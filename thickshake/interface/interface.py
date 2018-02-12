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

##########################################################
# Third Party Imports


##########################################################
# Local Imports

from thickshake.interface.reader import read_file
from thickshake.interface.importer import load_database
from thickshake.interface.exporter import export_database
from thickshake.interface.writer import write_file
from thickshake.utils import convert_file_type, generate_output_path, FileType

##########################################################
# Typing Configuration

from typing import Text, Any, List, AnyStr
FilePath = Text
PymarcRecord = Any

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Functions

#TODO
def combine_records(records_new, records_old, **kwargs):
    # type: (List[PymarcRecord], List[PymarcRecord], **Any) -> List[PymarcRecord]
    pass


def import_metadata(input_metadata_file, **kwargs):
    # type: (FilePath, **Any) -> None
    """Import metadata files from any format to RDBMS."""
    assert os.path.exists(input_metadata_file)
    records = read_file(input_metadata_file, **kwargs)
    load_database(records, **kwargs)


def export_metadata(output_metadata_file, input_metadata_file=None, partial=True, force=True, **kwargs):
    # type: (FilePath, FilePath, bool, bool, **Any) -> None
    """Export metadata records from RDBMS to any format."""
    if not force: assert not os.path.exists(output_metadata_file)
    if not partial: assert input_metadata_file is not None
    records = export_database(force=False, **kwargs)
    if not partial:
        records_old = read_file(input_metadata_file, force=force, **kwargs)
        records = combine_records(records, records_old, force=force, **kwargs)
    write_file(records, output_metadata_file, force=force, **kwargs)


def convert_metadata(input_metadata_file, output_metadata_file=None, output_metadata_type=None, **kwargs):
    # type: (FilePath, FilePath, AnyStr, **Any) -> FilePath
    """Convert metadata files from one format to another."""
    records = read_file(input_metadata_file, **kwargs)
    if output_metadata_file is None:
        output_metadata_file = generate_output_path(input_metadata_file)
        output_metadata_file = convert_file_type(output_metadata_file, output_metadata_type) 
    write_file(records, output_metadata_file, **kwargs)
    return output_metadata_file


##########################################################