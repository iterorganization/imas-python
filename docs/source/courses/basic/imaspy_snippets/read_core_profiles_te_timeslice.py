from importlib_resources import files

import imaspy

# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imaspy.DBEntry(imaspy.ids_defs.ASCII_BACKEND, database, shot, run)
assets_path = files(imaspy) / "assets/"
input.open(options=f"-prefix {assets_path}/")

# Read Te profile and the associated normalised toroidal flux coordinate
# partial_get-like functionality will be implemented
# with IMASPy lazy-loading https://jira.iter.org/browse/IMAS-4506
cp = input.get("core_profiles")
t_closest = 1
te = cp.profiles_1d[t_closest].electrons.temperature
rho = cp.profiles_1d[t_closest].grid.rho_tor_norm
print("te =", te)
print("rho =", rho)

# Close the datafile
input.close()
