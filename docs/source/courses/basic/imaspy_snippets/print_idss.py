from importlib_resources import files

import imaspy
from imaspy.dd_zip import latest_dd_version, get_dd_xml, dd_etree

# IMASPy has multiple DD versions inside, which makes this exercise harder.
# We provide possible solutions here

# Option 1: Print the data in an existing imaspy.DBEntry
# As data is only loaded when the user explicitly calls get, use the internal
# factory to find the IDS names
shot, run, user, database = 134173, 106, "public", "ITER"
input = imaspy.DBEntry(imaspy.ids_defs.ASCII_BACKEND, database, shot, run)
assets_path = files(imaspy) / "assets/"
input.open(options=f"-prefix {assets_path}/")
print(input.factory._ids_elements.keys())

# Option 2: Use IMASPys IDS factory directory to find the names of IDSs that are
# recognized by IMASPy. We use the latest DD version that is installed, but in
# principle a version string can be blindly given and IMASPy will try to find
# matching version.
from imaspy.dd_zip import latest_dd_version
from imaspy.ids_factory import IDSFactory

factory = IDSFactory(latest_dd_version())
print(factory._ids_elements.keys())

# Option 3: Load the names of the IDSs from the included IDSDef.zip, and use
# Pythons XML etree to find IDSs. This is as low-level as one can get in IMASPy!
from imaspy.dd_zip import dd_etree

tree = dd_etree(latest_dd_version())
print([ids.attrib["name"] for ids in tree.findall("IDS")])
