import imas

# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imas.DBEntry(imas.imasdef.MDSPLUS_BACKEND, database, shot, run, user)
input.open()

# Read Te profile and the associated normalised toroidal flux coordinate
t_closest = 261
te = input.partial_get("core_profiles", f"profiles_1d({t_closest})/electrons/temperature")
rho = input.partial_get("core_profiles", f"profiles_1d({t_closest})/grid/rho_tor_norm")

# Close the datafile
input.close()
