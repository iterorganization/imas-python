# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Main CLI entry point """
from importlib.metadata import version, PackageNotFoundError

import click


@click.command()
def print_version():
    """Print the version number of IMASPy"""
    try:
        __version__ = version("imaspy")
    except PackageNotFoundError:
        click.echo("Package is not installed")
    click.echo(__version__)


if __name__ == "__main__":
    print_version()
