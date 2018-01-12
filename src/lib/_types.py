##########################################################
# Built-in Types

from typing import (
    List, Optional, NewType, Dict, Iterator,
    IO, Union, Callable, Any, Pattern, Tuple
)
from mypy_extensions import TypedDict, KwArg

##########################################################
# External Types

import datetime
import pymarc
import sqlalchemy.engine
import sqlalchemy.orm
import sqlalchemy.ext
import numbers
import tensorflow as tf
import numpy as np

Date = datetime.date
Record = pymarc.Record
Field = pymarc.Field
Engine = sqlalchemy.engine.Engine
Session = sqlalchemy.orm.Session
Tensor = tf.Tensor
Array = np.array
Real = numbers.Real
Schema = Any #sqlalchemy - base type
Image = Any #OpenCV
Rectangle = Any #dlib
BoundingBox = Any #dlib
Shape = Any #dlib
TFSession = Any #tf

##########################################################
# Local Types

FilePath = str
DirPath = str
File = IO[str]
Match = Dict[str, str]
ParsedRecord = Dict[str, Any]
JSONType = Union[List[ParsedRecord], ParsedRecord]
Tag = TypedDict('Tag', {"field": str, "subfield": str})
Dates = TypedDict("Dates", {"start": Optional[Date], "end": Optional[Date]})
Size = TypedDict("Size", {"width": int, "height": int})
Location = TypedDict("Location", {
    "latitude": float, "longitude": float, "bb_size": float, "query": str, "address": str
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
Face = Any
Features = List[Real]
Label = int
DatasetRecord = TypedDict("DatasetRecord", {
    "features": Features, "label": Label, "path": FilePath
    }, total=False
)
Dataset = List[DatasetRecord]
