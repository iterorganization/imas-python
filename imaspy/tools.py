"""Command-line tools provided with IMASPy."""

import argparse
import logging
import os.path
import pathlib

import numpy as np

import imaspy
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

            print("% 22s = %s" % ("name", ids._name))

            def pr(a):
                print("% 22s = %s" % (a._name, a.value))

            ids.ids_properties.visit_children(pr, leaf_only=True)


def convert():
    """Convert an IMAS data structure (all idses or specific ones) to
    a specific or the latest version. Can also provide info about
    which version was used to create a specific IDS"""
    raise NotImplementedError()


def tree_print(a):
    """Pretty-print an IDS tree"""
    if isinstance(a, imaspy.ids_primitive.IDSPrimitive):
        if not np.array_equal(a.value, a._default):
            print(
                "%s- %- 24s%s = %s"
                % ((a.depth - 1) * "  ", a._name, (6 - a.depth) * "  ", a.value)
            )
    else:
        print("%s- %s" % ((a.depth - 1) * "  ", a._name))


def tree():
    """Pretty-print a tree of non-default variables."""
    args = _default_parser().parse_args()

    try:
        for file in args.file:
            if not os.path.isfile(file):
                logger.error("File %s not found", file)
            else:
                ids = open_from_file(file)

                if args.name and ids._name != args.name:
                    ids = ids[args.name]

            ids.visit_children(tree_print)
    except BrokenPipeError:
        pass


ENDINGS = {
    ".ids": ASCII_BACKEND,
    ".characteristics": MDSPLUS_BACKEND,
    ".tree": MDSPLUS_BACKEND,
    ".datafile": MDSPLUS_BACKEND,
}


def open_from_file(file):
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
        int(shot), int(run)
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
