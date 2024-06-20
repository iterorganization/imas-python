import importlib
import logging
import uuid
from pathlib import Path

from packaging.version import Version

import imaspy
from imaspy.backends.imas_core.imas_interface import ll_interface, lowlevel

# Don't directly import imas: code analyzers break on the huge code base
imas = importlib.import_module("imas")


def backend_exists(backend):
    """Tries to detect if the lowlevel has support for the given backend."""
    random_db = str(uuid.uuid4())
    if ll_interface._al_version < Version("5"):
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

    else:
        dbentry = imaspy.DBEntry(backend, random_db, 1, 1)
        try:
            dbentry.open()
        except Exception as exc:
            if "backend is not available" in str(exc):
                return False
            elif isinstance(exc, lowlevel.ImasCoreBackendException):
                return True
            raise
        return True


# Note: UDA backend is not used for benchmarking
all_backends = [
    imaspy.ids_defs.HDF5_BACKEND,
    imaspy.ids_defs.MDSPLUS_BACKEND,
    imaspy.ids_defs.MEMORY_BACKEND,
    imaspy.ids_defs.ASCII_BACKEND,
]

# Suppress error logs for testing backend availabitily:
#   ERROR:root:b'ual_open_pulse: [UALBackendException = HDF5 master file not found: <path>]'
#   ERROR:root:b'ual_open_pulse: [UALBackendException = %TREE-E-FOPENR, Error opening file read-only.]'
#   ERROR:root:b'ual_open_pulse: [UALBackendException = Missing pulse]'
logging.getLogger().setLevel(logging.CRITICAL)
available_backends = list(filter(backend_exists, all_backends))
logging.getLogger().setLevel(logging.INFO)
available_slicing_backends = [
    backend
    for backend in available_backends
    if backend != imaspy.ids_defs.ASCII_BACKEND
]

hlis = ["imas", "imaspy"]
DBEntry = {
    "imas": imas.DBEntry,
    "imaspy": imaspy.DBEntry,
}
factory = {
    "imas": imas,
    "imaspy": imaspy.IDSFactory(),
}
available_serializers = [imaspy.ids_defs.ASCII_SERIALIZER_PROTOCOL]


def create_dbentry(hli, backend):
    path = Path.cwd() / f"DB-{hli}-{backend}"
    path.mkdir(exist_ok=True)
    if backend == imas.imasdef.MDSPLUS_BACKEND:
        # Need to ensure that the MDS+ data folder exists:
        (path / "benchmark" / "3" / "0").mkdir(parents=True, exist_ok=True)
    dbentry = DBEntry[hli](backend, "benchmark", 1, 1, str(path))
    options = f"-prefix {path}/" if backend == imas.imasdef.ASCII_BACKEND else None
    dbentry.create(options=options)
    return dbentry
