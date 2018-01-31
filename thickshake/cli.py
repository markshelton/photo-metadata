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

from thickshake.helpers import convert_file_type

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
    @click.option("-q", "--quarantine", is_flag=True, help="run without import/export")
    @click.option("-g", "--graphics", is_flag=True, help="display images in GUI")
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


def _process(func: str, input_image_dir: DirPath, output_image_dir: DirPath, **kwargs: Any) -> None:
    from thickshake.image import image
    if "all" in func: func = ["face", "caption", "text"]
    if "face" in func: image.extract_faces(input_image_dir, output_image_dir, **kwargs)
    if "text" in func: image.read_text(input_image_dir, output_image_dir, **kwargs)
    if "caption" in func: image.caption_image(input_image_dir, output_image_dir, **kwargs)


def _parse(func: str,  **kwargs: Any) -> None:
    from thickshake.parser import parser
    if "all" in func: func = ["date", "location", "link"]
    if "date" in func: parser.parse_dates( **kwargs)
    if "location" in func: parser.parse_locations( **kwargs)
    if "link" in func: parser.parse_links( **kwargs)


##########################################################
# Commands


@cli.command(context_settings=context_settings)
@click.option("-i","--input-metadata-file", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("-o","--output-metadata-file", required=False, type=click.Path(dir_okay=False))
@click.option("-t","--output-metadata-type", required=False, type=click.Choice([".json", ".xml", ".marc"]), default=".marc", prompt='Output Types | Options: [.json, .xml, .marc] | Default:')
@common_params
def convert(input_metadata_file: FilePath, output_metadata_file: FilePath=None, output_metadata_type: str=None, **kwargs: Any) -> None:
    """Converts metadata between file formats."""
    from thickshake.marc import marc
    if output_metadata_type is not None:
        marc.convert_metadata(input_metadata_file, output_metadata_type=output_metadata_type, **kwargs)
    else: marc.convert_metadata(input_metadata_file, output_metadata_file=output_metadata_file, **kwargs)


@cli.command(context_settings=context_settings)
@click.option("-i", "--input-metadata-file", required=True, type=click.Path(exists=True, dir_okay=False))
@common_params
def load(input_metadata_file: FilePath, **kwargs: Any) -> None:
    """Imports metadata into database."""
    from thickshake.marc import marc
    marc.import_metadata(input_metadata_file, **kwargs)


@cli.command(context_settings=context_settings)
def inspect() -> None:
    """Inspects state of database."""
    from thickshake.storage.database import Database
    database = Database()
    database.inspect_database()


@cli.group(context_settings=context_settings)
@common_params
def export(**kwargs: Any) -> None:
    """[WIP] Exports metadata from database."""


@export.command(name="marc", context_settings=context_settings)
@click.option("-o", "--output-metadata-file", required=False, type=click.Path(exists=False, dir_okay=False))
@click.option("-t","--output-metadata-type", required=False, type=click.Choice([".json", ".xml", ".marc"]), default=".marc", prompt='Output Types | Options: [.json, .xml, .marc] | Default:')
@click.option("-i", "--input-metadata-file", required=False, type=click.Path(exists=True, dir_okay=False))
@click.option("-d", "--diff", required=False, is_flag=True, help="generate log of changes to metadata file")
@common_params
def export_marc(output_metadata_file: FilePath, output_metadata_type: str, input_metadata_file: FilePath, diff: bool, **kwargs: Any) -> None:
    """[TODO] Exports a marc file (for catalogues)."""
    assert output_metadata_file is not None or output_metadata_type is not None
    from thickshake.marc import marc
    if output_metadata_type is not None:
        output_metadata_file = convert_file_type(output_metadata_file, output_metadata_type)
    marc.export_metadata(output_metadata_file, input_metadata_file, diff, **kwargs)


@export.command(name="dump", context_settings=context_settings)
@click.option("-o", "--output-dump-file", required=True, type=click.Path(exists=False, dir_okay=False))
@click.option("-t","--output-dump-type", required=False, type=click.Choice([".csv", ".json", ".hdf5"]), default=".csv", prompt='Output Types | Options: [.csv, .json, .hdf5] | Default:')
@common_params
def export_dump(output_dump_file: FilePath, output_dump_type: str, **kwargs: Any) -> None:
    """Exports a flat file (for other systems)."""
    assert output_dump_type is not None or output_dump_file is not None
    from thickshake.storage import writer
    if output_dump_type is not None:
        output_dump_file = convert_file_type(output_dump_file, output_dump_type)
    writer.export_flat_file(output_dump_file, **kwargs)


@cli.command(context_settings=context_settings)
@click.option("-im", "--input-metadata-file", required=False, type=click.Path(exists=True, dir_okay=False))
@click.option("-om", "--output-metadata-file", required=False, type=click.Path(exists=False, dir_okay=False))
@click.option("-ii", "--input-image-dir", required=False, type=click.Path(exists=True, file_okay=False))
@click.option("-oi", "--output-image-dir", required=False, type=click.Path(exists=False, file_okay=False))
@click.option("-d", "--diff", required=False, is_flag=True, help="generate log of changes to metadata file")
@click.option("-mf", "--metadata-func", type=click.Choice(["date", "location", "link", "all", "none"]), default="all", prompt='Metadata Parsing | Options: [date, location, link, all, none] | Default:', help="Metadata parsing function")
@click.option("-if", "--image-func", type=click.Choice(["face", "caption", "text", "all", "none"]), default="none", prompt='Image Processing | Options: [face, caption, text, all, none] | Default:', help="Image processing function")
@common_params
def augment(input_metadata_file: FilePath, output_metadata_file: FilePath, input_image_dir: DirPath, output_image_dir: DirPath, quarantine: bool, diff: bool, metadata_func: str, image_func: str, **kwargs: Any) -> None:
    """[TODO] Applies functions to augment metadata."""
    from thickshake.marc import marc
    if not quarantine: marc.import_metadata(input_metadata_file, **kwargs)
    _parse(metadata_func, **kwargs)
    _process(image_func, input_image_dir, output_image_dir, **kwargs)
    if not quarantine: marc.export_metadata(output_metadata_file, input_metadata_file, diff, **kwargs)

@cli.command(context_settings=context_settings)
@click.option("-i", "--input-image-dir", required=True, type=click.Path(exists=True, file_okay=False))
@click.option("-o", "--output-image-dir", required=False, type=click.Path(exists=False, file_okay=False))
@click.option("-if", "--func", type=click.Choice(["face", "caption", "text", "all", "none"]), default="none", prompt='Image Functions | Options: [face, caption, text, all, none] | Default:', help="Image processing function")
@common_params
def process(func: str, input_image_dir: DirPath, output_image_dir: DirPath, **kwargs: Any) -> None:
    """[TODO] Performs processing on the images."""
    _process(func, input_image_dir, output_image_dir, **kwargs)


@cli.command(context_settings=context_settings)
@click.option("-i", "--input-metadata-file", required=False, type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--output-metadata-file", required=False, type=click.Path(exists=False, dir_okay=False))
@click.option("-mf", "--func", type=click.Choice(["date", "location", "link", "all", "none"]), default="all", prompt='Parsing Functions | Options: [date, location, link, all, none] | Default:', help="Metadata parsing function")
@click.pass_context
def parse(func: str, input_metadata_file: FilePath, output_metadata_file: FilePath, quarantine: bool, **kwargs: Any) -> None:
    """[TODO] Performs parsing on the metadata."""
    _parse(func, **kwargs)
    if not quarantine: metadata.export_database(output_metadata_file, **kwargs)


##########################################################
