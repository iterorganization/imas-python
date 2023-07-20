import imaspy

# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imaspy.DBEntry(imaspy.ids_defs.MDSPLUS_BACKEND, database, shot, run, user_name=user)
input.open()

# 1. Read and print the time of the equilibrium IDS for the whole scenario
# This explicitly converts the data from the old version on disk, to the
# new version of the environment that you have loaded!
equilibrium = input.get("equilibrium")  # All time slices
print(equilibrium.time)

# 2. Read and print the electron temperature profile in the core_profiles IDS
# at time slice t=253s
core_profiles = input.get_slice(
    "core_profiles", 253, imaspy.ids_defs.PREVIOUS_INTERP,
)
print(core_profiles.profiles_1d[0].electrons.temperature)

# Close input datafile
input.close()
