##########################################################
# Standard Library Imports

import logging

##########################################################
# Third Party Imports

from envparse import env

##########################################################
# Local Imports

from thickshake.utils import setup_logging, setup_warnings
from thickshake.types import *

##########################################################
# Constants

DB_CONFIG = {} # type: DBConfig
DB_CONFIG["drivername"] = env.str("DB_DRIVER")
DB_CONFIG["host"] = env.str("DB_HOST")
DB_CONFIG["database"] = env.str("POSTGRES_DB")
DB_CONFIG["username"] = env.str("POSTGRES_USER")
DB_CONFIG["password"] = env.str("POSTGRES_PASSWORD")

##########################################################
# Logging Configuration

logger = logging.getLogger(__name__)

##########################################################
# Functions


# 
def augment_metadata(db_config: DBConfig=DB_CONFIG, **kwargs: Any) -> None:
    pass


##########################################################
# Main


def main():
    augment_metadata(
        db_config=DB_CONFIG
    )


if __name__ == "__main__":
    setup_logging()
    setup_warnings()
    main()