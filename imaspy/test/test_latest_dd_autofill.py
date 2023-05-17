"""A testcase checking if writing and then reading works for the latest full
data dictionary version.
"""

import copy

import imaspy
from imaspy.ids_root import IDSRoot
from imaspy.test.test_helpers import (
    compare_children,
    fill_with_random_data,
    open_dbentry,
)


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
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path)
    ids = IDSRoot()[ids_name]
    fill_with_random_data(ids)

    dbentry.put(ids)

    dbentry2 = open_dbentry(backend, "a", worker_id, tmp_path)
    ids2 = dbentry2.get(ids_name)
    compare_children(ids, ids2)


def test_latest_dd_autofill_single(ids_name, backend, worker_id, tmp_path):
    """Write and then read again a full IDSRoot and all IDSToplevels."""
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path)
    ids = IDSRoot()[ids_name]
    fill_with_random_data(ids)

    dbentry.put(ids)
    ids_ref = copy.deepcopy(ids)
    # the deepcopy comes after the put() since that updates dd version and AL lang

    ids = dbentry.get(ids_name)

    # basic comparison first
    assert ids.ids_properties.comment == ids_ref.ids_properties.comment
    compare_children(ids, ids_ref)


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

    compare_children(ids[ids_name], ids2[ids_name])
