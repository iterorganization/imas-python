"""A testcase checking if writing and then reading works for the latest full
data dictionary version.

We then specifically check certain fields which have been renamed between versions,
by writing them as the old and reading as new and vice-versa
"""

import logging

from imaspy.ids_defs import IDS_TIME_MODE_HOMOGENEOUS, MEMORY_BACKEND
from imaspy.test_helpers import compare_children, fill_with_random_data, open_ids

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.DEBUG)


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

        assert ids2[ids_name].ec.antenna[0].name == "test"


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

        assert ids2[ids_name].ec.antenna[0].name == "test"


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

        assert ids2[ids_name].ec.antenna[0].name == "test"


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
        compare_children(ids[ids_name].ec.antenna, ids2[ids_name].ec.launcher)
