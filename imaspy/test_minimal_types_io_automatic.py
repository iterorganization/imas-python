"""A minimal testcase loading an IDS file and checking that the structure built is ok
"""

import logging
from pathlib import Path

import numpy as np
import pytest

import imaspy
from imaspy.ids_defs import ASCII_BACKEND, IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test_helpers import fill_with_random_data, open_ids
from imaspy.test_minimal_types_io import TEST_DATA

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


@pytest.fixture
def xml():
    return Path(__file__).parent / "assets/IDS_minimal_types.xml"


def test_minimal_types_str_1d_decode(xml):
    ids = imaspy.ids_root.IDSRoot(1, 0, xml_path=xml)
    ids.minimal.str_1d = [b"test", b"test2"]
    assert ids.minimal.str_1d.value == ["test", "test2"]


def test_minimal_types_str_1d_decode_and_put(backend, xml, worker_id, tmp_path):
    """The access layer changed 1d string types to bytes.
    This is unexpected, especially since on read it is converted from bytes to string
    again (which implies that the proper form for in python is as strings)"""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    ids.minimal.str_1d = [b"test", b"test2"]
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT

    assert ids.minimal.str_1d.value == ["test", "test2"]
    ids.minimal.put()
    assert ids.minimal.str_1d.value == ["test", "test2"]


def test_minimal_types_io_automatic(backend, xml, worker_id, tmp_path):
    """Write and then read again a number on our minimal IDS.
    This gets run with all 4 backend options and with all ids_types (+ None->all)
    """
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    fill_with_random_data(ids)

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=xml)
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        pytest.skip("Memory backend cannot be opened from different root")
    else:
        for k, v in TEST_DATA.items():
            if isinstance(v, np.ndarray):
                assert np.array_equal(ids2.minimal[k].value, ids.minimal[k].value)
            else:
                if isinstance(ids2.minimal[k].value, np.ndarray):
                    assert np.array_equal(
                        ids2.minimal[k].value,
                        np.asarray(
                            ids.minimal[k].value, dtype=ids2.minimal[k].value.dtype
                        ),
                    )
                else:
                    assert ids2.minimal[k].value == ids.minimal[k].value
