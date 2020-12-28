"""A testcase checking if writing and then reading works for the latest full
data dictionary version.
"""

import logging
import os
from pathlib import Path

import numpy as np
import pytest

import imaspy
from imaspy.ids_defs import ASCII_BACKEND, IDS_TIME_MODE_HOMOGENEOUS, MEMORY_BACKEND
from imaspy.test_helpers import (
    compare_children,
    fill_with_random_data,
    open_ids,
    visit_children,
)

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.DEBUG)


def test_time_slicing_get(backend, worker_id, tmp_path):
    """Write some data to an IDS and then check that all slices match."""
    ids = open_ids(backend, "w", worker_id, tmp_path)
    ids_name = "equilibrium"
    eq = ids[ids_name]
    eq.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS

    eq.time = np.array([0.0, 0.1, 0.2])
    eq.vacuum_toroidal_field.b0 = np.array([0, 1, 2])
    eq.put()

    for time in range(3):
        eq.getSlice(time * 0.1)
        assert eq.vacuum_toroidal_field.b0.value == time
