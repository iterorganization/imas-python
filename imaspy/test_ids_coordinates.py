from imaspy.ids_coordinates import IDSCoordinate

import pytest


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
        coordinate = IDSCoordinate(spec)
        assert len(caplog.records) == 1
        assert not coordinate.has_validation


def test_coordinate_immutable():
    coordinate = IDSCoordinate("1...N")
    with pytest.raises(RuntimeError):
        coordinate.has_validation = True
