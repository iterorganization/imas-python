import numpy as np
import imas
import imaspy.training


# Find nearest value and index in an array
def find_nearest(a, a0):
    "Element in nd array `a` closest to the scalar value `a0`"
    idx = np.abs(a - a0).argmin()
    return a.flat[idx], idx


# Open input data entry
entry = imaspy.training.get_training_imas_db_entry()
assert isinstance(entry, imas.DBEntry)

# Read the time array from the equilibrium IDS
equilibrium = entry.get("equilibrium")  # All time slices
time_array = equilibrium.time

# Find the index of the desired time slice in the time array
t_closest, t_index = find_nearest(time_array, 433)
print("Time index = ", t_index)
print("Time value = ", t_closest)

# Close input data entry
entry.close()
