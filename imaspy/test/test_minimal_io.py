# A minimal testcase loading an IDS file and checking that the structure built is ok
import pytest

from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test.test_helpers import open_ids


def test_minimal_io(backend, ids_minimal, worker_id, tmp_path):
    """Write and then read again a number on our minimal IDS."""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=ids_minimal)
    ids.minimal.a = 2.0
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()
    assert ids.minimal.a.value == 2.0

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=ids_minimal)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("Memory backend cannot be opened from different root")
    else:
        assert ids2.minimal.a.value == 2.0