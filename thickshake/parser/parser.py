##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

from envparse import env
import pandas as pd
from tqdm import tqdm

##########################################################
# Local Imports

from thickshake.parser.geocoder import extract_location
#from thickshake.parser.dates import extract_date
#from thickshake.parser.links import extract_links
from thickshake.storage.database import Database

##########################################################
# Typing Configuration

from typing import Tuple, Dict, Any, List
Parser = Any
FilePath = str
DirPath = str

##########################################################
# Constants

##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Functions


def apply_parser(
        input_table: str, #Table
        input_columns: List[str], # Columns
        output_table: str,
        output_map: Dict[str, str], # Map (df column -> db column)
        parser: Parser,
        sample: int,
        **kwargs: Any
    ) -> None:
    database = Database(**kwargs)
    input_dataframe = database.load_columns(input_table, input_columns, **kwargs)
    if sample != 0: input_dataframe = input_dataframe.sample(n=sample)
    output_records = []
    total = input_dataframe.shape[0] 
    for _, row in tqdm(input_dataframe.iterrows(), total=total, desc="Parsing Records"):
        input_values = row[input_columns].values
        if len(input_values) == 1: input_values = input_values[0]
        output_values = parser(input_values, **kwargs)
        output_records.append(output_values)
    output_dataframe = pd.DataFrame.from_records(output_records, index=input_dataframe.index)
    database.save_columns(input_table, output_table, output_map, output_dataframe, **kwargs)


def parse_locations(**kwargs: Any) -> None:
    apply_parser(
        input_table = "image",
        input_columns = ["image_note"],
        output_table = "location",
        output_map = { 
            "uuid": "image_uuid",
            "building_name": "building_name",
            "street_number": "street_number",
            "street_name": "street_name",
            "street_type": "street_type",
            "suburb": "suburb",
            "state": "state",
            "post_code": "post_code",
            "latitude": "latitude",
            "longitude": "longitude",
            "confidence": "confidence",
            "location_type": "location_type"
        },
        parser = extract_location,
        **kwargs
    )


def parse_links(**kwargs: Any) -> None:
    apply_parser(
        input_table = "image",
        input_columns = ["image_url"],
        output_table = "image",
        output_map = { 
            "uuid": "uuid",
            "image_label": "image_label",
            "image_url_raw": "image_url_raw",
            "image_url_thumb": "image_url_thumb",
            "image_height": "image_height",
            "image_width": "image_width"
        },
        parser = None, #extract_links,
        **kwargs
    )


def parse_dates(**kwargs: Any) -> None:
    apply_parser(
        input_table = "image",
        input_columns = ["image_note"],
        output_table = "image",
        output_map = { 
            "uuid": "uuid",
            "image_date_created": "image_date_created"
        },
        parser = None, #extract_date,
        **kwargs
    )


##########################################################
# Main


def main():
    augment_metadata(
        db_config=DB_CONFIG
    )


if __name__ == "__main__":
    main()