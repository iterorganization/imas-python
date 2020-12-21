# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging

import pytest

import imaspy

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.WARNING)

# TODO: unify into single file
@pytest.fixture
def ids_minimal_types():
    from pathlib import Path

    return Path(__file__).parent / "../assets/IDS_minimal_types.xml"


def test_load_minimal_types(ids_minimal_types):
    """Check if the standard datatypes are loaded correctly"""
    ids = imaspy.ids_root.IDSRoot(0, 0, xml_path=ids_minimal_types)

    assert ids.minimal.flt_0d.data_type == "FLT_0D"
    assert ids.minimal.flt_1d.data_type == "FLT_1D"
    assert ids.minimal.flt_2d.data_type == "FLT_2D"
    assert ids.minimal.flt_3d.data_type == "FLT_3D"
    assert ids.minimal.flt_4d.data_type == "FLT_4D"
    assert ids.minimal.flt_5d.data_type == "FLT_5D"
    assert ids.minimal.flt_6d.data_type == "FLT_6D"

    assert ids.minimal.str_0d.data_type == "STR_0D"
    assert ids.minimal.str_1d.data_type == "STR_1D"

    assert ids.minimal.int_0d.data_type == "INT_0D"
    assert ids.minimal.int_1d.data_type == "INT_1D"
    assert ids.minimal.int_2d.data_type == "INT_2D"
    assert ids.minimal.int_3d.data_type == "INT_3D"


def test_load_minimal_types_legacy(ids_minimal_types):
    """Check if the legacy datatypes are loaded correctly"""
    ids = imaspy.ids_root.IDSRoot(0, 0, xml_path=ids_minimal_types)

    assert ids.minimal.flt_type.data_type == "FLT_0D"
    assert ids.minimal.flt_1d_type.data_type == "FLT_1D"
    assert ids.minimal.int_type.data_type == "INT_0D"
    assert ids.minimal.str_type.data_type == "STR_0D"
    assert ids.minimal.str_1d_type.data_type == "STR_1D"
