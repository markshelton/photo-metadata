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
from pandas import Series, DataFrame

Schema = Any #sqlalchemy - base type
ImageType = Any #OpenCV
Rectangle = Any #dlib
BoundingBox = Any #dlib
Shape = Any #dlib
TFSession = Any #tf
Face = Any
File = Any

##########################################################
# Local Types

Label = int

Match = Dict[str, str]
Features = List[Real]
ParsedRecord = Dict[str, Any]
JSONType = Union[List[ParsedRecord], ParsedRecord]
PymarcParser = Callable[[PymarcRecord, KwArg(Any)], List[ParsedRecord]]
Parser = Callable[[Series, KwArg(Any)], DataFrame]

Address = Dict[str, Optional[str]]
Location = Dict[str, Optional[str]]

Tag = TypedDict('Tag', {"field": str, "subfield": str})
Size = TypedDict("Size", {"width": int, "height": int})
Dates = TypedDict("Dates", {"start": Optional[Date], "end": Optional[Date]})

DatasetRecord = TypedDict("DatasetRecord", {"features": Features, "label": Label, "path": FilePath}, total=False)
Dataset = List[DatasetRecord]

##########################################################