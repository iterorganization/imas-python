# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

"""Functions that are useful for the IMASPy training courses.
"""

from importlib_resources import files
from unittest.mock import patch

import imaspy
import imas


def _initialize_training_db(DBEntry_cls):
    shot, run, user, database = 134173, 106, "public", "ITER"
    entry = DBEntry_cls(imaspy.ids_defs.ASCII_BACKEND, database, shot, run, user)
    assets_path = files(imaspy) / "assets/"
    entry.open(options=f"-prefix {assets_path}/")

    output_entry = DBEntry_cls(imaspy.ids_defs.MEMORY_BACKEND, database, shot, run)
    output_entry.create()
    for ids_name in ["core_profiles", "equilibrium"]:
        ids = entry.get(ids_name)
        with patch.dict('os.environ', {"IMAS_AL_DISABLE_VALIDATE": "1"}):
            output_entry.put(ids)
    entry.close()
    return output_entry


def get_training_db_entry() -> imaspy.DBEntry:
    """Open and return an imaspy.DBEntry pointing to the training data."""
    return _initialize_training_db(imaspy.DBEntry)


def get_training_imas_db_entry() -> imas.DBEntry:
    """Open and return an imas.DBEntry pointing to the training data."""
    return _initialize_training_db(imas.DBEntry)
