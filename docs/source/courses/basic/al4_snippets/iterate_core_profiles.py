import imas

# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imas.DBEntry(imas.imasdef.MDSPLUS_BACKEND, database, shot, run, user)
input.open()

cp = input.get("core_profiles")
for el in ["profiles_1d", "global_quantities", "code"]:
    try:
        print(getattr(cp, el))
    except NameError:
        print(f"Could not print {el}, internal IMAS error")
