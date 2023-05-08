"""A testcase checking if writing and then reading works for the latest full
data dictionary version.
"""

import copy
import logging

import pytest

import imaspy
from imaspy.ids_defs import ASCII_BACKEND, MEMORY_BACKEND
from imaspy.test.test_helpers import compare_children, fill_with_random_data, open_ids

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


def test_latest_dd_autofill_consistency(ids_name):
    ids = imaspy.ids_root.IDSRoot(1, 0)
    fill_with_random_data(ids[ids_name])

    # check that each element in ids[ids_name] has _parent set.
    ids[ids_name].visit_children(has_parent, leaf_only=False)


def has_parent(child):
    """Check that the child has _parent set"""
    assert child._parent is not None


def test_latest_dd_autofill_separate(ids_name, backend, worker_id, tmp_path):
    """Write and then read again a full IDSRoot and all IDSToplevels."""
    ids = open_ids(backend, "w", worker_id, tmp_path)
    fill_with_random_data(ids[ids_name])

    ids[ids_name].put()

    if backend == MEMORY_BACKEND:
        pytest.skip("memory backend does not support opening from separate file")
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


def test_latest_dd_autofill_single(ids_name, backend, worker_id, tmp_path):
    """Write and then read again a full IDSRoot and all IDSToplevels."""
    ids = open_ids(backend, "w", worker_id, tmp_path)
    fill_with_random_data(ids[ids_name])

    ids[ids_name].put()
    ids_ref = copy.deepcopy(ids)
    # the deepcopy comes after the put() since that updates dd version and AL lang

    # test also that deepcopy parents are properly set:
    assert id(ids_ref) == id(ids_ref[ids_name]._parent)

    ids[ids_name].get()

    # basic comparison first
    assert (
        ids[ids_name].ids_properties.comment == ids_ref[ids_name].ids_properties.comment
    )

    if backend == ASCII_BACKEND:
        logger.warning("Skipping ASCII backend tests for empty arrays")
        compare_children(ids[ids_name], ids_ref[ids_name], _ascii_empty_array_skip=True)
    else:
        compare_children(ids[ids_name], ids_ref[ids_name])


def test_latest_dd_autofill_serialize(ids_name, has_imas):
    """Serialize and then deserialize again a full IDSRoot and all IDSToplevels"""
    # TODO: test with multiple serialization protocols
    ids = imaspy.ids_root.IDSRoot(0, 0)
    fill_with_random_data(ids[ids_name])

    if not has_imas:
        return  # rest of the test requires an IMAS install
    data = ids[ids_name].serialize()

    ids2 = imaspy.ids_root.IDSRoot(0, 0)
    ids2[ids_name].deserialize(data)

    logger.warning("Skipping ASCII backend tests for empty arrays")
    compare_children(ids[ids_name], ids2[ids_name], _ascii_empty_array_skip=True)