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
import urllib.request
import urllib.parse
from envparse import env

##########################################################
# Third Party Imports

import geopy.distance

##########################################################
# Local Imports

from thickshake.types import *

##########################################################
# Environmental Variables

CURRENT_FILE_DIR, _ = os.path.split(__file__)
MTD_LOC_STREET_TYPES_FILE = env.str("MTD_LOC_STREET_TYPES_FILE", default="%s/deps/aus_street_types.csv" % (CURRENT_FILE_DIR)) # type: FilePath
MTD_LOC_SUBURB_NAMES_FILE = env.str("MTD_LOC_SUBURB_NAMES_FILE", default="%s/deps/wa_suburb_names.csv" % (CURRENT_FILE_DIR)) # type: FilePath
MTD_LOC_ADDRESS_STOP_WORDS_FILE = env.str("MTD_LOC_ADDRESS_STOP_WORDS_FILE", default="%s/deps/stop_words.csv" % (CURRENT_FILE_DIR)) # type: FilePath

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

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
    return [match.groupdict() for match in compiled_regex.finditer(target_text)]


##########################################################
# Functions


def clean_up_addresses(address_matches: List[Match]) -> Optional[Address]:
    if not address_matches: return None
    address_dict = address_matches[0]
    address = Address(
        street_number=address_dict["street_number"],
        street_name=address_dict["street_name"],
        street_type=address_dict["street_type"],
        suburb_name=address_dict["suburb_name"],
        state="Western Australia",
        country="Australia"
    )
    return address


def parse_structured_address(location_text: str, street_types_file: FilePath, suburb_names_file: FilePath) -> Optional[Address]:
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
    address_clean = clean_up_addresses(addresses)
    return address_clean


def parse_keywords_from_address(location_text: str, stop_words_file: FilePath) -> List[str]:
    stop_words = prepare_search_string(stop_words_file)
    re_keywords = re.compile(
        r'(?P<keywords>(?:\s*(?!\b{0}\b)\b(?:[A-Z][a-z]+)\b)+)'.format(stop_words)
    )
    keywords_matches = get_matches_from_regex(re_keywords, location_text)
    keywords_list = [match["keywords"].strip() for match in keywords_matches]
    return keywords_list


def parse_address(location_text: str) -> Optional[Address]:
    address = parse_structured_address(location_text, MTD_LOC_STREET_TYPES_FILE, MTD_LOC_SUBURB_NAMES_FILE)
    if address is None: return None
    keywords_list = parse_keywords_from_address(location_text, MTD_LOC_ADDRESS_STOP_WORDS_FILE)
    if address["street_name"] is not None and address["street_type"] is not None:
        keywords_list.extend([address["street_name"] + " " + address["street_type"]])
    keywords_list_unique = set(keywords_list) - set(address.values())
    address["keywords"] = list(keywords_list_unique)
    return address


def create_structured_params(address: Address) -> str:
    params_dict = {}
    if address["street_number"]:
        params_dict["street"] = "{0} {1} {2}".format(
            address["street_number"], address["street_name"], address["street_type"]
        )
    else:
        params_dict["street"] = "{0} {1}".format(address["street_name"], address["street_type"])
    params_dict["suburb"] = address["suburb_name"]
    params_dict["state"] = address["state"]
    params_dict["country"] = address["country"]
    params = urllib.parse.urlencode(params_dict)
    return params


def create_unstructured_params_list(address: Address) -> List[str]:
    params_list = []
    for keyword in address["keywords"]:
        params_dict = {}
        params_dict["q"] = "{0} {1} {2} {3}".format(
            keyword, address["suburb_name"], address["state"], address["country"]
        )
        params = urllib.parse.urlencode(params_dict)
        params_list.append(params)
    return params_list


def generate_queries(address: Address) -> List[str]:
    queries = []
    url = "http://nominatim.openstreetmap.org/search?format=jsonv2&"
    if address["street_name"] and address["street_type"]:
        params = create_structured_params(address)
        queries.append(url + params)
    else:
        params_list = create_unstructured_params_list(address)
        for params in params_list:
            queries.append(url + params)
    return queries


def calculate_bounding_box_size(bb_coords: List[float]) -> float:
    """Calculate Bounding Box Size of GPS Location, using Vincenty algorithm (in km)."""
    return geopy.distance.vincenty((bb_coords[0], bb_coords[2]), (bb_coords[1], bb_coords[3])).km


def geocode_addresses(query: str) -> List[Location]:
    locations = []
    try:
        res = urllib.request.urlopen(query)
        res_body = res.read().decode()
        response = [json.loads(res_body)[0]]
        #TODO: use multiple results with choose_best_location
        for location_raw in response:
            location = Location(
                address=location_raw["display_name"],
                latitude=location_raw["lat"],
                longitude=location_raw["lon"],
                bb_size=calculate_bounding_box_size(location_raw["boundingbox"]),
                query=query
            )
        locations.append(location)
    except BaseException:
        pass
    return locations


def choose_best_location(coordinates_list: List[Location]) -> Optional[Location]:
    """Choose best coordinates from list based on smallest bounding box."""
    if not coordinates_list: return None
    best_coords = min(coordinates_list, key=lambda x: x.get('bb_size'))
    return Location(best_coords)


#TODO: Convert to Async requests
def extract_location_from_text(location_text: str) -> Optional[Location]:
    """Parse and geocode location from text using OSM Nominatim."""
    parameterised_address = parse_address(location_text)
    if not parameterised_address: return None
    queries = generate_queries(parameterised_address)
    locations_all = []
    for query in queries:
        locations = geocode_addresses(query)
        locations_all.extend(locations)
    location = choose_best_location(locations_all)
    return location


##########################################################
