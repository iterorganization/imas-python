# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging
import os

import numpy as np
import pytest

import imaspy
from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test_helpers import randdims

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.WARNING)


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
    from pathlib import Path

    return Path(__file__).parent / "../assets/IDS_minimal_types.xml"


# TODO: use a separate folder for the MDSPLUS DB and clear it after the testcase
# TODO: since a get() loads the whole IDS splitting this test by ids_type is not so useful maybe
def test_minimal_types_io(backend, xml, ids_type, worker_id):
    """Write and then read again a number on our minimal IDS.
    This gets run with all 4 backend options and with all ids_types (+ None->all)
    """
    ids = open_ids(backend, xml, "w", worker_id)
    for k, v in TEST_DATA.items():
        if ids_type is None or k == ids_type:
            ids.minimal[k] = v

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, xml, "a", worker_id)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        for k, v in TEST_DATA.items():
            if ids_type is None or k == ids_type:
                if type(v) == np.ndarray:
                    assert np.array_equal(ids2.minimal[k].value, v)
                else:
                    assert ids2.minimal[k].value == v


def open_ids(backend, xml_path, mode, worker_id):
    ids = imaspy.ids_root.IDSRoot(1, 0, xml_path=xml_path)
    ids.open_ual_store(
        os.environ.get("USER", "root"), "test", worker_id, backend, mode=mode
    )
    return ids
