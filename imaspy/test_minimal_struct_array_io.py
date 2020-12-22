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
logger.setLevel(logging.WARNING)


@pytest.fixture
def xml():
    from pathlib import Path

    return Path(__file__).parent / "../assets/IDS_minimal_struct_array.xml"


def test_minimal_struct_array_maxoccur(backend, xml):
    ids = imaspy.ids_root.IDSRoot(1, 0, xml_path=xml)
    ids.minimal_struct_array.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT

    # Can't we do this transparently?
    # i.e.
    # ids.minimal_struct_array[1].a.flt_0d = 2
    # such that it automatically makes the struct if it did not exist?
    # maxoccur is 2, so the next one should raise an exception
    a = ids.minimal_struct_array.struct_array
    a.append(a._element_structure)
    a.append(a._element_structure)
    with pytest.raises(ValueError):
        a.append(a._element_structure)


def test_minimal_struct_array_io(backend, xml, worker_id, tmp_path):
    """Write and then read again a number on our minimal IDS."""
    ids = open_ids(backend, "w", worker_id, tmp_path, xml_path=xml)
    a = ids.minimal_struct_array.struct_array
    ids.minimal_struct_array.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
    a.append(a._element_structure)

    # TODO: these are nested one too deeply in my opinion.
    # (a struct array contains an array of structures directly,
    #  without the intermediate one?)
    a[0].a.flt_0d = 2.0
    a.append(a._element_structure)
    a[1].a.flt_0d = 4.0

    ids.minimal_struct_array.put()
    assert a[0].a.flt_0d.value == 2.0
    assert a[1].a.flt_0d.value == 4.0

    ids2 = open_ids(backend, "a", worker_id, tmp_path, xml_path=xml)
    ids2.minimal_struct_array.get()
    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        assert ids2.minimal_struct_array.struct_array[0].a.flt_0d.value == 2.0
        assert ids2.minimal_struct_array.struct_array[1].a.flt_0d.value == 4.0
