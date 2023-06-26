import imaspy

# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imaspy.DBEntry(imaspy.ids_defs.MDSPLUS_BACKEND, database, shot, run, user)
input.open()

# Read Te profile and the associated normalised toroidal flux coordinate
# partial_get-like functionality will be implemnted
# with IMASPy lazy-loading https://jira.iter.org/browse/IMAS-4506
t_closest = 261
pr = input.get("core_profiles")
te = pr["profiles_1d"][t_closest]["electrons"]["temperature"]
rho = pr["profiles_1d"][t_closest]["grid"]["rho_tor_norm"]
print("te =", te)
print("rho =", rho)

# Close the datafile
input.close()
