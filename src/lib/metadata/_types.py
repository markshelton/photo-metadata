##########################################################
# Built-in Types

from typing import (
    List, Optional, NewType, Dict, Iterator,
    IO, Union, Callable, Any, Pattern,
)
from mypy_extensions import TypedDict, KwArg

##########################################################
# External Types

import datetime
import pymarc
import sqlalchemy.engine
import sqlalchemy.orm
import sqlalchemy.ext

Date = datetime.date
Record = pymarc.Record
Field = pymarc.Field
Engine = sqlalchemy.engine.Engine
Session = sqlalchemy.orm.Session
Schema = Any

##########################################################
# Local Types

FilePath = str
DirPath = str
File = IO[str]
Match = Dict[str, str]
ParsedRecord = Dict[str, Any]
Tag = TypedDict('Tag', {"field": str, "subfield": str})
Dates = TypedDict("Dates", {"start": Optional[Date], "end": Optional[Date]})
Size = TypedDict("Size", {"width": int, "height": int})
Coordinates = TypedDict("Coordinates", {
    "latitude": float, "longitude": float, "bb_size": float, "query": str
    }, total=False
)
Address = TypedDict("Address", {
    'street_number': Optional[str], 'street_name': Optional[str], 'street_type': Optional[str],
    'suburb_name': str, 'state': str, 'country': str, 'keywords': List[Optional[str]]
    }, total=False
)
DBConfig = TypedDict("DBConfig", {
    'database': str, 'drivername': str, 'host': Optional[str],
    'username': Optional[str], 'password': Optional[str],
    }, total=False
)

