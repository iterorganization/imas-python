# A minimal testcase loading an IDS file and checking that the structure built is ok

import logging
import os

import imaspy
import numpy as np
import pytest
from imaspy.ids_defs import (
    IDS_TIME_MODE_INDEPENDENT,
    MEMORY_BACKEND,
)
from imaspy.test_helpers import fill_with_random_data
from imaspy.test_minimal_types_io import TEST_DATA

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.DEBUG)


@pytest.fixture
def xml():
    from pathlib import Path

    return Path(__file__).parent / "../assets/IDS_minimal_types.xml"


# TODO: use a separate folder for the MDSPLUS DB and clear it after the testcase
# TODO: since a get() loads the whole IDS splitting this test by ids_type is not so useful maybe
def test_minimal_types_io_automatic(backend, xml, ids_type):
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
            if ids_type is None or k == ids_type:
                if type(v) == np.ndarray:
                    assert np.array_equal(ids2.minimal[k].value, ids.minimal[k].value)
                else:
                    assert ids2.minimal[k].value == ids.minimal[k].value


def open_ids(backend, xml_path, mode):
    ids = imaspy.ids_root.IDSRoot(1, 0, xml_path=xml_path, verbosity=2)
    ids.open_ual_store(os.environ.get("USER", "root"), "test", "3", backend, mode=mode)
    return ids
