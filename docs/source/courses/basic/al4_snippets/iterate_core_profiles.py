from importlib_resources import files

import imas
import imaspy

# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imas.DBEntry(imas.imasdef.ASCII_BACKEND, database, shot, run)
assets_path = files(imaspy) / "assets/"
input.open(options=f"-prefix {assets_path}/")

cp = input.get("core_profiles")
for el in ["profiles_1d", "global_quantities", "code"]:
    try:
        print(getattr(cp, el))
    except NameError:
        print(f"Could not print {el}, internal IMAS error")
