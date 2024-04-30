# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" Main CLI entry point """

import logging
import sys
from pathlib import Path

import click
from packaging.version import Version
from rich import console, traceback
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

import imaspy
from imaspy import dd_zip, imas_interface
from imaspy.exception import UnknownDDVersion


def setup_rich_log_handler(quiet: bool):
    # Disable default imaspy log handler
    imaspy_logger = logging.getLogger("imaspy")
    for handler in imaspy_logger.handlers:
        imaspy_logger.removeHandler(handler)
    # Disable any root log handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    # Install rich handler on the root logger:
    root_logger.addHandler(RichHandler())
    if quiet:  # Silence IMASPy INFO messages
        # If loglevel is less than WARNING, set it to WARNING:
        imaspy_logger.setLevel(max(logging.WARNING, imaspy_logger.getEffectiveLevel()))


def _excepthook(type_, value, tb):
    # Only display the last traceback frame:
    if tb is not None:
        while tb.tb_next:
            tb = tb.tb_next
    rich_tb = traceback.Traceback.from_exception(type_, value, tb, extra_lines=0)
    console.Console(stderr=True).print(rich_tb)


@click.group("imaspy", invoke_without_command=True)
def cli():
    # Limit the traceback to 1 item: avoid scaring CLI users with long traceback prints
    # and let them focus on the actual error message
    sys.excepthook = _excepthook


def min_version_guard(al_version: Version):
    """Print an error message if the loaded AL version is too old."""
    used_version = imas_interface.ll_interface._al_version
    if used_version >= al_version:
        return
    click.echo(
        f"This command requires at least version {al_version} of the Access Layer."
    )
    click.echo(f"The current loaded version is {used_version}, which is too old.")
    sys.exit(1)


@cli.command("version")
def print_version():
    """Print the version number of IMASPy."""
    click.echo(imaspy.__version__)


@cli.command("print")
@click.argument("uri")
@click.argument("ids")
@click.argument("occurrence", default=0)
@click.option(
    "--all",
    "-a",
    "print_all",
    is_flag=True,
    help="Also show nodes with empty/default values",
)
def print_ids(uri, ids, occurrence, print_all):
    """Pretty print the contents of an IDS.

    \b
    uri         URI of the Data Entry (e.g. "imas:mdsplus?path=testdb")
    ids         Name of the IDS to print (e.g. "core_profiles")
    occurrence  Which occurrence to print (defaults to 0)
    """
    min_version_guard(Version("5.0"))
    setup_rich_log_handler(False)

    dbentry = imaspy.DBEntry(uri, "r")
    ids_obj = dbentry.get(ids, occurrence, autoconvert=False)
    imaspy.util.print_tree(ids_obj, not print_all)


@cli.command("convert")
@click.argument("uri_in")
@click.argument("dd_version")
@click.argument("uri_out")
@click.option("--ids", default="*", help="Specify which IDS to convert")
@click.option("--occurrence", default=-1, help="Specify which occurrence to convert")
@click.option("--quiet", "-q", is_flag=True, help="Suppress progress output")
def convert_ids(uri_in, dd_version, uri_out, ids, occurrence, quiet):
    """Convert an IDS to the target DD version.

    \b
    uri_in      URI of the input Data Entry
    dd_version  Data dictionary version to convert to. Can also be the path to an
                IDSDef.xml to convert to custom/unreleased DD versions.
    uri_out     URI of the output Data Entry
    """
    min_version_guard(Version("5.1"))
    setup_rich_log_handler(quiet)

    # Check if we can load the requested version
    if dd_version in dd_zip.dd_xml_versions():
        version_params = dict(dd_version=dd_version)
    elif Path(dd_version).exists():
        version_params = dict(xml_path=dd_version)
    else:
        raise UnknownDDVersion(dd_version, dd_zip.dd_xml_versions())

    entry_in = imaspy.DBEntry(uri_in, "r")
    # Set dd_version/xml_path, so the IDSs are converted to this version during put()
    # Use "x" to prevent accidentally overwriting existing Data Entries
    entry_out = imaspy.DBEntry(uri_out, "x", **version_params)

    # First build IDS/occurrence list so we can show a decent progress bar
    ids_list = [ids] if ids != "*" else entry_out.factory.ids_names()
    idss_with_occurrences = []
    for ids_name in ids_list:
        if occurrence == -1:
            idss_with_occurrences.extend(
                (ids_name, occ) for occ in entry_in.list_all_occurrences(ids_name)
            )
        else:
            idss_with_occurrences.append((ids_name, occurrence))

    # Convert all IDSs
    columns = (
        TimeElapsedColumn(),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[progress.description]{task.description}"),
        SpinnerColumn("simpleDots", style="[white]"),
    )
    with Progress(*columns, disable=quiet) as progress:
        task = progress.add_task("Converting", total=len(idss_with_occurrences) * 3)

        for ids_name, occurrence in idss_with_occurrences:
            name = f"{ids_name}/{occurrence}"

            progress.update(task, description=f"Reading [green]{name}")
            ids = entry_in.get(ids_name, occurrence, autoconvert=False)

            progress.update(task, description=f"Converting [green]{name}", advance=1)
            # Explicitly convert instead of auto-converting during put. This is a bit
            # slower, but gives better diagnostics:
            ids2 = imaspy.convert_ids(ids, None, factory=entry_out.factory)

            # Store in output entry:
            progress.update(task, description=f"Storing [green]{name}", advance=1)
            entry_out.put(ids2, occurrence)

            # Update progress bar
            progress.update(task, advance=1)


if __name__ == "__main__":
    cli()
