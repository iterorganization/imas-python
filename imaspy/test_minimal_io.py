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
from imaspy.test_helpers import open_ids

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


@pytest.fixture
def xml():
    from pathlib import Path

    return Path(__file__).parent / "../assets/IDS_minimal.xml"


def test_minimal_io(backend, xml, worker_id, tmp_path):
    """Write and then read again a number on our minimal IDS."""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    ids.minimal.a = 2.0
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()
    assert ids.minimal.a.value == 2.0

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=xml)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        assert ids2.minimal.a.value == 2.0
