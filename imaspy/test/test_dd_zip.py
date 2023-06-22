import pytest

from imaspy.dd_zip import get_dd_xml


def test_known_version():
    """Test if 3.30.0 is part of the IDSDef.zip
    Mostly this tests if IDSDef.zip has been made."""

    get_dd_xml("3.30.0")


def test_known_failing_version():
    """Test if 0.0 is not part of the IDSDef.zip"""

    with pytest.raises(ValueError):
        get_dd_xml("0.0")
