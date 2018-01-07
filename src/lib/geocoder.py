##########################################################
# Standard Library Imports

import re
import csv
import urllib.request
import urllib.parse
import json
import logging

##########################################################
# Third Party Imports

import geopy.distance

##########################################################
# Local Imports

from _types import (
    Dict, List, Pattern, Optional,
    FilePath, Match, Coordinates, Address, 
)

##########################################################
# Environmental Variables

INPUT_STREET_TYPE_FILE = "/home/app/data/input/metadata/location/aus_street_types.csv" # type: FilePath
INPUT_SUBURB_NAMES_FILE = "/home/app/data/input/metadata/location/wa_suburb_names.csv" # type: FilePath
INPUT_STOP_WORDS_FILE = "/home/app/data/input/metadata/location/stop_words.csv" # type: FilePath

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
    address = parse_structured_address(location_text, INPUT_STREET_TYPE_FILE, INPUT_SUBURB_NAMES_FILE)
    if address is None: return None
    keywords_list = parse_keywords_from_address(location_text, INPUT_STOP_WORDS_FILE)
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


def format_nominatim_queries(address: Address) -> List[str]:
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
    """Calculate Bounding Box Size of GPS Coordinates, using Vincenty algorithm (in km)."""
    return geopy.distance.vincenty((bb_coords[0], bb_coords[2]), (bb_coords[1], bb_coords[3])).km

def geocode_addresses(queries: List[str]) -> List[Coordinates]:
    coordinates_list = []
    for query in queries:
        try:
            res = urllib.request.urlopen(query)
            res_body = res.read().decode()
            j = json.loads(res_body)[0]
            coords = Coordinates(
                latitude=j["lat"],
                longitude=j["lon"],
                bb_size=calculate_bounding_box_size(j["boundingbox"]),
                query=query
            )
            coordinates_list.append(coords)
        except BaseException:
            pass
    return coordinates_list


def choose_best_coordinates(coordinates_list: List[Coordinates]) -> Optional[Coordinates]:
    """Choose best coordinates from list based on smallest bounding box."""
    if not coordinates_list: return None
    best_coords = min(coordinates_list, key=lambda x: x.get('bb_size'))
    coords = Coordinates(
        latitude=best_coords["latitude"],
        longitude=best_coords["longitude"]
    )
    return coords

#TODO: Convert to Async requests
def extract_coordinates_from_text(location_text: str) -> Optional[Coordinates]:
    """Parse and geocode location from text using OSM Nominatim."""
    address_dict = parse_address(location_text)
    if not address_dict: return None
    queries = format_nominatim_queries(address_dict)
    coordinates_list = geocode_addresses(queries)
    coordinates = choose_best_coordinates(coordinates_list)
    return coordinates


##########################################################
# One-time Scripts


INPUT_SUBURB_URL = "https://www0.landgate.wa.gov.au/maps-and-imagery/wa-geographic-names/name-history/historical-suburb-names" # type: FilePath
OUTPUT_SUBURB_FILE = INPUT_SUBURB_NAMES_FILE # type: FilePath


def scrape_suburbs_list(output_file: FilePath) -> None:
    """Scrape list of WA suburb names from Landgate web page and store in file."""
    from bs4 import BeautifulSoup
    with urllib.request.urlopen(INPUT_SUBURB_URL) as suburbs_page:
        suburbs_html = BeautifulSoup(suburbs_page, 'html.parser')
        suburb_nodes = suburbs_html.findAll('h3')
        suburbs = [suburb_node.text.strip() for suburb_node in suburb_nodes]
    with open(output_file, "w+") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["suburb_name"])
        for suburb in suburbs:
            writer.writerow([suburb])


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    extract_coordinates_from_text("135 St George's Tce, Perth, 1961")
    #resolve_location("Spitfire PK481 in front of Air Force Memorial House, 207 Adelaide Terrace, Perth, 1960")
    #resolve_location("Perth from the State War Memorial in Kings Park, March 1960")
    #resolve_location("z142982PD: Christmas decorations, Barrack Street, Perth, 1974")
    # scrape_suburbs_list(OUTPUT_SUBURB_FILE)

##########################################################
