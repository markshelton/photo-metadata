##########################################################
# Standard Library Imports

import datetime
import logging
import re

##########################################################
# Third Party Imports

import datefinder

##########################################################
# Local Imports

##########################################################
# Typing Configuration

from typing import List, Optional, Any, Dict
Date = Any
Dates = Dict[str, Date]

##########################################################
# Constants


##########################################################
# Initializations

logger = logging.getLogger(__name__)

##########################################################
# Functions

def get_possible_dates(date_string):
    # type: (str) -> List[Date]
    years = re.findall(".*([1-2][0-9]{3})", date_string)
    dates = [datetime.date(year=int(year), month=1, day=1) for year in years]
    if not dates:
        dates = list(datefinder.find_dates(date_string))
    return dates


def select_date(possible_dates, method="first"):
    # type: (List[Date], str) -> Optional[Date]
    if len(possible_dates) == 0: return None
    if method == "first": return possible_dates[0]
    elif method == "last": return possible_dates[-1]
    else: return None
    

def extract_date(date_text, method="first", **kwargs):
    # type: (str, str, **Any) -> Optional[Date]
    possible_dates = get_possible_dates(date_text)
    selected_date = select_date(possible_dates, method=method)
    return {"date": selected_date}


def extract_date_from_title(date_text, **kwargs):
    # type: (str, **Any) -> Optional[Date]
    try: date_text = " ".join(date_text.split(" ")[1:])
    except: pass
    extracted_date = extract_date(date_text, **kwargs).get("date", None)
    return {"date": extracted_date}

def combine_dates(fields, **kwargs):
    # type: (List[str], **Any) -> Optional[Date]
    date_created_raw = fields[0]
    date_created_approx_raw = fields[1]
    if date_created_raw: date_created = extract_date(date_created_raw).get("date", None)
    elif date_created_approx_raw: date_created = extract_date(date_created_approx_raw).get("date", None)
    else: date_created = None
    return {"date": date_created}


def split_dates(text, **kwargs):
    # type: (str, **Any) -> Dates
    if text is None: return {"start_date": None, "end_date": None}
    dates_num = len(text.split("-"))
    if dates_num >= 2:
        date_start_raw = text.split("-")[0]
        date_end_raw = text.split("-")[1]
        date_start = extract_date(date_start_raw).get("date", None)
        date_end = extract_date(date_end_raw).get("date", None)
    elif dates_num == 1:
        date_start_raw = text.split("-")[0]
        date_start = extract_date(date_start_raw).get("date", None)
        date_end = None
    return {"start_date": date_start, "end_date": date_end}


##########################################################
# Main


def main():
    pass


if __name__ == "__main__":
    main()


##########################################################
