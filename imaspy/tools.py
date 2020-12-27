"""Command-line tools provided with IMASPy."""

import argparse
import logging
import os.path
import pathlib

import numpy as np
from tree_format import format_tree

import imaspy
from imaspy.dd_zip import latest_dd_version
from imaspy.ids_defs import ASCII_BACKEND, IDS_TIME_MODE_HOMOGENEOUS, MDSPLUS_BACKEND
from imaspy.logger import logger

logger.setLevel(logging.WARNING)


def info():
    """Print info about IDSes provided by path."""
    args = _default_parser().parse_args()

    for file in args.file:
        if not os.path.isfile(file):
            logger.error("File %s not found", file)
        else:
            ids = open_from_file(file)

            if args.name and ids._name != args.name:
                ids = ids[args.name]

            print(ids._name)

            print(
                format_tree(
                    ids.ids_properties,
                    format_node=format_node_value,
                    get_children=all_children,
                )
            )


def convert():
    """Convert an IMAS data structure (all idses or specific ones) to
    a specific or the latest version. Can also provide info about
    which version was used to create a specific IDS"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        help="file to open",
        type=pathlib.Path,
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
    return el._name


def format_node_value(el):
    if isinstance(el, imaspy.ids_primitive.IDSPrimitive):
        return "%- 22s%s = %s" % (el._name, "    " * (6 - el.depth), el.value)
    return el._name


def has_value(el):
    return el.has_value


def all_children(el):
    return el.__iter__()


def nonempty_children(el):
    return filter(has_value, el)


def tree():
    """Pretty-print a tree of non-default variables."""
    parser = _default_parser()
    parser.add_argument(
        "-s",
        "--structure",
        action="store_true",
        help="show structure only, don't print values",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="show all values (including empty/default)",
    )
    args = parser.parse_args()

    print_f = format_node_value
    if args.all:
        children_f = all_children
    else:
        children_f = nonempty_children

    if args.structure:
        print_f = format_node
        children_f = all_children

    for file in args.file:
        if not os.path.isfile(file):
            logger.error("File %s not found", file)
        else:
            ids = open_from_file(file)

            if args.name and ids._name != args.name:
                ids = ids[args.name]

            try:
                print(format_tree(ids, format_node=print_f, get_children=children_f))
            except BrokenPipeError:
                pass


ENDINGS = {
    ".ids": ASCII_BACKEND,
    ".characteristics": MDSPLUS_BACKEND,
    ".tree": MDSPLUS_BACKEND,
    ".datafile": MDSPLUS_BACKEND,
}


def open_from_file(file, version=None):
    """Given a filename as an argument, try to open that with the latest version."""

    backend = ENDINGS[file.suffix]
    if backend == ASCII_BACKEND:
        try:
            tree_name, shot, run, ids_name = file.stem.split("_", maxsplit=3)
        except IndexError as ee:
            raise ValueError("Could not parse ASCII backend filename %s" % file) from ee
    elif backend == MDSPLUS_BACKEND:
        raise ValueError("Could not parse ASCII backend filename %s" % file)
    else:
        raise ValueError("Could not identify backend from filename %s" % file)

    ids = imaspy.ids_root.IDSRoot(
        int(shot), int(run), version=version
    )  # use the latest version by default
    ids.open_ual_store(file.parent, tree_name, "3", backend, mode="r")

    # Fake time mode homogeneous so we can actually read the file.
    # TODO: work around that!
    ids[ids_name].ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids[ids_name].get()
    return ids[ids_name]


def _default_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        help="file to open",
        type=pathlib.Path,
        nargs="+",
    )
    parser.add_argument(
        "--name",
        help="ids to select",
    )
    # TODO: also support URLs
    return parser