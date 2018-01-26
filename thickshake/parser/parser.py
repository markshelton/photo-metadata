##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

from envparse import env

##########################################################
# Local Imports

from thickshake.parser.geocoder import extract_location
from thickshake.database import Database
from thickshake.utils import setup_logging, setup_warnings
from thickshake.types import *

##########################################################
# Constants

##########################################################
# Initializations

logger = logging.getLogger(__name__)
database = Database()

##########################################################
# Functions


# 
def augment_metadata(**kwargs: Any) -> None:
    process_field(
        input_field=("image", "image_note"),
        output_field={}, # TODO
        parser=extract_location,
        **kwargs
    )


def process_field(
        input_field: Tuple[str, str], # Table, Column
        output_field: Dict[str, Tuple[str, str]], # Map (df column -> (db table, db column))
        parser: Parser,
        **kwargs: Any
    ) -> None:
    input_series = database.load_column(*input_field)
    output_dataframe = parser(input_series, **kwargs)
    database.save_columns(*output_field, data=output_dataframe)


##########################################################
# Main


def main():
    augment_metadata(
        db_config=DB_CONFIG
    )


if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()