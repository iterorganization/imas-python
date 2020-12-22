"""A testcase checking if writing and then reading works for the latest full
data dictionary version.
"""

import logging
import os
from pathlib import Path

import numpy as np
import pytest

import imaspy
from imaspy.ids_defs import ASCII_BACKEND, IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test_helpers import (
    compare_children,
    fill_with_random_data,
    open_ids,
    visit_children,
)

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


def test_latest_dd_autofill_consistency(ids_name):
    ids = imaspy.ids_root.IDSRoot(1, 0)
    fill_with_random_data(ids[ids_name])

    # check that each element in ids[ids_name] has _parent set.
    visit_children(ids[ids_name], has_parent)


def has_parent(child):
    """Check that the child has _parent set"""
    assert child._parent is not None


# TODO: use a separate folder for the MDSPLUS DB and clear it after the testcase
def test_latest_dd_autofill(ids_name, backend, worker_id, tmp_path):
    """Write and then read again a full IDSRoot and all IDSToplevels."""
    ids = open_ids(backend, "w", worker_id, tmp_path)
    fill_with_random_data(ids[ids_name])

    ids[ids_name].put()

    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        ids2 = open_ids(backend, "a", worker_id, tmp_path)
        ids2[ids_name].get()

        if backend == ASCII_BACKEND:
            logger.warning("Skipping ASCII backend tests for empty arrays")
            compare_children(
                ids[ids_name], ids2[ids_name], _ascii_empty_array_skip=True
            )
        else:
            compare_children(ids[ids_name], ids2[ids_name])
