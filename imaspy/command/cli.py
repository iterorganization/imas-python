# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Main CLI entry point """
from importlib.metadata import version, PackageNotFoundError

import click


@click.group()
def cli():
    pass


@click.command()
def print_version():
    """Print the version number of IMASPy"""
    try:
        __version__ = version("imaspy")
    except PackageNotFoundError:
        click.echo("Package is not installed")
    click.echo(__version__)


@click.command()
def print_hello_world():
    click.echo("Hey world!")


cli.add_command(print_hello_world)
cli.add_command(print_version)

if __name__ == "__main__":
    cli()
