import imas

# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imas.DBEntry(imas.imasdef.MDSPLUS_BACKEND, database, shot, run, user)
input.open()

# 1. Read and print the time of the equilibrium IDS for the whole scenario
equilibrium = input.get("equilibrium")  # All time slices
print(equilibrium.time)

# 2. Read and print the electron temperature profile in the equilibrium IDS
# at time slice t=253s
core_profiles = input.get_slice(
    "core_profiles", 253, 2
)
print(core_profiles.profiles_1d[0].electrons.temperature)

# Close input datafile
input.close()
