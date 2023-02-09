from click.testing import CliRunner
import pytest

from importlib.metadata import version
from imaspy import __version__
from imaspy.command.cli import print_hello_world, print_version

@pytest.mark.cli
def test_hello_world():
    runner = CliRunner()
    result = runner.invoke(print_hello_world)
    assert result.exit_code == 0
    assert result.output == 'Hello world!\n'

@pytest.mark.cli
def test_hello_world():
    imaspy_version = version("imaspy")
    runner = CliRunner()
    result = runner.invoke(print_version)
    assert result.exit_code == 0
    assert result.output == f"{imaspy_version}\n"
