##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

from envparse import env

##########################################################
# Local Imports

from thickshake.utils import setup_warnings, setup_logging
from thickshake.types import *

##########################################################
# Environmental Variables


##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions

def get_possible_dates(date_string: str) -> List[Date]:
    years = re.findall(".*([1-2][0-9]{3})", date_string)
    dates = [datetime.date(year=int(year), month=1, day=1) for year in years]
    if not dates:
        dates = list(datefinder.find_dates(date_string))
    return dates


def select_date(possible_dates: List[Date], method: str = "first") -> Optional[Date]:
    if len(possible_dates) == 0: return None
    if method == "first":
        return possible_dates[0]
    elif method == "last":
        return possible_dates[-1]
    else:
        logger.error("Invalid method argument: %s. Please use 'first' or 'last'.", method)
        return None
    

def extract_date_from_text(date_text: str, method: str = "first") -> Optional[Date]:
    possible_dates = get_possible_dates(date_text)
    selected_date = select_date(possible_dates, method=method)
    return selected_date


def get_date_collection_created(record: PymarcRecord) -> Optional[Date]:
    date_created_raw = get_subfield_from_tag(record, TAG_DATE_CREATED)
    date_created_approx_raw = get_subfield_from_tag(record, TAG_DATE_CREATED_APPROX)
    if date_created_raw:
        date_created = extract_date_from_text(date_created_raw)
    elif date_created_approx_raw:
        date_created = extract_date_from_text(date_created_approx_raw)
    else:
        date_created = None
    return date_created


def split_dates(record: PymarcRecord, dates_tag: str) -> Dates:
    dates_raw = get_subfield_from_tag(record, dates_tag)
    if dates_raw is None: return Dates({"start": None, "end": None})
    dates_num = len(dates_raw.split("-"))
    if dates_num >= 2:
        date_start_raw, date_end_raw, *_ = dates_raw.split("-")
        date_start = extract_date_from_text(date_start_raw)
        date_end = extract_date_from_text(date_end_raw)
    elif dates_num == 1:
        date_start_raw = dates_raw.split("-")[0]
        date_start = extract_date_from_text(date_start_raw)
        date_end = None
    dates = Dates({"start": date_start, "end": date_end})
    return dates


def get_date(field: PymarcField, tag: str) -> Optional[Date]:
    date_text = get_subfield_from_tag(field, tag)
    if date_text is None: return None
    extracted_date = extract_date_from_text(date_text)
    return extracted_date


##########################################################
# Main

def main():
    pass

if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()

