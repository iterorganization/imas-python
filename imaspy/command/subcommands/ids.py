# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""Command-line tools provided with IMASPy."""
import argparse
import logging
import os.path
from pathlib import Path

import click

import imaspy.util
from imaspy.dd_zip import latest_dd_version
from imaspy.ids_defs import ASCII_BACKEND, MDSPLUS_BACKEND

logger = logging.getLogger(__name__)


# TODO: these tools should be updated for AL5 to accept URIs instead of file paths


@click.command("ids_info")
@click.option("-n", "--name")
@click.option("--version")
@click.option("--xml_path")
@click.argument("paths", nargs=-1, type=click.Path(dir_okay=False, path_type=Path))
def info(name, version, xml_path, paths):
    """Print info about IDSes provided by path."""
    for file in paths:
        if not file.exists():
            logger.error("File %s not found", file)
        else:
            ids = open_from_file(file, version=version, xml_path=xml_path)

            print(ids.metadata.name)
            imaspy.util.print_tree(ids.ids_properties, hide_empty_nodes=False)


@click.command("ids_convert")
def convert():
    """Convert an IMAS data structure (all idses or specific ones) to
    a specific or the latest version. Can also provide info about
    which version was used to create a specific IDS"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        help="file to open",
        type=Path,
    )
    parser.add_argument(
        "version",
        default=latest_dd_version(),
        help="version to convert to (default {!s})".format(latest_dd_version()),
        nargs="?",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="verbosity (repeat for more output)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="print only errors",
    )
    args = parser.parse_args()

    if args.quiet:
        logger.setLevel(logging.ERROR)
    else:
        if args.verbose == 0:
            logger.setLevel(logging.WARNING)
        elif args.verbose == 1:
            logger.setLevel(logging.INFO)
        elif args.verbose == 2:
            logger.setLevel(logging.DEBUG)

    if not os.path.isfile(args.file):
        logger.error("File %s not found", args.file)
    else:
        ids = open_from_file(args.file, args.version)

        # now switch the backend to the requested version
        ids._read_backend_xml(version=args.version)

        # and write the IDS
        ids.put()


def format_node(el):
    return el.metadata.name


def format_node_value(el):
    if isinstance(el, imaspy.ids_primitive.IDSPrimitive):
        return "%- 22s%s = %s" % (el.metadata.name, "    " * (6 - el.depth), el.value)
    return el.metadata.name


def has_value(el):
    return el.has_value


def all_children(el):
    return el.__iter__()


def nonempty_children(el):
    return filter(has_value, el)


@click.command("ids_print")
@click.argument("paths", nargs=-1, type=click.Path(dir_okay=False, path_type=Path))
@click.option("--all", "-a", help="Show all values (including empty/default).")
def tree(paths, all):
    """Pretty-print a tree of non-default variables."""
    for path in paths:
        ids = open_from_file(path)

        try:
            imaspy.util.print_tree(ids, not all)
        except BrokenPipeError:
            pass


ENDINGS = {
    ".ids": ASCII_BACKEND,
    ".characteristics": MDSPLUS_BACKEND,
    ".tree": MDSPLUS_BACKEND,
    ".datafile": MDSPLUS_BACKEND,
}


def open_from_file(file, version=None, xml_path=None):
    """Given a filename as an argument, try to open that with the latest version."""

    backend = ENDINGS[file.suffix]
    if backend == ASCII_BACKEND:
        try:
            db_name, shot, run, ids_name = file.stem.split("_", maxsplit=3)
        except IndexError as ee:
            raise ValueError("Could not parse ASCII backend filename %s" % file) from ee
    elif backend == MDSPLUS_BACKEND:
        raise ValueError("Could not parse MDSplus backend filename %s" % file)
    else:
        raise ValueError("Could not identify backend from filename %s" % file)

    entry = imaspy.DBEntry(
        backend, db_name, int(shot), int(run), dd_version=version, xml_path=xml_path
    )
    entry.open(options=f"-prefix {file.parent}/")  # ASCII backend to direct to path
    return entry.get(ids_name)


def _default_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        help="file to open",
        type=Path,
        nargs="+",
    )
    parser.add_argument(
        "--name",
        help="ids to select",
    )
    # TODO: also support URLs
    return parser
