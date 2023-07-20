import numpy as np
import imaspy


# Find nearest value and index in an array
def find_nearest(a, a0):
    "Element in nd array `a` closest to the scalar value `a0`"
    idx = np.abs(a - a0).argmin()
    return a.value[idx], idx


# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imaspy.DBEntry(imaspy.ids_defs.MDSPLUS_BACKEND, database, shot, run, user)
input.open()

# Read the time array from the equilibrium IDS
# partial_get-like functionality will be implemented
# with IMASPy lazy-loading https://jira.iter.org/browse/IMAS-4506
eq = input.get("equilibrium")
time_array = eq.time

# Find the index of the desired time slice in the time array
t_closest, t_index = find_nearest(time_array, 253.0)
print("Time index = ", t_index)
print("Time value = ", t_closest)

# Close input datafile
input.close()
