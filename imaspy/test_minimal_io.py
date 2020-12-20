# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging
import os

import pytest

import imaspy
from imaspy.ids_defs import (
    ASCII_BACKEND,
    HDF5_BACKEND,
    IDS_TIME_MODE_INDEPENDENT,
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


def test_minimal_io(backend, xml):
    """Write and then read again a number on our minimal IDS."""
    ids = open_ids(backend, xml, "w")
    ids.minimal.a = 2.0
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()
    assert ids.minimal.a.value == 2.0

    ids2 = open_ids(backend, xml, "a")
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        assert ids2.minimal.a.value == 2.0


def open_ids(backend, xml_path, mode):
    ids = imaspy.ids_root.IDSRoot(1, 0, xml_path=xml_path)
    ids.open_ual_store(os.environ.get("USER", "root"), "test", "3", backend, mode=mode)
    return ids
