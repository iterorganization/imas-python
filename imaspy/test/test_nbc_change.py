"""A testcase checking if writing and then reading works for the latest full
data dictionary version.

We then specifically check certain fields which have been renamed between versions,
by writing them as the old and reading as new and vice-versa
"""

import logging

import numpy
import pytest

from imaspy.dd_zip import latest_dd_version
from imaspy.ids_convert import convert_ids
from imaspy.ids_defs import IDS_TIME_MODE_HOMOGENEOUS
from imaspy.ids_factory import IDSFactory
from imaspy.test.test_helpers import (
    compare_children,
    fill_with_random_data,
    open_dbentry,
)


@pytest.fixture(autouse=True)
def debug_log(caplog):
    """Make sure we capture all debug output when tests fail."""
    caplog.set_level(logging.DEBUG, "imaspy.ids_convert")


def test_nbc_change_aos_renamed():
    """Test renamed AoS in pulse_schedule: ec/antenna -> ec/launcher.

    Also tests renamed structures:
    - ec/antenna/launching_angle_pol -> ec/launcher/steering_angle_pol
    - ec/antenna/launching_angle_tor -> ec/launcher/steering_angle_tor
    """
    # AOS was renamed at v3.26.0. NBC metadata introduced in 3.28.0
    ps = IDSFactory("3.28.0").new("pulse_schedule")
    ps.ec.launcher.resize(2)
    for i in range(2):
        ps.ec.launcher[i].name = f"test{i}"

    # Test conversion from 3.28.0 -> 3.25.0
    ps2 = convert_ids(ps, "3.25.0")
    assert len(ps2.ec.antenna.value) == 2
    for i in range(2):
        assert ps2.ec.antenna[i].name == f"test{i}"

    # Test conversion from 3.25.0 -> 3.28.0
    ps3 = convert_ids(ps2, "3.28.0")
    assert len(ps3.ec.launcher.value) == 2
    for i in range(2):
        assert ps3.ec.launcher[i].name == f"test{i}"


def test_nbc_change_leaf_renamed():
    """Test renamed leaf in reflectometer_profile: position/r/data -> position/r"""
    # Leaf was renamed at 3.23.3. NBC metadata introduced in 3.28.0
    rp = IDSFactory("3.28.0").new("reflectometer_profile")
    rp.channel.resize(1)
    data = numpy.linspace([0, 1, 2], [1, 2, 3], 5)
    rp.channel[0].position.r = data

    # Test conversion from 3.28.0 -> 3.23.0
    rp2 = convert_ids(rp, "3.23.0")
    assert numpy.array_equal(rp2.channel[0].position.r.data.value, data)

    # Test conversion from 3.23.0 -> 3.28.0
    rp3 = convert_ids(rp2, "3.28.0")
    assert numpy.array_equal(rp3.channel[0].position.r.value, data)


def test_ids_convert_deepcopy():
    time = numpy.linspace(0, 1, 10)

    cp = IDSFactory("3.28.0").new("core_profiles")
    cp.time = time
    assert cp.time.value is time

    cp2 = convert_ids(cp, "3.28.0")  # Converting to the same version should also work
    assert cp2.time.value is time

    cp3 = convert_ids(cp, "3.28.0", deepcopy=True)
    assert cp3.time.value is not time
    assert numpy.array_equal(cp3.time.value, time)


def test_pulse_schedule_aos_renamed_up(backend, worker_id, tmp_path):
    """pulse_schedule/ec/launcher was renamed from pulse_schedule/ec/antenna
    in version 3.26.0."""
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path, dd_version="3.28.0")
    ids = IDSFactory("3.25.0").new("pulse_schedule")
    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.ec.antenna.resize(1)
    ids.ec.antenna[0].name = "test"

    # Test automatic conversion up
    dbentry.put(ids)

    # Now load back and ensure no conversion is done
    ids2 = dbentry.get("pulse_schedule")
    assert ids2.ec.launcher[0].name.value == "test"


def test_pulse_schedule_aos_renamed_autodetect_up(backend, worker_id, tmp_path):
    """pulse_schedule/ec/launcher was renamed from pulse_schedule/ec/antenna
    in version 3.26.0."""
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path, dd_version="3.25.0")
    ids = dbentry.factory.new("pulse_schedule")
    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.ec.antenna.resize(1)
    ids.ec.antenna[0].name = "test"

    # No conversion required
    dbentry.put(ids)

    # Now load back with a newer dbentry version, which does a conversion
    dbentry2 = open_dbentry(backend, "r", worker_id, tmp_path, dd_version="3.28.0")
    ids2 = dbentry2.get("pulse_schedule")
    assert ids2.ec.launcher[0].name.value == "test"


def test_pulse_schedule_aos_renamed_down(backend, worker_id, tmp_path):
    """pulse_schedule/ec/launcher was renamed from pulse_schedule/ec/antenna
    in version 3.26.0."""
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path, dd_version="3.25.0")
    ids = IDSFactory("3.28.0").new("pulse_schedule")
    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.ec.launcher.resize(1)
    ids.ec.launcher[0].name = "test"

    # Test automatic conversion down
    dbentry.put(ids)

    # Now load back and ensure no conversion is done
    ids2 = dbentry.get("pulse_schedule")
    assert ids2.ec.antenna[0].name.value == "test"


def test_pulse_schedule_aos_renamed_autodetect_down(backend, worker_id, tmp_path):
    """pulse_schedule/ec/launcher was renamed from pulse_schedule/ec/antenna
    in version 3.26.0."""
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path, dd_version="3.28.0")
    ids = dbentry.factory.new("pulse_schedule")
    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.ec.launcher.resize(1)
    ids.ec.launcher[0].name = "test"

    # No conversion required
    dbentry.put(ids)

    # Now load back with a newer dbentry version, which does a conversion
    dbentry2 = open_dbentry(backend, "r", worker_id, tmp_path, dd_version="3.25.0")
    ids2 = dbentry2.get("pulse_schedule")
    assert ids2.ec.antenna[0].name.value == "test"


def test_pulse_schedule_aos_renamed_autofill_up(backend, worker_id, tmp_path):
    """pulse_schedule/ec/launcher was renamed from pulse_schedule/ec/antenna
    in version 3.26.0."""
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path, dd_version="3.25.0")
    ids = IDSFactory("3.28.0").new("pulse_schedule")
    fill_with_random_data(ids)
    dbentry.put(ids)

    ids2 = dbentry.get("pulse_schedule")

    # test the antenna/launcher only
    assert len(ids.ec.launcher.value) == len(ids2.ec.antenna.value)
    for ch1, ch2 in zip(ids.ec.launcher, ids2.ec.antenna):
        # compare_children does not work since also the fields were changed.
        # manually check the common fields
        assert ch1.name == ch2.name
        assert ch1.identifier == ch2.identifier
        assert ch1.power_type.name == ch2.power_type.name
        assert ch1.power_type.index == ch2.power_type.index
        for new, old in [
            (ch1.power, ch2.power),
            (ch1.frequency, ch2.frequency),
            (ch1.deposition_rho_tor_norm, ch2.deposition_rho_tor_norm),
            (ch1.steering_angle_pol, ch2.launching_angle_pol),
            (ch1.steering_angle_tor, ch2.launching_angle_tor),
        ]:
            assert new.reference_name == old.reference_name
            assert new.reference.data == old.reference.data
            assert new.reference.data_error_upper == old.reference.data_error_upper
            assert new.reference.data_error_lower == old.reference.data_error_lower
            assert new.reference.data_error_index == old.reference.data_error_index
            assert new.reference.time == old.reference.time
            assert new.reference_type == old.reference_type
            assert new.envelope_type == old.envelope_type


def test_autofill_save_newer(ids_name, backend, worker_id, tmp_path):
    """Create an ids, autofill it, save it as a newer version, read it back
    and check that it's the same.

    TODO: we should also check newer IDSes, since this only checks variables that
    existed in 3.25.0. Doing all versions for all IDSes is too slow however.
    """
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path, dd_version="3.30.0")
    factory = IDSFactory(version="3.25.0")
    if not factory.exists(ids_name):
        pytest.skip("IDS %s not defined for version 3.25.0" % (ids_name,))
    ids = factory.new(ids_name)
    fill_with_random_data(ids)

    dbentry.put(ids)

    dbentry2 = open_dbentry(backend, "r", worker_id, tmp_path, dd_version="3.25.0")
    ids2 = dbentry2.get(ids_name)

    # Some elements were removed between 3.25.0 and 3.30.0, so the conversion discards
    # the affected data. Pass as deleted_paths to compare_children
    deleted_paths = {
        "coils_non_axisymmetric": {"is_periodic", "coils_n"},
        "ece": {"channel/harmonic/data"},
        "langmuir_probes": {
            "embedded/j_ion_parallel/data",
            "embedded/j_ion_parallel/validity_timed",
            "embedded/j_ion_parallel/validity",
            "reciprocating/plunge/potential_floating",
            "reciprocating/plunge/t_e",
            "reciprocating/plunge/t_i",
            "reciprocating/plunge/saturation_current_ion",
            "reciprocating/plunge/heat_flux_parallel",
        },
        "magnetics": {"method/diamagnetic_flux/data"},
        "pulse_schedule": {
            "ec/antenna/phase/reference_name",
            "ec/antenna/phase/reference/data",
            "ec/antenna/phase/reference/time",
            "ec/antenna/phase/reference_type",
            "ec/antenna/phase/envelope_type",
        },
        "spectrometer_x_ray_crystal": {
            "camera/center/r",
            "camera/center/z",
            "camera/center/phi",
        },
    }.get(ids_name, [])
    compare_children(ids, ids2, deleted_paths=deleted_paths)

    # Compare outcome of implicit conversion at put with explicit convert_ids
    implicit_3_30 = dbentry.get(ids_name)
    explicit_3_30 = convert_ids(ids, version="3.30.0")
    compare_children(implicit_3_30, explicit_3_30)

    # Compare outcome of explicit conversion back to 3.25.0
    compare_children(ids2, convert_ids(explicit_3_30, "3.25.0"))


def test_convert_min_to_max(ids_name):
    factory = IDSFactory("3.22.0")
    if not factory.exists(ids_name):
        pytest.skip("IDS %s not defined for version 3.22.0" % (ids_name,))

    ids = factory.new(ids_name)
    fill_with_random_data(ids)
    convert_ids(ids, latest_dd_version())


def test_convert_max_to_min(ids_name):
    factory = IDSFactory("3.22.0")
    if not factory.exists(ids_name):
        pytest.skip("IDS %s not defined for version 3.22.0" % (ids_name,))

    ids = IDSFactory(latest_dd_version()).new(ids_name)
    fill_with_random_data(ids)
    convert_ids(ids, None, factory=factory)
