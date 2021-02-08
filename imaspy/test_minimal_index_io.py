"""A minimal testcase loading an IDS file and checking that the structure built is ok"""

import logging
from pathlib import Path

import pytest

from imaspy.ids_defs import IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test_helpers import open_ids

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


@pytest.fixture
def xml():
    return Path(__file__).parent / "../assets/IDS_minimal_index.xml"


def test_large_numbers(backend, xml, worker_id, tmp_path):
    """Write and then read again a large number"""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    ids.minimal_index["index"] = 1850997127

    ids.minimal_index.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal_index.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=xml)
    ids2.minimal_index.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("memory backend cannot be opened from different root")
    else:
        assert ids2.minimal_index["index"] == 1850997127
