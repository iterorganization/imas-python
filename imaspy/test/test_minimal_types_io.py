"""A minimal testcase loading an IDS file and checking that the structure built is ok"""
import numpy as np
import pytest

from imaspy.ids_defs import ASCII_BACKEND, IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test.test_helpers import open_ids, randdims


TEST_DATA = {
    "str_0d": "test",
    "str_1d": ["test0", "test1"],
    "str_type": "test_legacy",
    "str_1d_type": ["test0_legacy", "test1_legacy"],
    "flt_type": 2.0,
    "flt_1d_type": np.asarray([3.0, 4.0]),
    "int_type": 5,
}
for i in range(0, 7):
    # dimensions are random
    TEST_DATA["flt_%dd" % i] = np.random.random_sample(size=randdims(i))
    if i < 4:
        TEST_DATA["int_%dd" % i] = np.random.randint(0, 1000, size=randdims(i))


def test_minimal_types_io(backend, ids_minimal_types, worker_id, tmp_path):
    """Write and then read again a number on our minimal IDS."""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=ids_minimal_types)
    for k, v in TEST_DATA.items():
        ids.minimal[k] = v

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("memory backend cannot be opened from different root")
    else:
        for k, v in TEST_DATA.items():
            if isinstance(v, np.ndarray):
                assert np.array_equal(ids2.minimal[k].value, v)
            else:
                assert ids2.minimal[k].value == v


def test_large_numbers(backend, ids_minimal_types, worker_id, tmp_path):
    """Write and then read again a large number"""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids.minimal["int_0d"] = 955683416

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("memory backend cannot be opened from different root")
    else:
        assert ids2.minimal["int_0d"] == 955683416


def test_str1d_empty_default_no_write(backend, ids_minimal_types, worker_id, tmp_path):
    """Write and then read again a large number"""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids.minimal["str_1d"] = np.empty((0,), dtype="str")

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=ids_minimal_types)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("memory backend cannot be opened from different root")
    else:
        assert ids2.minimal["str_1d"].value.size == 0

    if backend == ASCII_BACKEND:
        # test that it did not show up in the file
        filename = str(tmp_path) + "/test_%s_0_minimal.ids" % (
            1 if worker_id == "master" else int(worker_id[2:]) + 1
        )
        with open(filename, "r") as file:
            for line in file.readlines():
                assert not line.startswith("minimal/str_1d")