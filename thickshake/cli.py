# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
"""
##########################################################
# Standard Library Imports

import configparser
import os

##########################################################
# Third Party Imports

import click
from click_help_colors import HelpColorsGroup, HelpColorsCommand

##########################################################
# Local Imports

from thickshake import main
from thickshake.datastore import Store
from thickshake.metadata import metadata
from thickshake.parser import parser
from thickshake.image import image

##########################################################
# Typing Configuration

FilePath = str 
DirPath = str

##########################################################
# Constants

CURRENT_FILE_DIR, _ = os.path.split(__file__)
CONFIG_FILE = "%s/settings.ini" % (CURRENT_FILE_DIR)

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
parser.read(CONFIG_FILE)
default_map = parser.as_dict()
context_settings = dict(default_map=default_map, ignore_unknown_options=True, allow_extra_args=True)
store = Store()

##########################################################
# Functions


@click.group(
    cls=HelpColorsGroup,
    help_headers_color='yellow',
    help_options_color='green',
    context_settings=context_settings,
)
@click.option("-v/-q", "--verbose/--quiet", default=False, help="logging")
@click.option("-f", "--force", is_flag=True, help="overwrite existing files")
@click.option("-n", "--dry-run", is_flag=True, help="run without creating files")
@click.option("-d", "--display", is_flag=True, help="display images in GUI")
@click.option("-s", "--sample", type=int, default=20, help="perform on random sample")
@click.pass_context
def cli(ctx, **kwargs):
    """Functions for improving library catalogues."""
    ctx.obj = kwargs


@cli.command(context_settings=context_settings)
@click.argument("input_metadata_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("output_metadata_file", required=False, type=click.Path(exists=True, dir_okay=False))
@click.argument("input_image_dir", required=False, type=click.Path(exists=True, file_okay=False))
@click.option("--diff", is_flag=True, help="generate change log from metadata files")
@click.pass_context
def augment(ctx, input_metadata_file: FilePath, output_metadata_file: FilePath, input_image_dir: DirPath, diff: bool) -> None:
    """Applies techniques to improve the metadata."""
    parser.augment_metadata(input_metadata_file, output_metadata_file, input_image_dir, diff, **ctx.obj)


@cli.command(context_settings=context_settings)
@click.argument("input_metadata_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("output_metadata_file", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def convert(ctx, input_metadata_file: FilePath, output_metadata_file: FilePath) -> None:
    """Converts metadata between file formats."""
    marc.convert_metadata(input_metadata_file, output_metadata_file, **ctx.obj)


@cli.command(context_settings=context_settings)
@click.argument("input_image_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("output_image_dir", required=False, type=click.Path(exists=True, file_okay=False))
@click.option("--func", type=click.Choice(["face", "caption", "text", "all"]), default="all", multiple=True, help="Image processing function")
@click.pass_context
def process(ctx, func: str, input_image_dir: DirPath, output_image_dir: DirPath) -> None:
    """Performs processing on the images."""
    input_images = [cv2.imread(image_file) for image_file in input_image_dir]
    if "all" in func: func = ["face", "caption", "text"]
    if "face" in func: image.extract_faces(input_images, output_image_dir, **ctx.obj)
    if "text" in func: image.read_text(input_images, output_image_dir, **ctx.obj)
    if "caption" in func: image.caption_image(input_images, output_image_dir, **ctx.obj)


@cli.command(context_settings=context_settings)
@click.argument("input_metadata_file", required=False, type=click.Path(exists=True, dir_okay=False))
@click.argument("output_metadata_file", required=False, type=click.Path(exists=True, dir_okay=False))
@click.option("--func", type=click.Choice(["date", "location", "link", "all"]), default="all", multiple=True, help="Metadata parsing function")
@click.pass_context
def parse(ctx, func: str, input_metadata_file: DirPath, output_metadata_file: DirPath) -> None:
    """Performs parsing on the metadata."""
    if "all" in func: func = ["date", "location", "link"]
    if "date" in func: parser.parse_dates(input_metadata_file, **ctx.obj)
    if "location" in func: parser.parse_locations(input_metadata_file, **ctx.obj)
    if "link" in func: parser.parse_links(input_metadata_file, **ctx.obj)
    metadata.export_database(output_metadata_file, **ctx.obj)


##########################################################
