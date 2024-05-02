import pytest
from click.testing import CliRunner

from imaspy.command.cli import print_version


@pytest.mark.cli
def test_imaspy_version():
    runner = CliRunner()
    result = runner.invoke(print_version)
    assert result.exit_code == 0
