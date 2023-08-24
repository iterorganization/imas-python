import uuid

import imas


def backend_exists(backend):
    """Tries to detect if the lowlevel has support for the given backend."""
    random_db = str(uuid.uuid4())
    dbentry = imas.DBEntry(backend, random_db, 1, 1)
    try:
        # open() raises an exception when there is no support for the backend
        # when there is support, but the entry cannot be opened, it only gives a
        # negative return value.
        # A bit weird (and subject to change per
        # https://jira.iter.org/browse/IMAS-4671), but we can use it nicely here
        dbentry.open()
    except Exception as exc:
        if "Error calling ual_begin_pulse_action" in str(exc):
            return False
        raise
    return True


# Note: UDA backend is not used for benchmarking
all_backends = [
    imas.imasdef.HDF5_BACKEND,
    imas.imasdef.MDSPLUS_BACKEND,
    imas.imasdef.MEMORY_BACKEND,
    imas.imasdef.ASCII_BACKEND,
]

available_backends = list(filter(backend_exists, all_backends))
available_slicing_backends = [
    backend for backend in available_backends if backend != imas.imasdef.ASCII_BACKEND
]
