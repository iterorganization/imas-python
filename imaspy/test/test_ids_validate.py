import logging
from unittest.mock import Mock

import numpy as np
import pytest

from imaspy import IDSFactory, DBEntry
from imaspy.exception import ValidationError
from imaspy.ids_defs import (
    IDS_TIME_MODE_HOMOGENEOUS,
    IDS_TIME_MODE_HETEROGENEOUS,
    IDS_TIME_MODE_INDEPENDENT,
    MEMORY_BACKEND,
)
from imaspy.test.test_helpers import fill_consistent


# Ugly hack to enable the tests for development builds after DD 3.38.1, which have
# version 3.38.1-{commits since tag}-{commit hash}.
# This relies on Python string comparisons and will work also when 3.38.2/3.39.0 is
# released. However, by that point we should just require that as minimum version of the
# test.
requires_DD_after_3_38_1 = pytest.mark.skipif(
    IDSFactory().version <= "3.38.1",
    reason=f"DD newer than 3.38.1 required for test, version is {IDSFactory().version}"
)


@pytest.fixture(autouse=True)
def raise_on_logged_warnings(caplog):
    """Catch warnings logged by validate() and fail the testcase if there are any."""
    yield
    records = [
        rec for rec in caplog.get_records("call") if rec.levelno >= logging.WARNING
    ]
    if records:
        pytest.fail(f"Warning(s) encountered during test: {records}")


def test_validate_time_mode():
    cp = IDSFactory().core_profiles()
    with pytest.raises(ValidationError):
        cp.validate()

    for time_mode in [
        IDS_TIME_MODE_HOMOGENEOUS,
        IDS_TIME_MODE_HETEROGENEOUS,
        IDS_TIME_MODE_INDEPENDENT,
    ]:
        cp.ids_properties.homogeneous_time = time_mode
        cp.validate()


def test_validate_time_coordinate_homogeneous():
    cp = IDSFactory("3.38.1").core_profiles()
    cp.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    cp.time = [1.0, 2.0]
    cp.profiles_1d.resize(2)
    cp.validate()

    cp.profiles_1d.resize(3)
    with pytest.raises(ValidationError):
        # non-matching size
        cp.validate()


def test_validate_time_coodinate_heterogeneous_core_profiles():
    cp = IDSFactory("3.38.1").core_profiles()
    cp.ids_properties.homogeneous_time = IDS_TIME_MODE_HETEROGENEOUS
    cp.profiles_1d.resize(2)
    cp.profiles_1d[0].time = 1.0
    cp.profiles_1d[1].time = 2.0
    cp.validate()


def test_validate_time_mode_heterogeneous_pf_active():
    pfa = IDSFactory("3.38.1").pf_active()
    pfa.ids_properties.homogeneous_time = IDS_TIME_MODE_HETEROGENEOUS
    pfa.coil.resize(1)
    pfa.coil[0].current.data = np.linspace(0, 1, 10)
    with pytest.raises(ValidationError):
        pfa.validate()
    pfa.coil[0].current.time = np.linspace(0, 1, 9)  # one too short
    with pytest.raises(ValidationError):
        pfa.validate()
    pfa.coil[0].current.time = np.linspace(0, 1, 10)
    pfa.validate()

    pfa.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    with pytest.raises(ValidationError):
        pfa.validate()
    pfa.time = np.linspace(0, 1, 10)
    pfa.validate()


def test_validate_time_mode_independent():
    cp = IDSFactory("3.38.1").core_profiles()
    cp.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    cp.validate()
    cp.profiles_1d.resize(1)
    with pytest.raises(ValidationError):
        cp.validate()


def test_fixed_size_coordinates_up_to_two():
    mag = IDSFactory("3.38.1").magnetics()
    mag.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    mag.b_field_pol_probe.resize(1)
    mag.validate()
    for bandwidth_size in [0, 1, 2, 3, 4, 1000]:
        mag.b_field_pol_probe[0].bandwidth_3db = np.linspace(0, 1, bandwidth_size)
        if bandwidth_size <= 2:
            mag.validate()
        else:  # coordinate1 = 1...2, so three or more elements are not allowed
            with pytest.raises(ValidationError):
                mag.validate()


def test_fixed_size_coordinates_up_to_three():
    wall = IDSFactory("3.38.1").wall()
    wall.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    wall.time = np.linspace(0, 1, 10)
    for size in range(1, 4):
        data = np.ones((size, 10))
        wall.global_quantities.electrons.particle_flux_from_wall = data
        wall.validate()
    wall.global_quantities.electrons.particle_flux_from_wall = np.ones((4, 10))
    with pytest.raises(ValidationError):
        wall.validate()


@requires_DD_after_3_38_1
def test_validate_indirect_coordinates():
    """Test indirect coordinates like
    coordinate1=coordinate_system(process(i1)/coordinate_index)/coordinate(1)
    """
    amns = IDSFactory().amns_data()
    amns.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    amns.process.resize(1)
    amns.process[0].charge_state.resize(1)
    amns.process[0].charge_state[0].table_1d = np.ones(10)
    with pytest.raises(ValidationError):
        # unset amns.process[0].coordinate_index
        amns.validate()

    # create some coordinate systems
    amns.coordinate_system.resize(3)
    for i in range(3):
        amns.coordinate_system[i].coordinate.resize(6)
        for j in range(6):
            amns.coordinate_system[i].coordinate[j].label = f"label_{i}_{j}"
            values = np.linspace(0, 1, 1 + i + j)
            amns.coordinate_system[i].coordinate[j].values = values

    amns.process[0].coordinate_index = 1
    amns.process[0].charge_state[0].table_1d = np.ones(1)
    amns.validate()

    for i in range(6):
        shape = [1, 2, 3, 4, 5, 6]
        shape[i] = shape[i] + 1
        amns.process[0].charge_state[0].table_6d = np.ones(shape)
        with pytest.raises(ValidationError):
            amns.validate()
    amns.process[0].charge_state[0].table_6d = np.ones((1, 2, 3, 4, 5, 6))
    amns.validate()

    amns.process[0].coordinate_index = 3
    with pytest.raises(ValidationError):
        amns.validate()
    amns.process[0].charge_state[0].table_1d = np.ones(3)
    amns.process[0].charge_state[0].table_6d = np.ones((3, 4, 5, 6, 7, 8))
    amns.validate()


def test_validate_exclusive_references():
    distr = IDSFactory("3.38.1").distributions()
    distr.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    distr.time = [1.0]
    distr.distribution.resize(1)
    distr.distribution[0].profiles_2d.resize(1)
    distr.distribution[0].profiles_2d[0].density = np.ones((2, 3))
    with pytest.raises(ValidationError):
        distr.validate()

    distr.distribution[0].profiles_2d[0].grid.r = np.linspace(0, 1, 2)
    distr.distribution[0].profiles_2d[0].grid.z = np.linspace(0, 1, 3)
    distr.validate()

    distr.distribution[0].profiles_2d[0].grid.rho_tor_norm = np.linspace(0, 1, 2)
    with pytest.raises(ValidationError):
        distr.validate()  # either grid/r or grid/rho_tor_norm can be defined

    distr.distribution[0].profiles_2d[0].grid.r = []
    distr.validate()


@requires_DD_after_3_38_1
def test_validate_reference_or_fixed_size():
    waves = IDSFactory().waves()
    waves.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    waves.time = [1.0]
    waves.coherent_wave.resize(1)
    waves.coherent_wave[0].beam_tracing.resize(1)
    waves.coherent_wave[0].beam_tracing[0].beam.resize(1)
    waves.validate()

    beam = waves.coherent_wave[0].beam_tracing[0].beam[0]
    # n_tor coordinate1=beam.length OR 1...1
    beam.wave_vector.n_tor = [1]
    waves.validate()
    beam.wave_vector.n_tor = [1, 2]
    with pytest.raises(ValidationError):
        waves.validate()  # beam.length has length 0
    beam.length = [0.4, 0.5]
    waves.validate()


def test_validate_coordinate_same_as():
    ml = IDSFactory("3.38.1").mhd_linear()
    ml.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ml.time = [1.0]
    ml.time_slice.resize(1)
    ml.validate()

    ml.time_slice[0].toroidal_mode.resize(1)
    tor_mode = ml.time_slice[0].toroidal_mode[0]
    tor_mode.plasma.grid.dim1 = np.ones(4)
    tor_mode.plasma.stress_maxwell.imaginary = np.ones((4, 5, 6))
    with pytest.raises(ValidationError):
        # The imaginary component has coordinate2/3_same_as the real component
        # but the real component is still empty
        ml.validate()

    tor_mode.plasma.stress_maxwell.real = np.ones((4, 5, 6))
    ml.validate()

    tor_mode.plasma.stress_maxwell.real = np.ones((4, 1, 6))
    with pytest.raises(ValidationError):
        ml.validate()  # dimension 2 does not match

    tor_mode.plasma.stress_maxwell.real = np.ones((4, 5, 1))
    with pytest.raises(ValidationError):
        ml.validate()  # dimension 3 does not match


@pytest.mark.parametrize(
    "env_value, should_validate",
    [
        ("1", True),
        ("yes", True),
        ("asdf", True),
        ("0", False),
        ("", False),
        (None, False),
    ],
)
def test_validate_on_put(monkeypatch, env_value, should_validate):
    dbentry = DBEntry(MEMORY_BACKEND, "test", 1, 1)
    dbentry.create()
    ids = dbentry.factory.core_profiles()
    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.time = [1]

    validate_mock = Mock()
    monkeypatch.setattr("imaspy.ids_toplevel.IDSToplevel.validate", validate_mock)
    if env_value is None:
        monkeypatch.delenv("IMAS_AL_ENABLE_VALIDATION_AT_PUT", raising=False)
    else:
        monkeypatch.setenv("IMAS_AL_ENABLE_VALIDATION_AT_PUT", env_value)

    dbentry.put(ids)
    assert validate_mock.call_count == 1 * should_validate
    dbentry.put_slice(ids)
    assert validate_mock.call_count == 2 * should_validate


def test_validate_ignore_nested_aos():
    # Ignore coordinates inside an AoS outside our tree, see IMAS-4675
    equilibrium = IDSFactory("3.38.1").equilibrium()
    equilibrium.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    equilibrium.time = [1]
    equilibrium.time_slice.resize(1)
    equilibrium.validate()
    equilibrium.time_slice[0].ggd.resize(1)
    # Coordinate of equilibrium time_slice(itime)/ggd = grids_ggd(itime)/grid
    # where grids_ggd is a (dynamic) AoS outside our tree, so this coordinate check
    # should be ignored:
    equilibrium.validate()


@requires_DD_after_3_38_1
def test_validate_random_fill(ids_name):
    if ids_name == "amns_data":
        pytest.skip("Indirect coordinates in amns_data tested separately")
    ids = IDSFactory().new(ids_name)
    fill_consistent(ids)
    ids.validate()
