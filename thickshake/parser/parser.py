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
        sample: int = 0,
        **kwargs: Any
    ) -> None:
    from thickshake.storage.database import Database
    database = Database(**dict(kwargs, force=False))
    input_dataframe = database.load_columns(input_table, input_columns, **kwargs)
    if sample != 0: input_dataframe = input_dataframe.sample(n=sample)
    total = input_dataframe.shape[0] 
    for i, row in tqdm(input_dataframe.iterrows(), total=total, desc="Parsing Records (%s)" % (parser.__name__)):
        input_values = row[input_columns].values
        if len(input_values) == 1: input_values = input_values[0]
        output_values = parser(input_values, **kwargs)
        if output_values:
            output_series = pd.DataFrame(output_values, index=[i])
            database.save_record(input_table, output_table, output_map, output_series, **kwargs)


def parse_locations(**kwargs: Any) -> None:
    from thickshake.parser.geocoder import extract_location
    apply_parser(
        input_table = "image",
        input_columns = ["image_note"],
        output_table = "location",
        output_map = { 
            "index": "image_uuid",
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
    from thickshake.parser.links import extract_image_links
    apply_parser(
        input_table = "image",
        input_columns = ["image_url"],
        output_table = "image",
        output_map = { 
            "index": "uuid",
            "image_label": "image_label",
            "image_url_raw": "image_url_raw",
            "image_url_thumb": "image_url_thumb",
        },
        parser = extract_image_links,
        **kwargs
    )


def parse_sizes(**kwargs: Any) -> None:
    from thickshake.parser.links import extract_image_dimensions
    apply_parser(
        input_table = "image",
        input_columns = ["image_url_raw"],
        output_table = "image",
        output_map = { 
            "index": "uuid",
            "image_height": "image_height",
            "image_width": "image_width"
        },
        parser = extract_image_dimensions,
        **kwargs
    )


def parse_dates(**kwargs: Any) -> None:
    from thickshake.parser.dates import extract_date_from_title, combine_dates, split_dates
    apply_parser(
        input_table = "image",
        input_columns = ["image_note"],
        output_table = "image",
        output_map = { 
            "index": "uuid",
            "date": "image_date_created"
        },
        parser = extract_date_from_title,
        **kwargs
    )
    apply_parser(
        input_table = "record",
        input_columns = ["date_created", "date_created_approx"],
        output_table = "record",
        output_map = { 
            "index": "uuid",
            "date": "date_created_parsed"
        },
        parser = combine_dates,
        **kwargs
    )
    apply_parser(
        input_table = "subject",
        input_columns = ["subject_dates"],
        output_table = "subject",
        output_map = { 
            "index": "uuid",
            "start_date": "subject_start_date",
            "end_date": "subject_end_date"
        },
        parser = split_dates,
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