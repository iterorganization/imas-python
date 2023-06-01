# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
""" Main CLI entry point """
from importlib.metadata import version, PackageNotFoundError

import click

import imaspy.command.subcommands.ids


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


cli.add_command(print_version)
cli.add_command(imaspy.command.subcommands.ids.info)
cli.add_command(imaspy.command.subcommands.ids.convert)
cli.add_command(imaspy.command.subcommands.ids.tree)

if __name__ == "__main__":
    cli()
