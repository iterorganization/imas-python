# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging
from pathlib import Path

import pytest

import imaspy

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


@pytest.fixture
def ids_minimal_types():
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


def test_numeric_array_value(ids_minimal_types):
    ids = imaspy.ids_root.IDSRoot(0, 0, xml_path=ids_minimal_types)

    assert not ids.minimal.flt_0d.has_value
    assert not ids.minimal.flt_1d.has_value

    ids.minimal.flt_0d.value = 7.4
    assert ids.minimal.flt_0d.has_value

    ids.minimal.flt_1d.value = [1.3, 3.4]
    assert ids.minimal.flt_1d.has_value
