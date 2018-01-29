# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
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

from thickshake.marc import marc
from thickshake.parser import parser
from thickshake.image import image

##########################################################
# Typing Configuration

from typing import Any
FilePath = str 
DirPath = str

##########################################################
# Constants

CURRENT_FILE_DIR, _ = os.path.split(__file__)
CONFIG_SETTINGS_FILE = env.str("CONFIG_SETTINGS_FILE", default="%s/settings.ini" % (CURRENT_FILE_DIR))

##########################################################
# Classes


class MyParser(configparser.ConfigParser):
    def as_dict(self):
        d = dict(self._sections)
        x = {}
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
            x.update(d[k])
        return x


##########################################################
# Initializations

parser = MyParser()
parser.read(CONFIG_SETTINGS_FILE)
default_map = parser.as_dict()
context_settings = dict(default_map=default_map, ignore_unknown_options=True, allow_extra_args=True)
logger = logging.getLogger()

##########################################################
# Helpers

def common_params(func):
    @click.option("-f", "--force", is_flag=True, help="overwrite existing files")
    @click.option("-n", "--dry-run", is_flag=True, help="run without creating files")
    @click.option("-d", "--display", is_flag=True, help="display images in GUI")
    @click.option("-s", "--sample", type=int, default=0, help="perform on random sample (default: 0 / None)")
    @click_log.simple_verbosity_option(logger)
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@click.group(
    cls=HelpColorsGroup,
    help_headers_color='yellow',
    help_options_color='green',
    context_settings=context_settings,
)
@common_params
def cli(**kwargs):
    """Functions for improving library catalogues."""
    pass


##########################################################
# Functions


@cli.command(context_settings=context_settings)
@click.option("-i", "--input-metadata-file", required=True, type=click.Path(exists=True, dir_okay=False))
@common_params
def load(input_metadata_file: FilePath, **kwargs: Any) -> None:
    """Imports metadata into database."""
    marc.import_metadata(input_metadata_file, **kwargs)


@cli.command(context_settings=context_settings)
@click.option("-o", "--output-metadata-file", required=True, type=click.Path(exists=True, dir_okay=False))
@common_params
def load(input_metadata_file: FilePath, **kwargs: Any) -> None:
    """Imports metadata into database."""
    marc.export_metadata(output_metadata_file, **kwargs)


@cli.command(context_settings=context_settings)
@click.option("-i","--input-metadata-file", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("-o","--output-metadata-file", required=True, type=click.Path(exists=True, dir_okay=False))
@common_params
def convert(input_metadata_file: FilePath, output_metadata_file: FilePath, **kwargs: Any) -> None:
    """Converts metadata between file formats."""
    marc.convert_metadata(input_metadata_file, output_metadata_file, **kwargs)


@cli.command(context_settings=context_settings)
@click.option("-i", "--input-image-dir", required=True, type=click.Path(exists=True, file_okay=False))
@click.option("-o", "--output-image-dir", required=False, type=click.Path(exists=True, file_okay=False))
@click.option("--func", type=click.Choice(["face", "caption", "text", "all"]), default="all", multiple=True, help="Image processing function")
@common_params
def process(func: str, input_image_dir: DirPath, output_image_dir: DirPath, **kwargs: Any) -> None:
    """Performs processing on the images."""
    input_images = [cv2.imread(image_file) for image_file in input_image_dir]
    if "all" in func: func = ["face", "caption", "text"]
    if "face" in func: image.extract_faces(input_images, output_image_dir, **kwargs)
    if "text" in func: image.read_text(input_images, output_image_dir, **kwargs)
    if "caption" in func: image.caption_image(input_images, output_image_dir, **kwargs)


@cli.command(context_settings=context_settings)
@click.option("-i", "--input-metadata-file", required=False, type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--output-metadata-file", required=False, type=click.Path(exists=True, dir_okay=False))
@click.option("--func", type=click.Choice(["date", "location", "link", "all"]), default="all", multiple=True, help="Metadata parsing function")
@click.pass_context
def parse(func: str, input_metadata_file: DirPath, output_metadata_file: DirPath, **kwargs: Any) -> None:
    """Performs parsing on the metadata."""
    if "all" in func: func = ["date", "location", "link"]
    if "date" in func: parser.parse_dates(input_metadata_file, **kwargs)
    if "location" in func: parser.parse_locations(input_metadata_file, **kwargs)
    if "link" in func: parser.parse_links(input_metadata_file, **kwargs)
    metadata.export_database(output_metadata_file, **kwargs)


##########################################################
