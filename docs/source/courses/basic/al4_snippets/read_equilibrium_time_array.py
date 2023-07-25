from importlib_resources import files

import numpy as np
import imas
import imaspy


# Find nearest value and index in an array
def find_nearest(a, a0):
    "Element in nd array `a` closest to the scalar value `a0`"
    idx = np.abs(a - a0).argmin()
    return a.flat[idx], idx


# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imas.DBEntry(imas.imasdef.ASCII_BACKEND, database, shot, run)
assets_path = files(imaspy) / "assets/"
input.open(options=f"-prefix {assets_path}/")

# Read the time array from the equilibrium IDS
equilibrium = input.get("equilibrium")  # All time slices
time_array = equilibrium.time

# Find the index of the desired time slice in the time array
t_closest, t_index = find_nearest(time_array, 0)
print("Time index = ", t_index)
print("Time value = ", t_closest)

# Close input datafile
input.close()
