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
import h5py

##########################################################
# Local Imports


##########################################################
# Typing Configuration

from typing import Any
FilePath = str

##########################################################
# Constants

STORE = env.str("STORE", default="/home/app/data/output/store.hdf5")

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions

class Store:
    path = None    

    def __init__(self, store_path: FilePath = STORE) -> None:
        if self.path is None:
            self.engine = self.make_file(store_path)
    

    #TODO
    def make_file(self, store_path: FilePath) -> None:
        pass
    

    def save_object(self, obj: Any, group_name: str, object_id: str = None) -> None:
        with h5py.File(self.path, "a") as f:
            grp = f.require_group(group_name)
            if object_id is not None:
                grp.create_dataset(object_id, data=obj)


    #TODO
    def save_records(self, obj: Any, group_name: str) -> None:
        pass


    #TODO
    def retrieve_object(self, group_name: str, object_id: str = None) -> None:
        with h5py.File(self.path, "a") as f:
            pass


    #TODO
    def delete_object(self, group_name: str, object_id: str = None) -> None:
        with h5py.File(self.path, "a") as f:
            pass


##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()

