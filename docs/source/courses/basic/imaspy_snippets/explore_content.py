from importlib_resources import files
import pprint

import imaspy
from imaspy.dd_zip import latest_dd_version, get_dd_xml, dd_etree
from IPython.display import display
from IPython.display import display, display_pretty, display_svg, display_html
from imaspy.ids_toplevel import Foo
from imaspy.ids_primitive import IDSPrimitive, IDSNumericArray

shot, run, user, database = 134173, 106, "public", "ITER"
input = imaspy.DBEntry(imaspy.ids_defs.ASCII_BACKEND, database, shot, run)
assets_path = files(imaspy) / "assets/"
input.open(options=f"-prefix {assets_path}/")
pp = pprint.PrettyPrinter(indent=4)
foo = Foo()

# Open a single IDSToplevel
cp = input.get("core_profiles")
te = cp.profiles_1d[0].electrons.temperature
te.value = [1,2,3,4,5.5]
te_val = cp.profiles_1d[0].electrons.temperature_validity
print("Native Python pprint IDSPrimitive:")
pp.pprint(IDSPrimitive)
print("Native Python pprint IDSPrimitive:")
pp.pprint(te_val)
print("Native Python print te instance:")
print(te)
print("Native Python pprint IDSNumericArray:")
pp.pprint(IDSNumericArray)
print("Native Python print te instance:")
print(te)
print("Native Python pprint te instance:")
pp.pprint(te)
print("Display IPython normal")
display(te)
print("Display IPython pretty")
display_pretty(te)
#display(cp)
#display_pretty(cp)
from IPython import embed; embed()

# IDSs are strict tree structures, where each Toplevel is a child of the DBEntry
# and each child is either a leaf node or a tree itself. We advice to experiment
# interactively with IMASPy before getting to this result, but here is the
# solution:
