# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

##########################################################
# Local Imports

##########################################################
# Typing Configuration

from typing import List, Any, Union, Dict

##########################################################
# Constants

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################


def export_database(database: Database, store: Store, sql_text: str = None, **kwargs: Any) -> None:
    if sql_text is None: records = database.dump()
    else: records = database.execute_sql_text(sql_text)
    store.save_records(records, group_name="database_export")


def import_store(database: Database, store: Store, store_path: str = None, **kwargs: Any) -> None:
    pass


##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    main()


##########################################################
