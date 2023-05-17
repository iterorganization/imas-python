# A testcase loading multiple data dictionary files
# (all IMAS data-dictionary files in the zip with version >= min).

from packaging.version import Version as V

import pytest

import imaspy
from imaspy.dd_zip import dd_xml_versions, get_dd_xml


def test_known_version():
    """Test if 3.30.0 is part of the IDSDef.zip
    Mostly this tests if IDSDef.zip has been made."""

    try:
        get_dd_xml("3.30.0")
    except FileNotFoundError:
        pytest.fail("3.30.0 not found in IDSDef.zip")


def test_known_failing_version():
    """Test if 0.0 is part of the IDSDef.zip"""

    with pytest.raises(FileNotFoundError):
        get_dd_xml("0.0")


# FIXME: duplicate of test_all_dd_versions
@pytest.mark.slow
def test_load_all_dds():
    """Test loading all of the data dictionaries.
    Only load those we support (OLDEST_SUPPORTED_VERSION and up)
    """
    for version in dd_xml_versions()[::-1]:
        if V(version) >= imaspy.OLDEST_SUPPORTED_VERSION:
            # iterate over all versions packaged in our zipfile (at least one)
            ids = imaspy.ids_root.IDSRoot(0, 0, version=version)

            # Check one trivial thing to see if at least something was loaded
            assert ids.nbi.ids_properties.comment.data_type == "STR_0D"
