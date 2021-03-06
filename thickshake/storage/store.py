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

##########################################################
# Third Party Imports

from envparse import env
import pandas as pd
import tables

##########################################################
# Local Imports

from thickshake.utils import Borg, maybe_make_directory

##########################################################
# Typing Configuration

from typing import Text, Any, Iterable, Dict, List, AnyStr
FilePath = Text
Series = Any
DataFrame = Any

##########################################################
# Constants

STORE_PATH = env.str("STORE", default="/home/app/data/output/store.hdf5")

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


def fix_unicode_columns(df):
    # type: (DataFrame) -> DataFrame
    types = df.apply(lambda x: pd.api.types.infer_dtype(x.values))
    for col in types[types=='unicode'].index:
        df[col] = df[col].astype(str)
    df.columns = [str(c) for c in df.columns]
    return df


class Store(Borg):
    store_path = None
    write_mode = "a"
    read_mode = "r"
    

    def __init__(self, store_path=STORE_PATH, force=False, **kwargs):
        # type: (FilePath, bool, **Any) -> None
        Borg.__init__(self)
        if self.store_path is None:
            self.write_mode = "w" if force else "a"
            self.store_path = store_path
            maybe_make_directory(store_path)
            with pd.HDFStore(self.store_path, self.write_mode) as f: pass


    def save(self, dataset_path, df, index, **kwargs):
        # type: (AnyStr, DataFrame, List[AnyStr], **Any) -> None
        df = fix_unicode_columns(df)
        with pd.HDFStore(self.store_path, "a") as store:
            store.append(dataset_path, df, index=index, min_itemsize=50)


    def contains(self, dataset_path):
        # type: (AnyStr) -> bool
        with pd.HDFStore(self.store_path, 'r') as store:
            return dataset_path in store and not store[dataset_path].shape is None


    def get_file(self):
        # type: () -> DataFrame
        return pd.HDFStore(self.store_path, 'r')


    def get_dataframe(self, dataset_path):
        # type: (AnyStr) -> DataFrame
        with pd.HDFStore(self.store_path, 'r') as store:
            return store.get(dataset_path)

    #TODO
    def export_to_database(self, series, output_map):
        from thickshake.storage import Database
        pass


    def display(self):
        # type: () -> None
        with pd.HDFStore(self.store_path, 'r') as store:
            logger.info(store.info())


##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    main()


##########################################################
