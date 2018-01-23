##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

from envparse import env

##########################################################
# Local Imports

from thickshake.parser.geocoder import extract_location
from thickshake.mtd.database import load_column, save_columns
from thickshake.utils import setup_logging, setup_warnings
from thickshake.types import *

##########################################################
# Constants

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["drivername"] = env.str("DB_DRIVER")
DB_CONFIG["host"] = env.str("DB_HOST")
DB_CONFIG["database"] = env.str("POSTGRES_DB")
DB_CONFIG["username"] = env.str("POSTGRES_USER")
DB_CONFIG["password"] = env.str("POSTGRES_PASSWORD")

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


# 
def augment_metadata(db_config: DBConfig=DB_CONFIG, **kwargs: Any) -> None:
    process_field(
        input_field=("image", "image_note"),
        output_field={}, # TODO
        parser=extract_location,
        db_config=db_config,
        **kwargs
    )


def process_field(
        input_field: Tuple[str, str], # Table, Column
        output_field: Dict[str, Tuple[str, str]], # Map (df column -> (db table, db column))
        parser: Parser,
        db_config: DBConfig=DB_CONFIG,
        **kwargs: Any
    ) -> None:
    input_series = load_column(*input_field, db_config=db_config)
    output_dataframe = parser(input_series, **kwargs)
    save_columns(*output_field, data=output_dataframe, db_config=db_config)


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