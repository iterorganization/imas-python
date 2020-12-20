"""A minimal testcase loading an IDS file and checking that the structure built is ok
"""

import logging
import os
from pathlib import Path

import numpy as np
import pytest

import imaspy
from imaspy.ids_defs import ASCII_BACKEND, IDS_TIME_MODE_INDEPENDENT, MEMORY_BACKEND
from imaspy.test_helpers import fill_with_random_data
from imaspy.test_minimal_types_io import TEST_DATA

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)


@pytest.fixture
def xml():
    return Path(__file__).parent / "../assets/IDS_minimal_types.xml"


def test_minimal_types_str_1d_decode(xml):
    ids = imaspy.ids_root.IDSRoot(1, 0, xml_path=xml)
    ids.minimal.str_1d = [b"test", b"test2"]
    assert ids.minimal.str_1d.value == ["test", "test2"]


def test_minimal_types_str_1d_decode_and_put(backend, xml):
    """The access layer changed 1d string types to bytes.
    This is unexpected, especially since on read it is converted from bytes to string
    again (which implies that the proper form for in python is as strings)"""
    ids = open_ids(backend, xml, "w")
    ids.minimal.str_1d = [b"test", b"test2"]
    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT

    assert ids.minimal.str_1d.value == ["test", "test2"]
    ids.minimal.put()
    assert ids.minimal.str_1d.value == ["test", "test2"]


# TODO: use a separate folder for the MDSPLUS DB and clear it after the testcase
def test_minimal_types_io_automatic(backend, xml):
    """Write and then read again a number on our minimal IDS.
    This gets run with all 4 backend options and with all ids_types (+ None->all)
    """
    ids = open_ids(backend, xml, "w")
    fill_with_random_data(ids)

    ids.minimal.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    ids.minimal.put()

    ids2 = open_ids(backend, xml, "a")
    ids2.minimal.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        for k, v in TEST_DATA.items():
            if isinstance(v, np.ndarray):
                assert np.array_equal(ids2.minimal[k].value, ids.minimal[k].value)
            else:
                if (
                    backend == ASCII_BACKEND
                    and k in ["str_1d", "str_1d_type"]
                    and ids.minimal[k].value == []
                ):
                    pytest.skip(
                        "Known issue with ASCII backend and 1d strings, see https://jira.iter.org/browse/IMAS-3463"
                    )
                else:
                    assert ids2.minimal[k].value == ids.minimal[k].value


def open_ids(backend, xml_path, mode):
    ids = imaspy.ids_root.IDSRoot(1, 0, xml_path=xml_path)
    ids.open_ual_store(os.environ.get("USER", "root"), "test", "3", backend, mode=mode)
    return ids
