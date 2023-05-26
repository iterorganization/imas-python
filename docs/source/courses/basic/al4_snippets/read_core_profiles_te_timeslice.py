import imas

# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imas.DBEntry(imas.imasdef.MDSPLUS_BACKEND, database, shot, run, user)
input.open()

# Read Te profile and the associated normalised toroidal flux coordinate
te = input.partial_get("core_profiles", "profiles_1d(261)/electrons/temperature")
rho = input.partial_get("core_profiles", "profiles_1d(261)/grid/rho_tor_norm")

# Close the datafile
input.close()
