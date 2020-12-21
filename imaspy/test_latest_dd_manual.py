"""A testcase checking if writing and then reading works for the latest full
data dictionary version.
"""

import logging
import os

import imaspy
from imaspy.ids_defs import IDS_TIME_MODE_HOMOGENEOUS, MEMORY_BACKEND

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.WARNING)


# TODO: use a separate folder for the MDSPLUS DB and clear it after the testcase
def test_latest_dd_manual(backend):
    """Write and then read again a full IDSRoot and a single IDSToplevel."""
    ids = open_ids(backend, "w")
    ids_name = "pulse_schedule"
    ids[ids_name].ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids[ids_name].ids_properties.comment = "test"

    assert ids[ids_name].ids_properties.comment.value == "test"

    ids[ids_name].put()

    if backend == MEMORY_BACKEND:
        # this one does not store anything between instantiations
        pass
    else:
        ids2 = open_ids(backend, "a")
        ids2[ids_name].get()

        assert ids2[ids_name].ids_properties.comment.value == "test"


def open_ids(backend, mode):
    ids = imaspy.ids_root.IDSRoot(1, 0, _lazy=False)
    ids.open_ual_store(os.environ.get("USER", "root"), "test", "3", backend, mode=mode)
    return ids
