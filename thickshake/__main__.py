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

from logger import setup_logging
from cli import cli

##########################################################
# Functions

setup_logging()
cli()

##########################################################
