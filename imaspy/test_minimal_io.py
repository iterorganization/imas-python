# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging
import os

import imaspy
import pytest
from imaspy.ids_defs import (
    ASCII_BACKEND,
    HDF5_BACKEND,
    IDS_TIME_MODE_HOMOGENEOUS,
    MDSPLUS_BACKEND,
    MEMORY_BACKEND,
)

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.DEBUG)


@pytest.fixture
def xml():
    from pathlib import Path

    return Path(__file__).parent / "../assets/IDS_minimal.xml"


def test_minimal_io_memory(xml):
    min_test(MEMORY_BACKEND, xml)


def test_minimal_io_mdsplus(xml):
    min_test(MDSPLUS_BACKEND, xml)


def test_minimal_io_hdf5(xml):
    min_test(HDF5_BACKEND, xml)


def test_minimal_io_ascii(xml):
    min_test(ASCII_BACKEND, xml)


def min_test(backend, xml):
    """Write and then read again a number on our minimal IDS."""
    ids = open_ids(backend, xml, "w")
    ids.minimal.a = 2
    ids.minimal.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.minimal.put()

    ids2 = open_ids(backend, xml, "a")
    ids2.minimal.get()
    assert ids2.minimal.a == 2


def open_ids(backend, xml_path, mode):
    ids = imaspy.ids_root.IDSRoot(1, 0, xml_path=xml_path, verbosity=2)
    ids.open_ual_store(os.environ["USER"], "test", "3", backend, mode=mode)
    return ids
