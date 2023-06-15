# A minimal testcase loading an IDS file and checking that the structure built is ok
import numpy
import pytest

from imaspy.ids_factory import IDSFactory


def test_load_minimal_types(ids_minimal_types):
    """Check if the standard datatypes are loaded correctly"""
    minimal = IDSFactory(xml_path=ids_minimal_types).new("minimal")

    assert minimal.flt_0d.data_type == "FLT_0D"
    assert minimal.flt_1d.data_type == "FLT_1D"
    assert minimal.flt_2d.data_type == "FLT_2D"
    assert minimal.flt_3d.data_type == "FLT_3D"
    assert minimal.flt_4d.data_type == "FLT_4D"
    assert minimal.flt_5d.data_type == "FLT_5D"
    assert minimal.flt_6d.data_type == "FLT_6D"

    assert minimal.str_0d.data_type == "STR_0D"
    assert minimal.str_1d.data_type == "STR_1D"

    assert minimal.int_0d.data_type == "INT_0D"
    assert minimal.int_1d.data_type == "INT_1D"
    assert minimal.int_2d.data_type == "INT_2D"
    assert minimal.int_3d.data_type == "INT_3D"


def test_load_minimal_types_legacy(ids_minimal_types):
    """Check if the legacy datatypes are loaded correctly"""
    minimal = IDSFactory(xml_path=ids_minimal_types).new("minimal")

    assert minimal.flt_type.data_type == "FLT_0D"
    assert minimal.flt_1d_type.data_type == "FLT_1D"
    assert minimal.int_type.data_type == "INT_0D"
    assert minimal.str_type.data_type == "STR_0D"
    assert minimal.str_1d_type.data_type == "STR_1D"


def test_numeric_array_value(ids_minimal_types):
    minimal = IDSFactory(xml_path=ids_minimal_types).new("minimal")

    assert not minimal.flt_0d.has_value
    assert not minimal.flt_1d.has_value

    minimal.flt_0d.value = 7.4
    assert minimal.flt_0d.has_value

    minimal.flt_1d.value = [1.3, 3.4]
    assert minimal.flt_1d.has_value


@pytest.mark.parametrize("tp", ["flt_0d", "cpx_0d", "int_0d", "str_0d"])
def test_ids_primitive_properties_0d(ids_minimal_types, tp):
    minimal = IDSFactory(xml_path=ids_minimal_types).new("minimal")

    assert not minimal[tp].has_value
    assert minimal[tp].shape == tuple()
    assert minimal[tp].size == 1

    minimal[tp] = 1
    assert minimal[tp].has_value
    assert minimal[tp].shape == tuple()
    assert minimal[tp].size == 1

    minimal[tp] = minimal[tp].metadata.data_type.default
    assert not minimal[tp].has_value
    assert minimal[tp].shape == tuple()
    assert minimal[tp].size == 1


def test_ids_primitive_properties_str_1d(ids_minimal_types):
    minimal = IDSFactory(xml_path=ids_minimal_types).new("minimal")

    assert minimal.str_1d.shape == (0,)
    assert minimal.str_1d.size == 0
    assert not minimal.str_1d.has_value

    minimal.str_1d.value.append("1")
    assert minimal.str_1d.has_value
    assert minimal.str_1d.shape == (1,)
    assert minimal.str_1d.size == 1

    minimal.str_1d.value.pop()
    assert not minimal.str_1d.has_value
    assert minimal.str_1d.shape == (0,)
    assert minimal.str_1d.size == 0


@pytest.mark.parametrize("typ, max_dim", [("flt", 6), ("cpx", 6), ("int", 3)])
def test_ids_primitive_properties_numeric_arrays(ids_minimal_types, typ, max_dim):
    minimal = IDSFactory(xml_path=ids_minimal_types).new("minimal")

    for dim in range(1, max_dim + 1):
        tp = f"{typ}_{dim}d"

        assert not minimal[tp].has_value
        assert minimal[tp].shape == (0,) * dim
        assert minimal[tp].size == 0

        new_size = (2,) * dim
        minimal[tp].value = numpy.ones(new_size)
        assert minimal[tp].has_value
        assert minimal[tp].shape == new_size
        assert minimal[tp].size == 2**dim

        minimal[tp] = []
        assert not minimal[tp].has_value
        if dim > 1:  # TODO: expected failure due to IMAS-4681
            with pytest.raises(AssertionError):
                assert minimal[tp].shape == (0,) * dim
        assert minimal[tp].size == 0
