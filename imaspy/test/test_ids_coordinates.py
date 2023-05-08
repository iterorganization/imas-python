from imaspy.ids_coordinates import IDSCoordinate
from imaspy.ids_root import IDSRoot

import numpy as np
import pytest


def test_coordinate_cache():
    coordinate = IDSCoordinate("1...N")
    coordinate2 = IDSCoordinate("1...N")
    assert coordinate is coordinate2


def test_coordinate_index_unbounded():
    coordinate = IDSCoordinate("1...N")
    assert coordinate.max_size is None
    assert not coordinate.references
    assert not coordinate.has_alternatives
    assert not coordinate.has_validation


@pytest.mark.parametrize("size", range(1, 5))
def test_coordinate_index_bounded(size):
    coordinate = IDSCoordinate(f"1...{size}")
    assert coordinate.max_size == size
    assert not coordinate.references
    assert coordinate.has_validation
    assert not coordinate.has_alternatives


def test_coordinate_with_path():
    coordinate = IDSCoordinate("time")
    assert coordinate.max_size is None
    assert len(coordinate.references) == 1
    assert str(coordinate.references[0]) == "time"
    assert coordinate.has_validation
    assert not coordinate.has_alternatives


def test_coordinate_with_multiple_paths():
    coordinate = IDSCoordinate(
        "distribution(i1)/profiles_2d(itime)/grid/r OR "
        "distribution(i1)/profiles_2d(itime)/grid/rho_tor_norm"
    )
    assert coordinate.max_size is None
    assert len(coordinate.references) == 2
    assert coordinate.has_validation
    assert coordinate.has_alternatives


def test_coordinate_with_path_or_size():
    coordinate = IDSCoordinate(
        "coherent_wave(i1)/beam_tracing(itime)/beam(i2)/length OR 1...1"
    )
    assert coordinate.max_size == 1
    assert len(coordinate.references) == 1
    assert coordinate.has_validation
    assert coordinate.has_alternatives


@pytest.mark.parametrize("spec", ["1...N_charge_states", "1..2"])
def test_coordinate_invalid(spec, caplog: pytest.LogCaptureFixture):
    with caplog.at_level("DEBUG", "imaspy.ids_coordinates"):
        caplog.clear()
        IDSCoordinate._cache.pop(spec, None)  # Remove spec from cache (if exists)
        coordinate = IDSCoordinate(spec)
        assert len(caplog.records) == 1
        assert not coordinate.has_validation


def test_coordinate_immutable():
    coordinate = IDSCoordinate("1...N")
    with pytest.raises(RuntimeError):
        coordinate.has_validation = True


def test_coordinates(ids_minimal_types):
    root = IDSRoot(xml_path=ids_minimal_types)
    ids = root.minimal

    assert len(ids.flt_0d.coordinates) == 0
    assert len(ids.flt_1d.coordinates) == 1
    assert len(ids.flt_2d.coordinates) == 2
    assert len(ids.flt_3d.coordinates) == 3
    assert len(ids.flt_4d.coordinates) == 4
    assert len(ids.flt_5d.coordinates) == 5
    assert len(ids.flt_6d.coordinates) == 6

    ids.flt_1d = [1, 2, 4]
    assert ids.flt_1d.metadata.coordinates[0].max_size == 3
    assert all(ids.flt_1d.coordinates[0] == np.arange(3))

    ids.flt_3d = np.ones((3, 4, 2))
    assert ids.flt_3d.coordinates[0] is ids.flt_1d
    assert all(ids.flt_3d.coordinates[1] == np.arange(4))
    assert all(ids.flt_3d.coordinates[2] == np.arange(2))

    ids.cpx_1d = [1 - 1j]
    assert ids.cpx_1d.coordinates[0] is ids.flt_1d
    # if both flt_1d and int_1d are set, this should give an error
    ids.int_1d = [1]
    with pytest.raises(RuntimeError):
        ids.cpx_1d.coordinates[0]
