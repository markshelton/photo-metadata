##########################################################
# Built-in Types

from typing import *
from typing import Pattern
from mypy_extensions import TypedDict, KwArg

##########################################################
# External Types

from pymarc.record import Record as PymarcRecord
from pymarc.field import Field as PymarcField
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from datetime import date as Date
from pathlib import Path as FilePath
from numbers import Real

Schema = Any #sqlalchemy - base type
Image = Any #OpenCV
Rectangle = Any #dlib
BoundingBox = Any #dlib
Shape = Any #dlib
TFSession = Any #tf
Face = Any
File = Any

##########################################################
# Local Types

DirPath = FilePath
Label = int

Match = Dict[str, str]
Features = List[Real]
ParsedRecord = Dict[str, Any]
JSONType = Union[List[ParsedRecord], ParsedRecord]
Parser = Callable[[PymarcRecord, KwArg(Any)], List[ParsedRecord]]

Tag = TypedDict('Tag', {"field": str, "subfield": str})
Size = TypedDict("Size", {"width": int, "height": int})
Location = TypedDict("Location", {"latitude": float, "longitude": float, "bb_size": float, "query": str, "address": str}, total=False)
Dates = TypedDict("Dates", {"start": Optional[Date], "end": Optional[Date]})
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

DatasetRecord = TypedDict("DatasetRecord", {"features": Features, "label": Label, "path": FilePath}, total=False)
Dataset = List[DatasetRecord]

##########################################################