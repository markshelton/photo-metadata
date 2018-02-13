# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""Command Line Interface (CLI)"""
##########################################################
# Python Compatibility

from __future__ import print_function, division, absolute_import
from builtins import dict
from future import standard_library
standard_library.install_aliases()

##########################################################
# Standard Library Imports

import configparser
import functools
import logging
import os

##########################################################
# Third Party Imports

import click
from click_help_colors import HelpColorsGroup, HelpColorsCommand
import click_log
from envparse import env

##########################################################
# Local Imports

from thickshake.utils import convert_file_type, open_file

##########################################################
# Typing Configuration

from typing import Text, Any, Callable, Dict, AnyStr, Text
FilePath = Text 
DirPath = Text

##########################################################
# Constants

CURRENT_FILE_DIR, _ = os.path.split(__file__)
CONFIG_DIR_PATH = "%s/_config" % CURRENT_FILE_DIR
CONFIG_SETTINGS_FILE = env.str("CONFIG_SETTINGS_FILE", default="%s/settings.ini" % (CONFIG_DIR_PATH))

##########################################################
# Classes


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
        return x


##########################################################
# Initializations

parser = MyParser() # create parser
parser.read(CONFIG_SETTINGS_FILE) # read config file
default_map = parser.as_dict() # convert config file to dictionary
context_settings = dict(default_map=default_map, ignore_unknown_options=True, allow_extra_args=True) 
logger = logging.getLogger()

##########################################################
# Helpers

def common_params(func):
    # type: (Callable) -> Any
    """Provides shared parameters for different functions."""
    @click.option("-f", "--force", is_flag=True, help="overwrite existing files")
    @click.option("-d", "--dry-run", is_flag=True, help="run without writing files")
    @click.option("-g", "--graphics", is_flag=True, help="display images in GUI")
    @click.option("-s", "--sample", type=int, default=0, help="perform on random sample (default: 0 / None)")
    @click_log.simple_verbosity_option(logger)
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # type: (*Any, **Any) -> Any
        return func(*args, **kwargs)
    return wrapper


@click.group(
    cls=HelpColorsGroup,
    help_headers_color='yellow',
    help_options_color='green',
    context_settings=context_settings,
)
def cli(**kwargs):
    # type: (**Any) -> None
    """Functions for improving library catalogues."""
    click.echo_via_pager(
        """
        {program}  Copyright (C) {year}  {author}
        This program comes with ABSOLUTELY NO WARRANTY; for details type `show warranty'.
        This is free software, and you are welcome to redistribute it
        under certain conditions; type `show copyright' for details.
        """.format(program="Thickshake", year="2018", author="Mark Shelton")
    )


##########################################################
# Functions


##########################################################
# Commands


@cli.command(context_settings=context_settings)
def inspect(**kwargs):
    # type: (**Any) -> None
    """Inspects state of database."""
    from thickshake.storage import Database
    database = Database()
    database.inspect_database()


@cli.group(context_settings=context_settings)
def show(**kwargs):
    # type: (**Any) -> None
    """Show program details and licenses."""
    pass


@show.command(name="warranty", context_settings=context_settings)
def show_warranty(**kwargs):
    # type: (**Any) -> None
    """Show GNU LGPL3 warranty statement."""
    click.echo_via_pager(
        """
        THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
        APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
        HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM 'AS IS' WITHOUT WARRANTY
        OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
        THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
        PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
        IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
        ALL NECESSARY SERVICING, REPAIR OR CORRECTION.
        """
    )


@show.command(name="copyright", context_settings=context_settings)
def show_copyright(**kwargs):
    # type: (**Any) -> None
    """Show GNU LGPL3 copying permission statement."""
    click.echo_via_pager(
        """
        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU Lesser General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU Lesser General Public License for more details.

        You should have received a copy of the GNU Lesser General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
        """
    )


@show.command(name="license", context_settings=context_settings)
def show_license(**kwargs):
    # type: (**Any) -> None
    """Show full GNU LGPL3 license."""
    license_path = "%s/../LICENSE" % CURRENT_FILE_DIR
    license_text = open_file(license_path).read()
    click.echo_via_pager(license_text)


@show.command(name="readme", context_settings=context_settings)
def show_readme(**kwargs):
    # type: (**Any) -> None
    """Show Thickshake Readme document."""
    readme_path = "%s/../README.md" % CURRENT_FILE_DIR
    readme_text = open_file(readme_path).read()
    click.echo_via_pager(readme_text)


@cli.command(context_settings=context_settings)
@click.option("-i","--input-metadata-file", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("-o","--output-metadata-file", required=False, type=click.Path(dir_okay=False))
@click.option("-t","--output-metadata-type", required=False, type=click.Choice([".json", ".xml", ".marc"]), default=".marc", prompt='Output Types | Options: [.json, .xml, .marc] | Default:')
@common_params
def convert(input_metadata_file, output_metadata_file=None, output_metadata_type=None, **kwargs):
    # type: (FilePath, FilePath, AnyStr, **Any) -> None
    """Converts metadata between file formats."""
    from thickshake.interface import convert_metadata
    if output_metadata_type is not None:
        convert_metadata(input_metadata_file, output_metadata_type=output_metadata_type, **kwargs)
    else: convert_metadata(input_metadata_file, output_metadata_file=output_metadata_file, **kwargs)


@cli.command(context_settings=context_settings)
@click.option("-i", "--input-metadata-file", required=True, type=click.Path(exists=True, dir_okay=False))
@common_params
def load(input_metadata_file, **kwargs):
    # type: (FilePath, **Any) -> None
    """Imports metadata into database."""
    from thickshake.interface import import_metadata
    import_metadata(input_metadata_file, **kwargs)


##########################################################
# Export


@cli.group(context_settings=context_settings)
def export(**kwargs):
    # type: (**Any) -> None
    """Exports metadata from database."""


@export.command(name="marc", context_settings=context_settings)
@click.option("-o", "--output-metadata-file", required=False, type=click.Path(exists=False, dir_okay=False))
@click.option("-t","--output-metadata-type", required=False, type=click.Choice([".json", ".xml", ".marc"]), default=".marc", prompt='Output Types | Options: [.json, .xml, .marc] | Default:')
@click.option("-i", "--input-metadata-file", required=False, type=click.Path(exists=True, dir_okay=False))
@click.option("-p", "--partial", required=False, is_flag=True, help="output minimal fields to merge into catalogue")
@common_params
def export_marc(output_metadata_file, output_metadata_type, input_metadata_file, partial, **kwargs):
    # type: (FilePath, AnyStr, FilePath, bool, **Any) -> None
    """[WIP] Exports a marc file (for catalogues)."""
    assert output_metadata_file is not None or output_metadata_type is not None
    from thickshake.interface import export_metadata
    if output_metadata_type is not None:
        output_metadata_file = convert_file_type(output_metadata_file, output_metadata_type)
    export_metadata(output_metadata_file, input_metadata_file, partial=partial, **kwargs)


@export.command(name="dump", context_settings=context_settings)
@click.option("-o", "--output-dump-file", required=True, type=click.Path(exists=False, dir_okay=False))
@click.option("-t","--output-dump-type", required=False, type=click.Choice([".csv", ".json", ".hdf5"]), default=".csv", prompt='Output Types | Options: [.csv, .json, .hdf5] | Default:')
@common_params
def export_dump(output_dump_file, output_dump_type, **kwargs):
    # type: (FilePath, AnyStr, **Any) -> None
    """Exports a flat file (for other systems)."""
    assert output_dump_type is not None or output_dump_file is not None
    from thickshake.interface.report import export_flat_file
    if output_dump_type is not None:
        output_dump_file = convert_file_type(output_dump_file, output_dump_type)
    export_flat_file(output_dump_file, **kwargs)


##########################################################
# Augment


@cli.group(context_settings=context_settings)
def augment(**kwargs):
    # type: (**Any) -> None
    """Applies functions to augment metadata."""


@augment.command(name="run_parsers", context_settings=context_settings)
@common_params
def augment_parsers(**kwargs):
    # type: (**Any) -> None
    """Runs all metadata parsing functions."""
    from thickshake.augment import parse_locations, parse_dates, parse_links, parse_sizes
    parse_locations(**kwargs)
    parse_dates(**kwargs)
    parse_links(**kwargs)
    parse_sizes(**kwargs)


@augment.command(name="run_processors", context_settings=context_settings)
@click.option("-ii", "--input-image-dir", required=False, type=click.Path(exists=True, file_okay=False))
@click.option("-oi", "--output-image-dir", required=False, type=click.Path(exists=False, file_okay=False))
@common_params
def augment_processors(input_image_dir, output_image_dir, **kwargs):
    # type: (DirPath, DirPath, **Any) -> None
    """Runs all image processing functions."""
    from thickshake.augment import detect_faces, identify_faces, read_text, caption_images
    detect_faces(input_image_dir, output_image_dir=output_image_dir, **kwargs)
    identify_faces(input_image_dir, output_image_dir=output_image_dir, **kwargs)
    read_text(input_image_dir, output_image_dir=output_image_dir, **kwargs)
    caption_images(input_image_dir, output_image_dir=output_image_dir, **kwargs)


@augment.command(name="run_all", context_settings=context_settings)
@click.option("-ii", "--input-image-dir", required=False, type=click.Path(exists=True, file_okay=False))
@click.option("-oi", "--output-image-dir", required=False, type=click.Path(exists=False, file_okay=False))
@common_params
def augment_all(input_image_dir, output_image_dir, **kwargs):
    # type: (DirPath, DirPath, **Any) -> None
    """Runs all augment functions."""
    from thickshake.augment import (
        parse_locations, parse_dates, parse_links, parse_sizes,
        detect_faces, identify_faces, read_text, caption_images
    )
    parse_locations(**kwargs)
    parse_dates(**kwargs)
    parse_links(**kwargs)
    parse_sizes(**kwargs)
    detect_faces(input_image_dir, output_image_dir=output_image_dir, **kwargs)
    identify_faces(input_image_dir, output_image_dir=output_image_dir, **kwargs)
    read_text(input_image_dir, output_image_dir=output_image_dir, **kwargs)
    caption_images(input_image_dir, output_image_dir=output_image_dir, **kwargs)


@augment.command(context_settings=context_settings)
@click.option("-ii", "--input-image-dir", required=False, type=click.Path(exists=True, file_okay=False))
@click.option("-oi", "--output-image-dir", required=False, type=click.Path(exists=False, file_okay=False))
@common_params
def detect_faces(input_image_dir, output_image_dir, **kwargs):
    # type: (DirPath, DirPath, **Any) -> None
    """[WIP] Detects faces in images."""
    from thickshake.augment import detect_faces
    detect_faces(input_image_dir, output_image_dir=output_image_dir, **kwargs)


@augment.command(context_settings=context_settings)
@click.option("-ii", "--input-image-dir", required=False, type=click.Path(exists=True, file_okay=False))
@click.option("-oi", "--output-image-dir", required=False, type=click.Path(exists=False, file_okay=False))
@common_params
def identify_faces(input_image_dir, output_image_dir, **kwargs):
    # type: (DirPath, DirPath, **Any) -> None
    """[WIP] Identifies faces in images."""
    from thickshake.augment import identify_faces
    identify_faces(input_image_dir, output_image_dir=output_image_dir, **kwargs)


@augment.command(context_settings=context_settings)
@click.option("-ii", "--input-image-dir", required=False, type=click.Path(exists=True, file_okay=False))
@click.option("-oi", "--output-image-dir", required=False, type=click.Path(exists=False, file_okay=False))
@common_params
def read_text(input_image_dir, output_image_dir, **kwargs):
    # type: (DirPath, DirPath, **Any) -> None
    """[TODO] Reads text embedded in images."""
    from thickshake.augment import augment
    augment.read_text(input_image_dir, output_image_dir=output_image_dir, **kwargs)


@augment.command(context_settings=context_settings)
@click.option("-ii", "--input-image-dir", required=False, type=click.Path(exists=True, file_okay=False))
@click.option("-oi", "--output-image-dir", required=False, type=click.Path(exists=False, file_okay=False))
@common_params
def caption_images(input_image_dir, output_image_dir, **kwargs):
    # type: (DirPath, DirPath, **Any) -> None
    """[TODO] Automatically captions images."""
    from thickshake.augment import caption_images
    caption_images(input_image_dir, output_image_dir=output_image_dir, **kwargs)


@augment.command(context_settings=context_settings)
@common_params
def parse_locations(**kwargs):
    # type: (**Any) -> None
    """Parses locations from text fields."""
    from thickshake.augment import parse_locations
    parse_locations(**kwargs)


@augment.command(context_settings=context_settings)
@common_params
def parse_dates(**kwargs):
    # type: (**Any) -> None
    """Parses dates from text fields."""
    from thickshake.augment import augment
    augment.parse_dates(**kwargs)


@augment.command(context_settings=context_settings)
@common_params
def parse_links(**kwargs):
    # type: (**Any) -> None
    """Parses links from text fields."""
    from thickshake.augment import parse_links
    parse_links(**kwargs)


@augment.command(context_settings=context_settings)
@common_params
def parse_sizes(**kwargs):
    # type: (**Any) -> None
    """Parses image sizes from urls."""
    from thickshake.augment import parse_sizes
    parse_sizes(**kwargs)


##########################################################
