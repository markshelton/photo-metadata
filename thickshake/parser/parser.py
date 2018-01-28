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
from thickshake.helpers import setup_logging, setup_warnings

##########################################################
# Typing Configuration

from typing import Tuple, Dict, Any

##########################################################
# Constants

##########################################################
# Initializations

logger = logging.getLogger(__name__)
database = Database()

##########################################################
# Functions


def process_field(
        input_field: Tuple[str, str], # Table, Column
        output_field: Dict[str, Tuple[str, str]], # Map (df column -> (db table, db column))
        parser: Parser,
        **kwargs: Any
    ) -> None:
    input_series = database.load_column(*input_field)
    output_dataframe = parser(input_series, **kwargs)
    database.save_columns(*output_field, data=output_dataframe)


def augment_metadata(
        input_metadata_file: FilePath,
        output_metadata_file: FilePath = None,
        input_image_dir: DirPath = None,
        diff: bool = True,
        **kwargs
    ) -> None:
    if output_metadata_file is None:
        output_metadata_file = generate_output_path(input_metadata_file)
    import_metadata(input_metadata_file, **kwargs)
    apply_parsers(**kwargs)
    export_metadata(output_metadata_file, **kwargs)
    if diff: generate_diff(input_metadata_file, output_metadata_file)


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