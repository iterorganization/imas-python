# A minimal testcase loading an IDS file and checking that the structure built is ok
import numpy
import pytest

from imaspy.ids_factory import IDSFactory


@pytest.fixture
def minimal(ids_minimal_types):
    return IDSFactory(xml_path=ids_minimal_types).new("minimal")


# The test_assign_* tests are testing IDSPrimitive.cast_value
sample_values = {
    "STR": ["0D string", ["list", "of", "strings"]],
    "INT": [1, *(numpy.ones((2,) * i, dtype=numpy.int32) for i in range(1, 4))],
    "FLT": [1.0, *(numpy.ones((2,) * i, dtype=numpy.float64) for i in range(1, 7))],
    "CPX": [
        1.0 + 1.0j,
        *(numpy.ones((2,) * i, dtype=numpy.complex128) * (1 + 1j) for i in range(1, 7)),
    ],
}


def test_assign_str_0d(minimal, caplog):
    caplog.set_level("WARNING", "imaspy")

    # Test auto-encoding
    minimal.str_0d = b"123"
    assert minimal.str_0d.value == "123"
    assert len(caplog.records) == 1  # Should trigger a warning about auto-conversion

    for name, values in sample_values.items():
        for ndim, value in enumerate(values):
            caplog.clear()
            minimal.str_0d = value
            # All values except sample_values["STR"][0] should log a warning
            assert len(caplog.records) == 0 if name == "STR" and ndim == 0 else 1


def test_assign_str_1d(minimal, caplog):
    caplog.set_level("WARNING", "imaspy")

    # Test auto-encoding
    minimal.str_1d = [b"123", "456"]
    assert minimal.str_1d.value == ["123", "456"]
    assert len(caplog.records) == 1  # Should trigger a warning about auto-conversion

    for name, values in sample_values.items():
        for ndim, value in enumerate(values):
            caplog.clear()
            minimal.str_1d = value
            # All values except sample_values["STR"][1] should log a warning
            assert len(caplog.records) == (0 if name == "STR" and ndim == 1 else 1)


# Prevent the expected numpy ComplexWarnings from cluttering pytest output
@pytest.mark.filterwarnings("ignore::numpy.ComplexWarning")
@pytest.mark.parametrize("typ, max_dim", [("flt", 6), ("cpx", 6), ("int", 3)])
def test_assign_numeric_types(minimal, caplog, typ, max_dim):
    for dim in range(max_dim + 1):
        name = f"{typ}_{dim}d"

        for other_typ, values in sample_values.items():
            can_assign = typ == other_typ.lower()
            can_assign = can_assign or (typ == "cpx" and other_typ != "STR")
            can_assign = can_assign or (typ == "int" and other_typ == "FLT")
            can_assign = can_assign or (typ == "flt" and other_typ == "INT")
            for other_ndim, value in enumerate(values):
                if dim == other_ndim and can_assign:
                    caplog.clear()
                    minimal[name].value = value
                    assert len(caplog.records) == (0 if typ == other_typ.lower() else 1)
                elif dim == other_ndim >= 1 and other_typ == "CPX":
                    with pytest.warns(numpy.ComplexWarning):
                        minimal[name].value = value
                else:
                    with pytest.raises(Exception) as excinfo:
                        minimal[name].value = value
                    assert excinfo.type in (ValueError, TypeError)


def test_load_minimal_types(minimal):
    """Check if the standard datatypes are loaded correctly"""
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


def test_load_minimal_types_legacy(minimal):
    """Check if the legacy datatypes are loaded correctly"""
    assert minimal.flt_type.data_type == "FLT_0D"
    assert minimal.flt_1d_type.data_type == "FLT_1D"
    assert minimal.int_type.data_type == "INT_0D"
    assert minimal.str_type.data_type == "STR_0D"
    assert minimal.str_1d_type.data_type == "STR_1D"


def test_numeric_array_value(minimal):
    assert not minimal.flt_0d.has_value
    assert not minimal.flt_1d.has_value

    minimal.flt_0d.value = 7.4
    assert minimal.flt_0d.has_value

    minimal.flt_1d.value = [1.3, 3.4]
    assert minimal.flt_1d.has_value


@pytest.mark.parametrize("tp", ["flt_0d", "cpx_0d", "int_0d", "str_0d"])
def test_ids_primitive_properties_0d(minimal, tp):
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


def test_ids_primitive_properties_str_1d(minimal):
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
def test_ids_primitive_properties_numeric_arrays(minimal, typ, max_dim):
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

        minimal[tp] = numpy.empty((0,) * dim)
        assert not minimal[tp].has_value
        assert minimal[tp].shape == (0,) * dim
        assert minimal[tp].size == 0
