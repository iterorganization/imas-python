# A testcase loading multiple data dictionary files (all IMAS data-dictionary files in the zip).

import logging
from distutils.version import StrictVersion

import imaspy
import pytest
from imaspy.dd_zip import dd_xml_versions, get_dd_xml

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.DEBUG)


def test_known_version():
    """Test if 3.29.0 is part of the IDSDef.zip
    Mostly this tests if IDSDef.zip has been made."""

    try:
        get_dd_xml("3.29.0")
    except FileNotFoundError:
        pytest.fail("3.29.0 not found in IDSDef.zip")


def test_known_failing_version():
    """Test if -1.0 is part of the IDSDef.zip"""

    with pytest.raises(FileNotFoundError):
        get_dd_xml("-1.0")


def test_load_all_dds():
    """Test loading all of the data dictionaries.
    Only load those where the NBI IDS exists (3.0.4 and up)
    """
    for version in dd_xml_versions()[::-1]:
        if StrictVersion(version) >= StrictVersion("3.0.4"):
            # iterate over all versions packaged in our zipfile (at least one)
            ids = imaspy.ids_classes.IDSRoot(0, 0, version=version, verbosity=1)

            # Check one trivial thing to see if at least something was loaded
            assert ids.nbi.ids_properties.comment.data_type == "STR_0D"
