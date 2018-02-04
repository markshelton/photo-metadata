# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

from envparse import env
import pandas as pd
import tables

##########################################################
# Local Imports

from thickshake.utils import Borg

##########################################################
# Typing Configuration

from typing import Any
FilePath = str

##########################################################
# Constants

STORE_PATH = env.str("STORE", default="/home/app/data/output/store.hdf5")

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions

class Store(Borg):
    store_path = None
    write_mode = "a"
    read_mode = "r"
    

    def __init__(self, store_path: FilePath = STORE_PATH, force: bool=False, **kwargs) -> None:
        Borg.__init__(self)
        if self.store_path is None:
            self.write_mode = "w" if force else "a"
            self.store_path = store_path
            with pd.HDFStore(self.store_path, self.write_mode) as f: pass


    def save(self, dataset_path, df, index, **kwargs) -> None:
        with pd.HDFStore(self.store_path, "a") as store:
            store.append(dataset_path, df, index=index)


    def contains(self, dataset_path) -> bool:
        with pd.HDFStore(self.store_path, 'r') as store:
            return dataset_path in store and not store[dataset_path].shape is None


    def get_dataframe(self, dataset_path) -> pd.DataFrame:
        with pd.HDFStore(self.store_path, 'r') as store:
            return store.get(dataset_path)

    #TODO
    def export_to_database(self, series, output_map) -> None:
        from thickshake.storage import Database
        pass

##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()

