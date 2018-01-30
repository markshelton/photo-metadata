# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import csv
import json
import logging
import os
import re
import time

##########################################################
# Third Party Imports

from envparse import env
import geopy.distance
import pandas as pd
import requests
from tqdm import tqdm

##########################################################
# Local Imports

from thickshake.storage.database import Database
from thickshake.helpers import deep_get, consolidate_list

##########################################################
# Typing Configuration

from typing import Any, List, Dict, Optional, Pattern, Match, Iterable
Address = Dict[str, Optional[str]]
Location = Dict[str, Optional[str]]
Series = Iterable[Any]
DataFrame = Dict[str, Series]
FilePath = str
Url = str

##########################################################
# Constants

MAPPIFY_BASE_URL = env.str("MAPPIFY_BASE_URL", default="https://mappify.io/api/rpc/address/geocode/") # type: Url
MAPPIFY_API_KEY = env.str("MAPPIFY_API_KEY", default=None) # type: Optional[str]

CURRENT_FILE_DIR, _ = os.path.split(__file__)
MTD_LOC_STREET_TYPES_FILE = "%s/deps/aus_street_types.csv" % (CURRENT_FILE_DIR) # type: FilePath
MTD_LOC_SUBURB_NAMES_FILE = "%s/deps/wa_suburb_names.csv" % (CURRENT_FILE_DIR) # type: FilePath
MTD_LOC_ADDRESS_STOP_WORDS_FILE ="%s/deps/stop_words.csv" % (CURRENT_FILE_DIR) # type: FilePath
MTD_LOC_DEFAULT_STATE = "WA" # type: str

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Database Configuration

database = Database()

##########################################################
# Helpers


def read_csv_to_dict(csv_file: FilePath) -> Dict[str, List[str]]:
    """Read CSV file into a dictionary"""
    with open(csv_file) as csvfile:
        reader = csv.DictReader(csvfile)
        rows = zip(*[d.values() for d in reader])
        header = reader.fieldnames
        outdict = dict(zip(header, rows))
        return outdict


def prepare_search_string(input_file: FilePath) -> str:
    """Read search terms from CSV files and concatentate into string for Regex."""
    search_dict = read_csv_to_dict(input_file)
    search_list = ["|".join(search_dict[key]) for key in search_dict.keys()]
    search_string = "".join(search_list)
    return search_string


def get_matches_from_regex(compiled_regex: Pattern[str], target_text: str) -> List[Match]:
    """Return a dictionary of all named groups for a Regex pattern."""
    matches = [match.groupdict() for match in compiled_regex.finditer(target_text)]
    return [{k:v for k,v in match.items() if v is not None} for match in matches]


def get_street_number(response: Dict[str, Optional[str]]) -> str:
    if response["numberFirst"] and response["numberLast"]:
        return str(response["numberFirst"]) + "-" + str(response["numberLast"])
    elif response["numberFirst"]:
        return response["numberFirst"]
    elif response["numberLast"]:
        return response["numberLast"]
    else: return ""


def choose_best_location(results: List[Dict[str, Optional[str]]]) -> Dict[str, Optional[str]]:
    return max(results, key=lambda x: x.get('confidence'))


def title_case(text: Optional[str]):
    if text is None: return None
    return text.title()


##########################################################
# Functions


def parse_address(
        location_text: str,
        street_types_file: FilePath=MTD_LOC_STREET_TYPES_FILE,
        suburb_names_file: FilePath=MTD_LOC_SUBURB_NAMES_FILE
    ) -> Optional[Address]:
    street_types = prepare_search_string(street_types_file)
    suburb_names = prepare_search_string(suburb_names_file)
    re_main = re.compile(
        r'(?:.*?),\s*' +
        r'(?P<street_number>\d+)?\s*' +
        r'(?P<street_name>.*?)?\s*' +
        r'(?P<street_type>\b(?:{0})\b)?,*\s*'.format(street_types) +
        r'(?P<suburb_name>\b(?:{0})\b)'.format(suburb_names), re.IGNORECASE
    )
    addresses = get_matches_from_regex(re_main, location_text)
    if not addresses: return None
    address = addresses[0]
    return address


def generate_params(
        address: Address,
        api_key: str=MAPPIFY_API_KEY,
        default_state: str=MTD_LOC_DEFAULT_STATE
    ) -> str:
    params_dict = {}
    address_parts = [address.get("street_number"), address.get("street_name"), address.get("street_type") ]
    address_parts = [part for part in address_parts if part is not None and part is not ""]
    if not address_parts: params_dict["streetAddress"] = ""
    params_dict["streetAddress"] = " ".join(address_parts)
    params_dict["suburb"] = address["suburb_name"]
    params_dict["state"] = default_state
    if api_key is not None: params_dict["apiKey"] = api_key
    return params_dict


def geocode_address(address: Address, api_url: Url=MAPPIFY_BASE_URL) -> Location:
    params = generate_params(address)
    if params["streetAddress"] != "":
        res = requests.post(api_url, json=params)
        try:
            res_body = res.json()
            results = res_body["result"]
            if isinstance(results, list):
                response = choose_best_location(results)
            else: response = results
            location = {
                "building_name": title_case(response["buildingName"]),
                "street_number": get_street_number(response),
                "street_name": title_case(response["streetName"]),
                "street_type": title_case(response["streetType"]),
                "suburb": title_case(response["suburb"]),
                "state": response["state"],
                "post_code": response["postCode"],
                "latitude": deep_get(response, "location", "lat"),
                "longitude": deep_get(response, "location", "lon"),
                "confidence": res_body["confidence"],
                "location_type": "geocoded",
            }
        except:
            location = {
                "street_number": address.get("street_number", None),
                "street_name": address.get("street_name", None),
                "street_type": address.get("street_type", None),
                "suburb": params.get("suburb", None),
                "state": params.get("state", None),
                "location_type": "parsed",
            }
    else: 
        location = {
            "street_number": address.get("street_number", None),
            "street_name": address.get("street_name", None),
            "street_type": address.get("street_type", None),
            "suburb": params.get("suburb", None),
            "state": params.get("state", None),
            "location_type": "parsed",
        }
    return location


def extract_location(location_text: str) -> Location:
    """Parse and geocode location from text using OSM Nominatim."""
    address = parse_address(location_text)
    if not address: return {}
    location = geocode_address(address)
    return location


#TODO: Convert to Async requests
def extract_locations(series: Series, sample_size: int = 5, **kwargs: Any) -> DataFrame:
    locations = []
    if sample_size != 0: series = series.sample(n=sample_size)
    for text in tqdm(series, desc="Detecting Locations"):
        location = extract_location(text)
        locations.append(location)
    locations = pd.DataFrame.from_records(locations, index=series.index)
    return locations


##########################################################
# Main


def main():
    pass
    

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()


##########################################################
