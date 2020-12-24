"""A testcase checking if writing and then reading works for the latest full
data dictionary version.

We then specifically check certain fields which have been renamed between versions,
by writing them as the old and reading as new and vice-versa
"""

import logging

import pytest

from imaspy.ids_defs import ASCII_BACKEND, IDS_TIME_MODE_HOMOGENEOUS, MEMORY_BACKEND
from imaspy.test_helpers import compare_children, fill_with_random_data, open_ids

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


def test_pulse_schedule_aos_renamed_up(backend, worker_id, tmp_path):
    """pulse_schedule/ec/launcher was renamed from pulse_schedule/ec/antenna
    in version 3.26.0."""

    ids = open_ids(
        backend, "w", worker_id, tmp_path, version="3.28.0", backend_version="3.25.0"
    )
    ids_name = "pulse_schedule"
    ids[ids_name].ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids[ids_name].ec.launcher.resize(1)
    ids[ids_name].ec.launcher[0].name = "test"

    ids[ids_name].put()

    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        ids2 = open_ids(
            backend,
            "a",
            worker_id,
            tmp_path,
            version="3.25.0",
        )
        ids2[ids_name].get()

        assert ids2[ids_name].ec.antenna[0].name.value == "test"


def test_pulse_schedule_aos_renamed_autodetect_up(backend, worker_id, tmp_path):
    """pulse_schedule/ec/launcher was renamed from pulse_schedule/ec/antenna
    in version 3.26.0."""

    ids = open_ids(
        backend, "w", worker_id, tmp_path, version="3.28.0", backend_version="3.25.0"
    )
    ids_name = "pulse_schedule"
    ids[ids_name].ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids[ids_name].ec.launcher.resize(1)
    ids[ids_name].ec.launcher[0].name = "test"

    ids[ids_name].put()

    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        ids2 = open_ids(
            backend,
            "a",
            worker_id,
            tmp_path,
        )
        ids2[ids_name].get()

        assert ids2[ids_name].ec.launcher[0].name.value == "test"


def test_pulse_schedule_aos_renamed_down(backend, worker_id, tmp_path):
    """pulse_schedule/ec/launcher was renamed from pulse_schedule/ec/antenna
    in version 3.26.0."""

    ids = open_ids(
        backend, "w", worker_id, tmp_path, version="3.25.0", backend_version="3.28.0"
    )
    ids_name = "pulse_schedule"
    ids[ids_name].ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids[ids_name].ec.antenna.resize(1)
    ids[ids_name].ec.antenna[0].name = "test"

    ids[ids_name].put()

    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        ids2 = open_ids(
            backend,
            "a",
            worker_id,
            tmp_path,
            version="3.28.0",
        )
        ids2[ids_name].get()

        assert ids2[ids_name].ec.launcher[0].name.value == "test"


def test_pulse_schedule_aos_renamed_autodetect_down(backend, worker_id, tmp_path):
    """pulse_schedule/ec/launcher was renamed from pulse_schedule/ec/antenna
    in version 3.26.0."""

    ids = open_ids(
        backend, "w", worker_id, tmp_path, version="3.28.0", backend_version="3.25.0"
    )
    ids_name = "pulse_schedule"
    ids[ids_name].ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids[ids_name].ec.launcher.resize(1)
    ids[ids_name].ec.launcher[0].name = "test"

    ids[ids_name].put()

    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        ids2 = open_ids(
            backend,
            "a",
            worker_id,
            tmp_path,
        )
        ids2[ids_name].get()

        assert ids2[ids_name].ec.launcher[0].name.value == "test"


def test_pulse_schedule_aos_renamed_autofill_up(backend, worker_id, tmp_path):
    """pulse_schedule/ec/launcher was renamed from pulse_schedule/ec/antenna
    in version 3.26.0."""

    ids = open_ids(
        backend, "w", worker_id, tmp_path, version="3.28.0", backend_version="3.25.0"
    )
    ids_name = "pulse_schedule"
    fill_with_random_data(ids[ids_name])

    ids[ids_name].put()

    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        ids2 = open_ids(
            backend,
            "a",
            worker_id,
            tmp_path,
            version="3.25.0",
        )
        ids2[ids_name].get()

        # test the antenna/launcher only
        for ch1, ch2 in zip(ids[ids_name].ec.launcher, ids2[ids_name].ec.antenna):
            # compare_children does not work since also the fields were changed.
            # manually check the common fields
            assert ch1.name
            assert ch1.name == ch2.name
            assert ch1.identifier == ch2.identifier
            assert ch1.power_type.name == ch2.power_type.name
            assert ch1.power_type.index == ch2.power_type.index
            for new, old in [
                ("power", "power"),
                ("frequency", "frequency"),
                ("deposition_rho_tor_norm", "deposition_rho_tor_norm"),
                ("steering_angle_pol", "launching_angle_pol"),
                ("steering_angle_tor", "launching_angle_tor"),
            ]:
                assert ch1[new].reference_name == ch2[old].reference_name
                assert ch1[new].reference.data == ch2[old].reference.data
                assert (
                    ch1[new].reference.data_error_upper
                    == ch2[old].reference.data_error_upper
                )
                assert (
                    ch1[new].reference.data_error_lower
                    == ch2[old].reference.data_error_lower
                )
                assert (
                    ch1[new].reference.data_error_index
                    == ch2[old].reference.data_error_index
                )
                assert ch1[new].reference.time == ch2[old].reference.time
                assert ch1[new].reference_type == ch2[old].reference_type
                assert ch1[new].envelope_type == ch2[old].envelope_type


def test_autofill_save_newer(ids_name, backend, worker_id, tmp_path):
    """Create an ids, autofill it, save it as a newer version, read it back
    and check that it's the same."""

    ids = open_ids(
        backend, "w", worker_id, tmp_path, version="3.25.0", backend_version="3.30.0"
    )
    try:
        ids[ids_name]
    except AttributeError:
        pytest.skip("IDS %s not defined for version 3.25.0" % (ids_name,))
    fill_with_random_data(ids[ids_name])

    ids[ids_name].put()

    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        ids2 = open_ids(
            backend,
            "a",
            worker_id,
            tmp_path,
            version="3.25.0",
        )
        ids2[ids_name].get()

        if backend == ASCII_BACKEND:
            compare_children(
                ids[ids_name], ids2[ids_name], _ascii_empty_array_skip=True
            )
        else:
            compare_children(ids[ids_name], ids2[ids_name])


def test_pulse_schedule_change_backend_live(backend, worker_id, tmp_path):
    """pulse_schedule/ec/launcher was renamed from pulse_schedule/ec/antenna
    in version 3.26.0."""

    if backend == MEMORY_BACKEND:
        pytest.skip(
            "memory backend does not support reading again from different structure"
        )
    pytest.skip("Needs implementation of close_ual_store")

    ids = open_ids(backend, "w", worker_id, tmp_path, version="3.25.0")
    ids_name = "pulse_schedule"
    fill_with_random_data(ids[ids_name])
    ids[ids_name].put()
    ids.close()

    ids2 = open_ids(
        backend,
        "a",
        worker_id,
        tmp_path,
        version="3.25.0",
    )
    ids2[ids_name].get()

    # now change backend to 3.28.0 and save it
    ids2[ids_name]._read_backend_xml(version="3.28.0")
    # TODO: close the old ual store
    ids2.open_ual_store(tmp_path, "test", "3", backend, mode="w")
    ids2[ids_name].put()

    # now from a third root check the results
    ids3 = open_ids(
        backend,
        "a",
        worker_id,
        tmp_path,
        version="3.25.0",
    )
    compare_children(ids[ids_name], ids3[ids_name])
