# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Python Compatibility

from __future__ import print_function, division, absolute_import
from future import standard_library
standard_library.install_aliases()

##########################################################
# Standard Library Imports

import configparser
import ast
import os
import logging
import logging.config
import shutil
import errno

##########################################################
# Third-Party Imports

import yaml

##########################################################
# Local Imports

from thickshake.utils import Borg, open_file

##########################################################

CURRENT_FILE_DIR, _ = os.path.split(__file__)
INTERNAL_CONFIG_DIR = "%s/_config" % CURRENT_FILE_DIR
INTERNAL_CONFIG_PATH = "%s/_config/settings.ini" % CURRENT_FILE_DIR
INTERNAL_LOGGING_LOADER_PATH = "%s/_config/logging.yaml" % CURRENT_FILE_DIR

CURRENT_WORKING_DIR = os.getcwd()
EXTERNAL_CONFIG_DEFAULT_DIR =  "%s/config" % CURRENT_WORKING_DIR
EXTERNAL_CONFIG_DEFAULT_PATH = "%s/settings.ini" % EXTERNAL_CONFIG_DEFAULT_DIR


##########################################################


class Config(Borg):
    external_config_path = None

    def __init__(self, external_config_path=None, **kwargs):
        # type: (FilePath) -> None
        Borg.__init__(self)
        if self.external_config_path is None:
            if external_config_path is None: self._eject_config()
            else: self.external_config_path = external_config_path
            self.setup_logging()
            self._load_config(self.external_config_path)
            self.setup_logging(self.logging_config_path)
        self.__dict__.update(**kwargs)

    def __getattr__(self, name):
        return None

    def reload(self, external_config_path=None, **kwargs):
        self.external_config_path = None
        self.__init__(external_config_path=None, **kwargs)
        return self

    def get_dict(self):
        return self.__dict__

    def _eject_config(self):
        logger = logging.getLogger()
        try:
            shutil.copytree(INTERNAL_CONFIG_DIR, EXTERNAL_CONFIG_DEFAULT_DIR)
            self.external_config_path = EXTERNAL_CONFIG_DEFAULT_PATH
            logger.info("Ejected internal config to %s.", EXTERNAL_CONFIG_DEFAULT_DIR)
        except FileExistsError as exc:
            logger.warning("External config default directory already exists.")
            self.external_config_path = EXTERNAL_CONFIG_DEFAULT_PATH
        except OSError as exc: # python >2.5
            if exc.errno == errno.ENOTDIR:
                shutil.copy(INTERNAL_CONFIG_DIR, EXTERNAL_CONFIG_DEFAULT_DIR)
            else: raise

    def _load_config(self, external_config_path=None):
        # type: () -> None
        self._load_config_from_file(INTERNAL_CONFIG_PATH)
        self._load_config_from_file(external_config_path)
        self._load_env_config()


    def _load_config_from_file(self, config_path):
        logger = logging.getLogger()
        try:
            parser = MyParser() # create parser
            parser.read(config_path) # read config file
            default_map = parser.as_dict() # convert config file to dictionary
            self.__dict__.update(**default_map) # update object with variables from config
            logger.info("Loaded config from %s", config_path)
        except:
            logger.warning("Couldn't load config from %s", config_path)


    def _load_env_config(self):
        envs = {k.lower():v for (k,v) in os.environ.items()}
        del envs["ls_colors"]
        self.__dict__.update(**envs)


    def setup_logging(self, config_path=None):
        # type: (FilePath) -> None
        """Load logging config from file, fall back to basic config if file doesn't exist."""
        logging.captureWarnings(True)
        if config_path is not None and os.path.exists(config_path):
            with open(config_path, 'rt') as f:
                config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)
        else:
            with open(INTERNAL_LOGGING_LOADER_PATH, 'rt') as f:
                config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)


class MyParser(configparser.ConfigParser):

    def as_dict(self):
        # type: () -> Dict[AnyStr, Any]
        """Load config file to dictionary, ignoring sections."""
        d = dict(self._sections)
        x = {} # type: Dict[AnyStr, Any]
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
            x.update(d[k])
        x = {k:self.coerce_type(v) for (k,v) in x.items()}
        return x

    def coerce_type(self, value):
        try: return ast.literal_eval(value)
        except: return value
