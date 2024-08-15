import logging
import sys

import click
from packaging.version import Version
from rich.logging import RichHandler

from imaspy.backends.imas_core.imas_interface import ll_interface


def setup_rich_log_handler(quiet: bool):
    """Setup rich.logging.RichHandler on the root logger.

    Args:
        quiet: When True: set log level of the `imaspy` logger to WARNING or higher.
    """
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


def min_version_guard(al_version: Version):
    """Print an error message if the loaded AL version is too old.

    Args:
        al_version: Minimum imas_core version required for this command.
    """
    used_version = ll_interface._al_version
    if used_version >= al_version:
        return
    click.echo(
        f"This command requires at least version {al_version} of the Access Layer."
    )
    click.echo(f"The current loaded version is {used_version}, which is too old.")
    sys.exit(1)
