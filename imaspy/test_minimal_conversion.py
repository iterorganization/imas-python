# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging
import os
from pathlib import Path

import pytest

import imaspy
from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test_helpers import open_ids

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


@pytest.fixture
def xml1():
    return Path(__file__).parent / "../assets/IDS_minimal.xml"


@pytest.fixture
def xml2():
    return Path(__file__).parent / "../assets/IDS_minimal_2.xml"


def test_minimal_io_read_flt_int(backend, xml1, xml2, worker_id, tmp_path):
    """Write and then read again a number on our minimal IDS."""
    shot = 1 if worker_id == "master" else int(worker_id[2:]) + 1
    ids = imaspy.ids_root.IDSRoot(shot, 0, xml_path=xml1)
    ids.open_ual_store(tmp_path, "test", worker_id, backend, mode="w")
    ids.minimal.a = 2.4
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()
    assert ids.minimal.a.value == 2.4

    # xml2 changed a float to an int
    ids2 = imaspy.ids_root.IDSRoot(shot, 0, xml_path=xml2, backend_xml_path=xml1)
    ids2.open_ual_store(tmp_path, "test", worker_id, backend, mode="a")
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("Memory backend cannot be opened from different root")
    else:
        assert ids2.minimal.a.value == 2


def test_minimal_io_read_int_flt(backend, xml1, xml2, worker_id, tmp_path):
    """Write and then read again a number on our minimal IDS."""
    shot = 1 if worker_id == "master" else int(worker_id[2:]) + 1
    ids = imaspy.ids_root.IDSRoot(shot, 0, xml_path=xml2)
    ids.open_ual_store(tmp_path, "test", worker_id, backend, mode="w")
    ids.minimal.a = 2
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()
    assert ids.minimal.a.value == 2

    # xml2 changed a float to an int
    ids2 = imaspy.ids_root.IDSRoot(shot, 0, xml_path=xml1, backend_xml_path=xml2)
    ids2.open_ual_store(tmp_path, "test", worker_id, backend, mode="a")
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("Memory backend cannot be opened from different root")
    else:
        assert ids2.minimal.a.value == 2.0


def test_minimal_io_write_int_flt(backend, xml1, xml2, worker_id, tmp_path):
    """Write and then read again a number on our minimal IDS."""
    shot = 1 if worker_id == "master" else int(worker_id[2:]) + 1
    ids = imaspy.ids_root.IDSRoot(shot, 0, xml_path=xml2, backend_xml_path=xml1)
    ids.open_ual_store(tmp_path, "test", worker_id, backend, mode="w")
    ids.minimal.a = 2
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()
    assert ids.minimal.a.value == 2

    # xml2 changed a float to an int
    ids2 = imaspy.ids_root.IDSRoot(shot, 0, xml_path=xml1)
    ids2.open_ual_store(tmp_path, "test", worker_id, backend, mode="a")
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("Memory backend cannot be opened from different root")
    else:
        assert ids2.minimal.a.value == 2.0


def test_minimal_io_write_flt_int(backend, xml1, xml2, worker_id, tmp_path):
    """Write and then read again a number on our minimal IDS."""
    shot = 1 if worker_id == "master" else int(worker_id[2:]) + 1
    ids = imaspy.ids_root.IDSRoot(shot, 0, xml_path=xml1, backend_xml_path=xml2)
    ids.open_ual_store(tmp_path, "test", worker_id, backend, mode="w")
    ids.minimal.a = 2.6
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()
    assert ids.minimal.a.value == 2.6

    # xml2 changed a float to an int
    ids2 = imaspy.ids_root.IDSRoot(shot, 0, xml_path=xml2)
    ids2.open_ual_store(tmp_path, "test", worker_id, backend, mode="a")
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("Memory backend cannot be opened from different root")
    else:
        assert ids2.minimal.a.value == 3
