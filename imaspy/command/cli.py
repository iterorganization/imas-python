# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" Main CLI entry point """

import logging
import sys
from contextlib import ExitStack
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
from imaspy.command.timer import Timer
from imaspy.exception import UnknownDDVersion

logger = logging.getLogger(__name__)


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
    logger.debug("Suppressed traceback:", exc_info=(type_, value, tb))
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

    with imaspy.DBEntry(uri, "r") as dbentry:
        ids_obj = dbentry.get(ids, occurrence, autoconvert=False)
        imaspy.util.print_tree(ids_obj, not print_all)


@cli.command("convert")
@click.argument("uri_in")
@click.argument("dd_version")
@click.argument("uri_out")
@click.option("--ids", default="*", help="Specify which IDS to convert")
@click.option("--occurrence", default=-1, help="Specify which occurrence to convert")
@click.option("--quiet", "-q", is_flag=True, help="Suppress progress output")
@click.option("--timeit", is_flag=True, help="Show timing information")
def convert_ids(uri_in, dd_version, uri_out, ids, occurrence, quiet, timeit):
    """Convert an IDS to the target DD version.

    \b
    uri_in      URI of the input Data Entry.
    dd_version  Data dictionary version to convert to. Can also be the path to an
                IDSDef.xml to convert to a custom/unreleased DD version.
    uri_out     URI of the output Data Entry.
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

    # Use an ExitStack to avoid three nested with-statements
    with ExitStack() as stack:
        entry_in = stack.enter_context(imaspy.DBEntry(uri_in, "r"))
        entry_out = stack.enter_context(imaspy.DBEntry(uri_out, "x", **version_params))

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

        # Create progress bar and task
        columns = (
            TimeElapsedColumn(),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[progress.description]{task.description}"),
            SpinnerColumn("simpleDots", style="[white]"),
        )
        progress = stack.enter_context(Progress(*columns, disable=quiet))
        task = progress.add_task("Converting", total=len(idss_with_occurrences) * 3)
        # Create timer for timing get/convert/put
        timer = Timer("Operation", "IDS/occurrence")

        # Convert all IDSs
        for ids_name, occurrence in idss_with_occurrences:
            name = f"[bold green]{ids_name}[/][green]/{occurrence}[/]"

            progress.update(task, description=f"Reading {name}")
            with timer("Get", name):
                ids = entry_in.get(ids_name, occurrence, autoconvert=False)

            progress.update(task, description=f"Converting {name}", advance=1)
            # Explicitly convert instead of auto-converting during put. This is a bit
            # slower, but gives better diagnostics:
            if ids._dd_version == entry_out.dd_version:
                ids2 = ids
            else:
                with timer("Convert", name):
                    ids2 = imaspy.convert_ids(ids, None, factory=entry_out.factory)

            # Store in output entry:
            progress.update(task, description=f"Storing {name}", advance=1)
            with timer("Put", name):
                entry_out.put(ids2, occurrence)

            # Update progress bar
            progress.update(task, advance=1)

    # Display timing information
    if timeit:
        console.Console().print(timer.get_table("Time required per IDS"))


if __name__ == "__main__":
    cli()
