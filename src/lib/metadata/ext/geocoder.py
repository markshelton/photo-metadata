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

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################

INPUT_STREET_TYPE_FILE = "/home/app/data/input/metadata/location/aus_street_types.csv"
INPUT_SUBURB_NAMES_FILE = "/home/app/data/input/metadata/location/wa_suburb_names.csv"
INPUT_STOP_WORDS_FILE = "/home/app/data/input/metadata/location/stop_words.csv"

##########################################################


def read_csv_to_dict(csv_file):
    with open(csv_file) as csvfile:
        reader = csv.DictReader(csvfile)
        return dict(zip(reader.fieldnames, zip(*[d.values() for d in reader])))


def make_candidate_string(candidate_list, lower=True):
    if lower:
        return "|".join(candidate_list).lower()
    else:
        return "|".join(candidate_list)


def prepare_search_strings():
    street_type_dict = read_csv_to_dict(INPUT_STREET_TYPE_FILE)
    street_types = make_candidate_string([
        *street_type_dict["street_type"], *street_type_dict["abbreviation"]
    ])
    suburb_name_dict = read_csv_to_dict(INPUT_SUBURB_NAMES_FILE)
    suburb_names = make_candidate_string(suburb_name_dict["suburb_name"])
    stop_words_dict = read_csv_to_dict(INPUT_STOP_WORDS_FILE)
    stop_words = make_candidate_string(
        stop_words_dict["stop_word"], lower=False)
    return street_types, suburb_names, stop_words


def get_matches_from_regex(compiled_regex, target_text):
    return [m.groupdict() for m in compiled_regex.finditer(target_text)]


def clean_up_addresses(address_matches):
    address_dict = address_matches[0]
    address_dict["state"] = "Western Australia"
    address_dict["country"] = "Australia"
    if address_dict["street_type"] is None:
        address_dict["street_name"] = None
        address_dict["street_number"] = None
    return address_dict


def parse_address(location_text):
    address = {
        "street_number": None, "street_name": None,
        "street_type": None, "suburb_name": None,
        "keywords": []
    }
    street_types, suburb_names, stop_words = prepare_search_strings()

    re_main = re.compile(
        r'(?P<street_number>\d+)?\s*' +
        r'(?P<street_name>.*?)?' +
        r'(?P<street_type>\b(?:{0})\b)?,*\s*'.format(street_types) +
        r'(?P<suburb_name>\b(?:{0})\b)'.format(suburb_names), re.IGNORECASE
    )
    main_matches = get_matches_from_regex(re_main, location_text)
    if main_matches:
        main_matches = clean_up_addresses(main_matches)
        re_keywords = re.compile(
            r'(?P<keywords>(?:\s*(?!\b{0}\b)\b(?:[A-Z][a-z]+)\b)+)'.format(
                stop_words)
        )
        keywords_matches = get_matches_from_regex(re_keywords, location_text)
        if keywords_matches:
            keywords_list = [match["keywords"].strip()
                             for match in keywords_matches]
            keywords_list_unique = set(
                keywords_list) - set(main_matches.values())
            address = dict(**main_matches, keywords=list(keywords_list_unique))
        else:
            address = main_matches
    return address


def create_structured_params(street_number=None, street_name=None, street_type=None,
                             suburb_name=None, state="Western Australia", country="Australia", **kwargs):
    params_dict = {}
    if street_number:
        params_dict["street"] = "{0} {1} {2}".format(
            street_number, street_name, street_type)
    else:
        params_dict["street"] = "{0} {1}".format(street_name, street_type)
    params_dict["suburb"] = suburb_name
    params_dict["state"] = state
    params_dict["country"] = country
    params = urllib.parse.urlencode(params_dict)
    return params


def create_unstructured_params_list(keywords=None, suburb_name=None,
                                    state="Western Australia", country="Australia", countrycodes="au", **kwargs):
    params_list = []
    if keywords:
        for keyword in keywords:
            params_dict = {}
            params_dict["q"] = "{0} {1} {2} {3}".format(
                keyword, suburb_name, state, country)
            params_dict["countrycodes"] = countrycodes
            params = urllib.parse.urlencode(params_dict)
            params_list.append(params)
    return params_list


def format_nominatim_queries(address_dict):
    queries = []
    url = "http://nominatim.openstreetmap.org/search?format=jsonv2&"
    if address_dict["street_name"] and address_dict["street_type"]:
        params = create_structured_params(**address_dict)
        queries.append(url + params)
    else:
        params_list = create_unstructured_params_list(**address_dict)
        for params in params_list:
            queries.append(url + params)
    return queries


def calculate_bounding_box_size(bb_coords_list):
    return geopy.distance.vincenty(
        (bb_coords_list[0], bb_coords_list[2]),
        (bb_coords_list[1], bb_coords_list[3])).km


def geocode_addresses(queries):
    coordinates_list = []
    for query in queries:
        try:
            coordinates = {}
            res = urllib.request.urlopen(query)
            res_body = res.read().decode()
            j = json.loads(res_body)[0]
            coordinates["latitude"] = j["lat"]
            coordinates["longitude"] = j["lon"]
            coordinates["bb_size"] = calculate_bounding_box_size(
                j["boundingbox"])
            coordinates["query"] = query
            coordinates_list.append(coordinates)
        except BaseException:
            pass
    return coordinates_list


def choose_best_coordinates(coordinates_list):
    coords = {"latitude": None, "longitude": None}
    if coordinates_list:
        best_coords = min(coordinates_list, key=lambda x: x['bb_size'])
        coords = dict(
            latitude=best_coords["latitude"],
            longitude=best_coords["longitude"])
        logger.info(best_coords)
    return coords


def resolve_location(location_text):
    address_dict = parse_address(location_text)
    queries = format_nominatim_queries(address_dict)
    coordinates_list = geocode_addresses(queries)
    coordinates = choose_best_coordinates(coordinates_list)
    return coordinates

##########################################################
# One-time Scripts


INPUT_SUBURB_URL = "https://www0.landgate.wa.gov.au/maps-and-imagery/wa-geographic-names/name-history/historical-suburb-names"
OUTPUT_SUBURB_FILE = INPUT_SUBURB_NAMES_FILE


def scrape_suburbs_list(output_file):
    import urllib.request
    from bs4 import BeautifulSoup
    import csv
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
    import logging
    logging.basicConfig(level=logging.DEBUG)
    resolve_location("135 St George's Tce, Perth, 1961")
    #resolve_location("Spitfire PK481 in front of Air Force Memorial House, 207 Adelaide Terrace, Perth, 1960")
    #resolve_location("Perth from the State War Memorial in Kings Park, March 1960")
    #resolve_location("z142982PD: Christmas decorations, Barrack Street, Perth, 1974")
    # scrape_suburbs_list(OUTPUT_SUBURB_FILE)

##########################################################
