"""A testcase checking if writing and then reading works for the latest full
data dictionary version.
"""

import copy

from imaspy.ids_factory import IDSFactory
from imaspy.test.test_helpers import (
    compare_children,
    fill_with_random_data,
    open_dbentry,
)
from imaspy.util import visit_children


def test_latest_dd_autofill_consistency(ids_name):
    ids = IDSFactory().new(ids_name)
    fill_with_random_data(ids)

    # check that each element in ids has _parent set.
    visit_children(ids, has_parent, leaf_only=False)


def has_parent(child):
    """Check that the child has _parent set"""
    assert child._parent is not None


def test_latest_dd_autofill_separate(ids_name, backend, worker_id, tmp_path):
    """Write and then read again all IDSToplevels."""
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path)
    ids = IDSFactory().new(ids_name)
    fill_with_random_data(ids)

    dbentry.put(ids)

    dbentry2 = open_dbentry(backend, "a", worker_id, tmp_path)
    ids2 = dbentry2.get(ids_name)
    compare_children(ids, ids2)


def test_latest_dd_autofill_single(ids_name, backend, worker_id, tmp_path):
    """Write and then read again all IDSToplevels."""
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path)
    ids = IDSFactory().new(ids_name)
    fill_with_random_data(ids)

    dbentry.put(ids)
    ids_ref = copy.deepcopy(ids)
    # the deepcopy comes after the put() since that updates dd version and AL lang

    ids = dbentry.get(ids_name)

    # basic comparison first
    assert ids.ids_properties.comment == ids_ref.ids_properties.comment
    compare_children(ids, ids_ref)


def test_latest_dd_autofill_serialize(ids_name, has_imas):
    """Serialize and then deserialize again all IDSToplevels"""
    # TODO: test with multiple serialization protocols
    factory = IDSFactory()
    ids = factory.new(ids_name)
    fill_with_random_data(ids)

    if not has_imas:
        return  # rest of the test requires an IMAS install
    data = ids.serialize()

    ids2 = factory.new(ids_name)
    ids2.deserialize(data)

    compare_children(ids, ids2)
