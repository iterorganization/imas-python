"""A minimal testcase loading an IDS file and checking that the structure built is ok"""

import logging
from pathlib import Path

import numpy as np
import pytest

from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test_helpers import open_ids, randdims

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


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


@pytest.fixture
def xml():
    return Path(__file__).parent / "../assets/IDS_minimal_types.xml"


def test_minimal_types_io(backend, xml, worker_id, tmp_path):
    """Write and then read again a number on our minimal IDS."""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    for k, v in TEST_DATA.items():
        ids.minimal[k] = v

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=xml)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("memory backend cannot be opened from different root")
    else:
        for k, v in TEST_DATA.items():
            if isinstance(v, np.ndarray):
                assert np.array_equal(ids2.minimal[k].value, v)
            else:
                assert ids2.minimal[k].value == v


def test_large_numbers(backend, xml, worker_id, tmp_path):
    """Write and then read again a large number"""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    ids.minimal["int_0d"] = 955683416

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=xml)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("memory backend cannot be opened from different root")
    else:
        assert ids2.minimal["int_0d"] == 955683416
