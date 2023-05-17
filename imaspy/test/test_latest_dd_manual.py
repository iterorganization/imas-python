"""A testcase checking if writing and then reading works for the latest full
data dictionary version.
"""

from imaspy.ids_factory import IDSFactory
from imaspy.ids_defs import IDS_TIME_MODE_HOMOGENEOUS
from imaspy.test.test_helpers import open_dbentry


def test_latest_dd_manual(backend, worker_id, tmp_path):
    """Write and then read again a full IDSRoot and a single IDSToplevel."""
    dbentry = open_dbentry(backend, "w", worker_id, tmp_path)
    ids_name = "pulse_schedule"
    ids = IDSFactory().new(ids_name)
    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.ids_properties.comment = "test"

    assert ids.ids_properties.comment.value == "test"

    dbentry.put(ids)

    dbentry2 = open_dbentry(backend, "a", worker_id, tmp_path)
    ids2 = dbentry2.get(ids_name)
    assert ids2.ids_properties.comment.value == "test"


def test_dir(backend, worker_id, tmp_path):
    """Test calling `dir()` on `IDSFactory` to test if we can see IDSes"""
    ir = IDSFactory()
    ir_dir = dir(ir)
    # Check if we can see the first and last stable IDS
    assert "amns_data" in ir_dir, "Could not find amns_data in dir(IDSRoot())"
    assert "workflow" in ir_dir, "Could not find workflow in dir(IDSRoot())"
    assert "__init__" in ir_dir, "Could not find base attributes in dir(IDSRoot())"
