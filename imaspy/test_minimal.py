# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging

import imaspy
import pytest

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.DEBUG)


@pytest.fixture
def ids_minimal():
    from pathlib import Path

    return Path(__file__).parent / "../assets/IDS_minimal.xml"


@pytest.fixture
def ids_minimal_types():
    from pathlib import Path

    return Path(__file__).parent / "../assets/IDS_minimal_types.xml"


def test_load_minimal(ids_minimal):
    ids = imaspy.ids_classes.IDSRoot(
        0, 0, xml_path=ids_minimal, verbosity=2
    )  # Create a empty IDSs

    # Check if the datatypes are loaded correctly
    assert ids.minimal.a.data_type == "FLT_0D"
    assert ids.minimal.ids_properties.comment.data_type == "STR_0D"

    # Check the documentation
    # assert ids.minimal.a.documentation == "A float"
    # assert ids.minimal.ids_properties.documentation == "Properties of this IDS"
    # assert ids.minimal.ids_properties.comment.documentation == "A string comment"

    # Check the units
    # assert ids.minimal.a.units == "unitless"

    # Check the static/dynamic/constant annotation
    # assert ids.minimal.a.type == "static"
    # assert ids.minimal.ids_properties.comment.type == "constant"


def test_load_multiple_minimal(ids_minimal, ids_minimal_types):
    ids = imaspy.ids_classes.IDSRoot(
        0, 0, xml_path=ids_minimal, verbosity=2
    )  # Create a empty IDSs

    # Check if the datatypes are loaded correctly
    assert ids.minimal.a.data_type == "FLT_0D"
    assert ids.minimal.ids_properties.comment.data_type == "STR_0D"

    ids2 = imaspy.ids_classes.IDSRoot(
        0, 0, xml_path=ids_minimal_types, verbosity=2
    )  # Create a empty IDSs

    # Check if the datatypes are loaded correctly
    assert ids2.minimal.flt_0d.data_type == "FLT_0D"
    assert ids2.minimal.ids_properties.comment.data_type == "STR_0D"
