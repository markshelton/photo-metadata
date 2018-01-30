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

from envparse import env
import pymarc
from tqdm import tqdm
import yaml

##########################################################
# Local Imports

from thickshake.storage.database import Database
from thickshake.marc.utils import load_config_file

##########################################################
# Typing Configuration

from typing import Optional, Union, List, Dict, Any
PymarcField = Any
PymarcRecord = Any
FilePath = str 

##########################################################
# Constants

##########################################################
# Database Configuration

database = Database()

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


def load_record(
        data: Union[PymarcField, PymarcRecord],
        loader: Dict[str, Any],
        config: Dict[str, Any],
        database: Database,
        temp_uids: Dict[str, str] = None,
        **kwargs: Any
    ) -> None:
    pass


def export_database(
        loader_config_file: FilePath=None,
        **kwargs: Any
    ) -> List[PymarcRecord]:
    database = Database(**kwargs)
    with database.manage_db_session(**kwargs) as session:
        records = database.get_records(**kwargs)
        loader_config, loader_map = load_config_file(loader_config_file)
        for record in tqdm(records, desc="Exporting Records"):
            export_record(data=record, loader=loader_map, config=loader_config, database=database, **kwargs)



##########################################################
# Main

def main() -> None:
    pass


if __name__ == "__main__":
    main()

##########################################################
