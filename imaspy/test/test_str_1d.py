# A minimal testcase loading an IDS file and checking that the structure built is ok
import string

from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test.test_helpers import open_ids


def test_str_1d_empty(backend, ids_minimal_types, worker_id, tmp_path):
    """Write and then read again a string on our minimal IDS."""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids.minimal.str_1d = []

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        assert list(ids2.minimal.str_1d.value) == []


def test_str_1d_long_single(backend, ids_minimal_types, worker_id, tmp_path):
    """Write and then read again a string on our minimal IDS."""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids.minimal.str_1d = [string.ascii_uppercase * 100]

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        assert ids2.minimal.str_1d.value == [string.ascii_uppercase * 100]


def test_str_1d_multiple(backend, ids_minimal_types, worker_id, tmp_path):
    """Write and then read again a string on our minimal IDS."""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids.minimal.str_1d = [string.ascii_uppercase, string.ascii_lowercase]

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        assert ids2.minimal.str_1d.value == [
            string.ascii_uppercase,
            string.ascii_lowercase,
        ]


def test_str_1d_long_multiple(backend, ids_minimal_types, worker_id, tmp_path):
    """Write and then read again a string on our minimal IDS."""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids.minimal.str_1d = [string.ascii_uppercase * 100, string.ascii_lowercase * 100]

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        assert ids2.minimal.str_1d.value == [
            string.ascii_uppercase * 100,
            string.ascii_lowercase * 100,
        ]
