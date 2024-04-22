# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""Functions that are useful for the IMASPy training courses.
"""

from unittest.mock import patch

from importlib_resources import files

import imaspy
from imaspy.imas_interface import imas


def _initialize_training_db(DBEntry_cls):
    assets_path = files(imaspy) / "assets/"
    pulse, run, user, database = 134173, 106, "public", "ITER"
    if imaspy.imas_interface.ll_interface._al_version.major == 4:
        entry = DBEntry_cls(imaspy.ids_defs.ASCII_BACKEND, database, pulse, run, user)
        entry.open(options=f"-prefix {assets_path}/")
    else:
        entry = DBEntry_cls(f"imas:ascii?path={assets_path}", "r")

    output_entry = DBEntry_cls(imaspy.ids_defs.MEMORY_BACKEND, database, pulse, run)
    output_entry.create()
    for ids_name in ["core_profiles", "equilibrium"]:
        ids = entry.get(ids_name)
        with patch.dict("os.environ", {"IMAS_AL_DISABLE_VALIDATE": "1"}):
            output_entry.put(ids)
    entry.close()
    return output_entry


def get_training_db_entry() -> imaspy.DBEntry:
    """Open and return an ``imaspy.DBEntry`` pointing to the training data."""
    return _initialize_training_db(imaspy.DBEntry)


def get_training_imas_db_entry():
    """Open and return an ``imas.DBEntry`` pointing to the training data."""
    return _initialize_training_db(imas.DBEntry)
