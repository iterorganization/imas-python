from importlib_resources import files

import imaspy

# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imaspy.DBEntry(imaspy.ids_defs.ASCII_BACKEND, database, shot, run)
assets_path = files(imaspy) / "assets/"
input.open(options=f"-prefix {assets_path}/")

cp = input.get("core_profiles")
for el in ["profiles_1d", "global_quantities", "code"]:
    print(cp[el])
