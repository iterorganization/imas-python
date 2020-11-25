# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging

import imaspy
import pytest

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.DEBUG)

# TODO: unify into single file
@pytest.fixture
def ids_minimal_types():
    from pathlib import Path

    return Path(__file__).parent / "../assets/IDS_minimal_types.xml"


def test_load_minimal_types(ids_minimal_types):
    ids = imaspy.ids_classes.IDSRoot(
        0, 0, xml_path=ids_minimal_types, verbosity=2
    )  # Create a empty IDSs

    # Check if the datatypes are loaded correctly
    assert ids.minimal.flt_0d.data_type == "FLT_0D"
    assert ids.minimal.ids_properties.comment.data_type == "STR_0D"
