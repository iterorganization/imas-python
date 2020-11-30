# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging
import os
import random

import imaspy
import numpy as np
import pytest
from imaspy.ids_defs import (
    ASCII_BACKEND,
    HDF5_BACKEND,
    IDS_TIME_MODE_INDEPENDENT,
    MDSPLUS_BACKEND,
    MEMORY_BACKEND,
)

import imas.hli_exception

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.DEBUG)


# strings and legacy types
def randdims(n):
    """Return a list of n random numbers between 1 and 10 representing
    the shapes in n dimensions"""
    return random.sample(range(1, 10), n)


TEST_DATA = {
    "str_0d": "test",
    "str_1d": ["test0", "test1"],
    "str_type": "test_legacy",
    "str_1d_type": ["test0_legacy", "test1_legacy"],
    "flt_type": 2.0,
    "flt_1d_type": np.asarray([3.0, 4.0]),
    "int_type": 5,
}
for i in range(0, 6):
    # dimensions are random
    TEST_DATA["flt_%dd" % i] = np.random.random_sample(size=randdims(i))
    if i < 4:
        TEST_DATA["int_%dd" % i] = np.random.randint(0, 1000, size=randdims(i))


@pytest.fixture
def xml():
    from pathlib import Path

    return Path(__file__).parent / "../assets/IDS_minimal_types.xml"


def test_minimal_types_io(backend, xml, ids_type):
    """Write and then read again a number on our minimal IDS.
    This gets run with all 4 backend options and with all ids_types (+ None->all)
    """
    ids = open_ids(backend, xml, "w")
    for k, v in TEST_DATA.items():
        if ids_type is None or k == ids_type:
            ids.minimal.__setattr__(k, v)

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, xml, "a")
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        for k, v in TEST_DATA.items():
            if ids_type is None or k == ids_type:
                assert ids2.minimal.__getattr(k).value == v


def open_ids(backend, xml_path, mode):
    ids = imaspy.ids_root.IDSRoot(1, 0, xml_path=xml_path, verbosity=2)
    ids.open_ual_store(os.environ.get("USER", "root"), "test", "3", backend, mode=mode)
    return ids
