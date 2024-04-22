import pytest
from click.testing import CliRunner

import imaspy
from imaspy.command.cli import print_version


@pytest.mark.cli
def test_imaspy_version():
    imaspy_version = imaspy.__version__
    runner = CliRunner()
    result = runner.invoke(print_version)
    assert result.exit_code == 0
    assert result.output == f"{imaspy_version}\n"
