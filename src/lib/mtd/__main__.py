##########################################################
# Standard Library Imports

##########################################################
# Third Party Imports

##########################################################
# Local Imports

from thickshake.mtd.database import load_database, dump_database
from thickshake.mtd.reader import read_json, read_hdf5, read_marc21, read_marcxml, read_csv
from thickshake.mtd.writer import write_json, write_hdf5, write_marc21, write_marcxml, write_csv
from thickshake.utils import get_file_type
from thickshake.types import *

##########################################################
# Constants

class FileType(Enum):
    JSON = ".json"
    HDF5 = ".hdf5"
    MARC21 = ".marc"
    MARCXML = ".xml"
    CSV = ".csv"

##########################################################
# Functions


# Import metadata files from any format to RDBMS
def import_metadata(input_file: FilePath, db_config: DBConfig) -> None:
    if not os.path.exists(input_file): raise IOError
    file_type = get_file_type(output_file) #DONE
    if file_type == FileType.JSON:
        records = read_json(input_file) #TODO
    elif file_type == FileType.HDF5:
        records = read_hdf5(input_file) #TODO
    elif file_type == FileType.MARC21:
        records = read_marc21(input_file) #TODO
    elif file_type == FileType.MARCXML:
        records = read_marcxml(input_file) #DONE
    elif file_type == FileType.CSV:
        records = read_csv(input_file) #TODO
    else: raise NotImplementedError
    load_database(records, db_config) #TODO


# Export metadata records from RDBMS to any format
def export_metadata(output_file: FilePath, db_config: DBConfig) -> None:
    if os.path.exists(output_file): raise IOError
    records = dump_database(db_config) #DONE
    file_type = get_file_type(output_file) #DONE
    if file_type == FileType.JSON:
        write_json(records, output_file) #DONE
    elif file_type == FileType.HDF5:
        write_hdf5(records, output_file) #DONE
    elif file_type == FileType.MARC21:
        write_marc21(records, output_file) #TODO
    elif file_type == FileType.MARCXML:
        write_marcxml(records, output_file) #TODO
    elif file_type == FileType.CSV:
        write_csv(records, output_file) #DONE
    else: raise NotImplementedError


##########################################################
# Functions

