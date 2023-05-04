"""A testcase checking if writing and then reading works for the latest full
data dictionary version.
"""

import logging
import os

import numpy as np
import pytest

# import IMAS HLI, skip module when this is an install without IMAS
imas = pytest.importorskip("imas")

from imaspy.ids_defs import (
    ASCII_BACKEND,
    IDS_TIME_MODE_HOMOGENEOUS,
    MEMORY_BACKEND,
    MDSPLUS_BACKEND,
)
from imaspy.mdsplus_model import ensure_data_dir, mdsplus_model_dir
from imaspy.test_helpers import open_ids

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


def test_write_read_time(backend, worker_id, tmp_path):
    """Write some data to an IDS and then check that all slices match."""
    ids = open_ids(backend, "w", worker_id, tmp_path)
    eq = ids["equilibrium"]
    eq.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS

    eq.time = np.array([0.0, 0.1, 0.2])
    eq.put()

    eq.time = None

    eq.get()
    assert eq.time == np.array([0.0, 0.1, 0.2])


def test_time_slicing_get(backend, worker_id, tmp_path):
    """Write some data to an IDS and then check that all slices match."""
    if backend == ASCII_BACKEND:
        pytest.skip("ASCII backend does not support slice mode")
    ids = open_ids(backend, "w", worker_id, tmp_path)
    eq = ids["equilibrium"]
    eq.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS

    eq.time = np.array([0.0, 0.1, 0.2])
    eq.vacuum_toroidal_field.b0 = np.array([3.0, 4.0, 5.0])
    eq.put()

    for time in range(3):
        eq.getSlice(time * 0.1)
        assert eq.vacuum_toroidal_field.b0.value == time + 3.0


def test_time_slicing_put(backend, worker_id, tmp_path, request):
    """Write some slices to an IDS and then check that they are all there"""
    if backend == ASCII_BACKEND:
        pytest.skip("ASCII backend does not support slice mode")
    ids = open_ids(backend, "w", worker_id, tmp_path)
    eq = ids["equilibrium"]
    eq.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS

    for time in range(3):
        eq.time = [time * 0.1]
        eq.vacuum_toroidal_field.b0 = [time + 3.0]
        eq.putSlice()

    eq.get()

    assert np.allclose(eq.vacuum_toroidal_field.b0.value, [3.0, 4.0, 5.0])
    assert np.allclose(eq.time.value, [0.0, 0.1, 0.2])


def test_hli_time_slicing_put(backend, worker_id, tmp_path):
    """Write some slices to an IDS and then check that they are all there"""
    if backend == ASCII_BACKEND:
        pytest.skip("ASCII backend does not support slice mode")

    ids = imas.equilibrium()

    if worker_id == "master":
        shot = 1
    else:
        shot = int(worker_id[2:]) + 1

    # ensure presence of mdsplus model dir
    if backend == MDSPLUS_BACKEND:
        os.environ["ids_path"] = mdsplus_model_dir(version=os.environ["IMAS_VERSION"])
        ensure_data_dir(str(tmp_path), "test", "3", 9999)
    db_entry = imas.DBEntry(backend, "test", shot, 9999, user_name=str(tmp_path))
    status, ctx = db_entry.create()
    if status != 0:
        logger.error("Error opening db entry %s", status)

    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS

    for time in range(3):
        ids.vacuum_toroidal_field.b0 = np.asarray([time + 3.0])
        ids.time = np.asarray([time * 0.1])
        ids.putSlice(0, db_entry)

    ids.get(0, db_entry)

    db_entry.close()

    assert np.allclose(ids.vacuum_toroidal_field.b0, [3.0, 4.0, 5.0])
    assert np.allclose(ids.time, [0.0, 0.1, 0.2])


def test_time_slicing_put_two(backend, worker_id, tmp_path):
    """Write some slices to an IDS and then check that they are all there"""
    if backend == ASCII_BACKEND:
        pytest.skip("ASCII backend does not support slice mode")
    ids = open_ids(backend, "w", worker_id, tmp_path)
    eq = ids["equilibrium"]
    eq.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS

    for time in range(3):
        eq.vacuum_toroidal_field.b0 = [time + 3.0, time + 3.5]
        eq.time = [time * 0.1, (time + 0.5) * 0.1]
        eq.putSlice()

    eq.get()

    assert np.array_equal(
        eq.vacuum_toroidal_field.b0.value, [3.0, 3.5, 4.0, 4.5, 5.0, 5.5]
    )
    # Use allclose instead of array_equal since 0.15000000000000002 != 0.15
    assert np.allclose(eq.time.value, [0.0, 0.05, 0.1, 0.15, 0.2, 0.25])


def test_get_default(backend, worker_id, tmp_path):
    """Write some slices to an IDS and then check that they are all there"""
    ids = open_ids(backend, "w", worker_id, tmp_path)
    eq = ids["equilibrium"]
    eq.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    assert eq.ids_properties.homogeneous_time == IDS_TIME_MODE_HOMOGENEOUS
    eq.put()

    eq.vacuum_toroidal_field.b0 = [1.0]
    eq.get()

    # a get() does not overwrite values which are default in the backend
    assert eq.vacuum_toroidal_field.b0.value == [1.0]
    assert eq.ids_properties.homogeneous_time == IDS_TIME_MODE_HOMOGENEOUS
    eq.put()

    eq.vacuum_toroidal_field.b0.value = [2.0]

    eq.get()
    # a get() should overwrite values which are changed in the backend
    assert eq.vacuum_toroidal_field.b0.value == [1.0]
