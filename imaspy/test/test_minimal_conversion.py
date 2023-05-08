import pytest

from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test.test_helpers import open_ids


def test_minimal_io_read_flt_int(
    backend, ids_minimal, ids_minimal2, worker_id, tmp_path
):
    """Write and then read again a number on our minimal IDS."""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=ids_minimal)
    ids.minimal.a = 2.4
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()
    assert ids.minimal.a.value == 2.4

    # ids_minimal2 changed a float to an int
    ids2 = open_ids(
        backend,
        "a",
        worker_id,
        tmp_path,
        xml_path=ids_minimal2,
        backend_xml_path=ids_minimal,
    )
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("Memory backend cannot be opened from different root")
    else:
        assert ids2.minimal.a.value == 2


def test_minimal_io_read_int_flt(
    backend, ids_minimal, ids_minimal2, worker_id, tmp_path
):
    """Write and then read again a number on our minimal IDS."""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=ids_minimal2)
    ids.minimal.a = 2
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()
    assert ids.minimal.a.value == 2

    # ids_minimal2 changed a float to an int
    ids2 = open_ids(
        backend,
        "a",
        worker_id,
        tmp_path,
        xml_path=ids_minimal,
        backend_xml_path=ids_minimal2,
    )
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("Memory backend cannot be opened from different root")
    else:
        assert ids2.minimal.a.value == 2.0


def test_minimal_io_write_int_flt(
    backend, ids_minimal, ids_minimal2, worker_id, tmp_path
):
    """Write and then read again a number on our minimal IDS."""
    ids = open_ids(
        backend,
        "w",
        worker_id,
        tmp_path,
        xml_path=ids_minimal2,
        backend_xml_path=ids_minimal,
    )
    ids.minimal.a = 2
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()
    assert ids.minimal.a.value == 2

    # ids_minimal2 changed a float to an int
    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=ids_minimal)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("Memory backend cannot be opened from different root")
    else:
        assert ids2.minimal.a.value == 2.0


def test_minimal_io_write_flt_int(
    backend, ids_minimal, ids_minimal2, worker_id, tmp_path
):
    """Write and then read again a number on our minimal IDS."""
    ids = open_ids(
        backend,
        "w",
        worker_id,
        tmp_path,
        xml_path=ids_minimal,
        backend_xml_path=ids_minimal2,
    )
    ids.minimal.a = 2.6
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()
    assert ids.minimal.a.value == 2.6

    # ids_minimal2 changed a float to an int
    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=ids_minimal2)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("Memory backend cannot be opened from different root")
    else:
        assert ids2.minimal.a.value == 3
