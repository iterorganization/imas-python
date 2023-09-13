import imaspy.training

# Open input data entry
entry = imaspy.training.get_training_db_entry()
assert isinstance(entry, imaspy.DBEntry)

# 1. Read and print the time of the equilibrium IDS for the whole scenario
# This explicitly converts the data from the old version on disk, to the
# new version of the environment that you have loaded!
equilibrium = entry.get("equilibrium")  # All time slices
print(equilibrium.time)

# 2. Read and print the electron temperature profile in the core_profiles IDS
# at time slice t=433s
core_profiles = entry.get("core_profiles")
print(core_profiles.profiles_1d[1].electrons.temperature)

# Close input data entry
entry.close()
