"""A minimal testcase loading an IDS file and checking that the structure built is ok"""

import logging
from pathlib import Path

import pytest

from imaspy.ids_defs import ASCII_BACKEND, IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test_helpers import compare_children, fill_with_random_data, open_ids

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


@pytest.fixture
def xml():
    return Path(__file__).parent / "../assets/IDS_minimal_index.xml"


def test_autofill(backend, xml, worker_id, tmp_path):
    """Write and then read again autofill"""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    fill_with_random_data(ids.minimal_index)

    ids.minimal_index.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=xml)
    ids2.minimal_index.get()

    if backend == MEMORY_BACKEND:
        pytest.skip("memory backend cannot be opened from different root")
    else:
        if backend == ASCII_BACKEND:
            logger.warning("Skipping ASCII backend tests for empty arrays")
            compare_children(
                ids.minimal_index, ids2.minimal_index, _ascii_empty_array_skip=True
            )
        else:
            compare_children(ids.minimal_index, ids2.minimal_index)


def test_manual(backend, xml, worker_id, tmp_path):
    """Setup a situation like that encountered in ascii backend tests"""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    ids.minimal_index.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT

    ids.minimal_index.struct_array.resize(200)
    for ii, el in enumerate(ids.minimal_index.struct_array.value):
        el.a.str_1d_2 = []
        el.a.b.str_1d = []
        el.a.b.index = ii

    ids.minimal_index.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=xml)
    ids2.minimal_index.get()

    if backend == MEMORY_BACKEND:
        pytest.skip("memory backend cannot be opened from different root")
    else:
        for ii, el in enumerate(ids2.minimal_index.struct_array.value):
            assert el.a.str_1d_2.value.size == 0
            assert el.a.b.str_1d.value.size == 0
            assert el.a.b.index == ii
