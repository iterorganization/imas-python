import imaspy

# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imaspy.DBEntry(imaspy.ids_defs.MDSPLUS_BACKEND, database, shot, run, user)
input.open()

cp = input.get("core_profiles")
for el in ["profiles_1d", "global_quantities", "code"]:
    print(cp[el])
