from importlib_resources import files

import imaspy
from imaspy.dd_zip import latest_dd_version, get_dd_xml, dd_etree

shot, run, user, database = 134173, 106, "public", "ITER"
input = imaspy.DBEntry(imaspy.ids_defs.ASCII_BACKEND, database, shot, run)
assets_path = files(imaspy) / "assets/"
input.open(options=f"-prefix {assets_path}/")

# Open a single IDSToplevel
cp = input.get("core_profiles")

# IDSs are strict tree structures, where each Toplevel is a child of the DBEntry
# and each child is either a leaf node or a tree itself. We advice to experiment
# interactively with IMASPy before getting to this result, but here is the
# solution:
