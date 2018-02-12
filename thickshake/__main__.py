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
# Local Imports

from thickshake.logger import setup_logging
from thickshake.cli import cli

##########################################################
# Functions

setup_logging() # load logger configuration
cli() # invoke command line interface

##########################################################
