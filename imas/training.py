# This file is part of IMAS-Python.
# You should have received the IMAS-Python LICENSE file with this project.
"""Functions that are useful for the IMAS-Python training courses."""

try:
    from importlib.resources import files
except ImportError:  # Python 3.8 support
    from importlib_resources import files

import imas


def get_training_db_entry(convert=False) -> imas.DBEntry:
    """Open and return an ``imas.DBEntry`` pointing to the training data.

    Args:
        convert: if True, converts assets to default DD version
    """
    assets_path = files(imas) / "assets/"
    entry = imas.DBEntry(f"imas:ascii?path={assets_path}", "r")

    version = imas.dd_zip.latest_dd_version() if convert else "3.39.0"
    output_entry = imas.DBEntry("imas:memory?path=/", "w", dd_version=version)
    for ids_name in ["core_profiles", "equilibrium"]:
        ids = entry.get(ids_name, autoconvert=False)
        if convert:
            output_entry.put(imas.convert_ids(ids, output_entry.dd_version))
        else:
            output_entry.put(ids)
    entry.close()
    return output_entry
