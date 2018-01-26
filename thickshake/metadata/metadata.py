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

from thickshake.metadata.reader import read_file
from thickshake.metadata.loader import load_database
from thickshake.metadata.exporter import dump_database
from thickshake.metadata.writer import write_file
from thickshake.utils import setup

##########################################################
# Typing Configuration

from typing import Any
FilePath = str

##########################################################
# Constants

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Functions


# Import metadata files from any format to RDBMS
def import_metadata(input_file: FilePath, **kwargs) -> None:
    assert os.path.exists(input_file)
    records = read_file(input_file)
    load_database(records)


# Export metadata records from RDBMS to any format
def export_metadata(output_file: FilePath, **kwargs) -> None:
    assert not os.path.exists(output_file)
    records = dump_database()
    write_file(records, output_file)


##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    setup()
    main()


##########################################################
