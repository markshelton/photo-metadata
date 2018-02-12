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

from .augment import (
    parse_locations, parse_dates, parse_links, parse_sizes,
    detect_faces, identify_faces, read_text, caption_images
)

##########################################################