# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging
from pathlib import Path
import string

import pytest

from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test.test_helpers import open_ids

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


@pytest.fixture
def xml():
    return Path(__file__).parents[1] / "assets" / "IDS_minimal_types.xml"


def test_str_1d_empty(backend, xml, worker_id, tmp_path):
    """Write and then read again a string on our minimal IDS.
    """
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    ids.minimal.str_1d = []

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=xml)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        assert list(ids2.minimal.str_1d.value) == []


def test_str_1d_long_single(backend, xml, worker_id, tmp_path):
    """Write and then read again a string on our minimal IDS.
    """
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    ids.minimal.str_1d = [string.ascii_uppercase * 100]

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=xml)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        assert ids2.minimal.str_1d.value == [string.ascii_uppercase * 100]


def test_str_1d_multiple(backend, xml, worker_id, tmp_path):
    """Write and then read again a string on our minimal IDS.
    """
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    ids.minimal.str_1d = [string.ascii_uppercase, string.ascii_lowercase]

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=xml)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        assert ids2.minimal.str_1d.value == [
            string.ascii_uppercase,
            string.ascii_lowercase,
        ]


def test_str_1d_long_multiple(backend, xml, worker_id, tmp_path):
    """Write and then read again a string on our minimal IDS.
    """
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    ids.minimal.str_1d = [string.ascii_uppercase * 100, string.ascii_lowercase * 100]

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=xml)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        assert ids2.minimal.str_1d.value == [
            string.ascii_uppercase * 100,
            string.ascii_lowercase * 100,
        ]
