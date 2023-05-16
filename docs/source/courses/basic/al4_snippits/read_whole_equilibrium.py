import imas

# Open input datafile
shot,run,user,database = 134173,106,'public','ITER'
input = imas.DBEntry(imas.imasdef.MDSPLUS_BACKEND,database,shot,run,user)
input.open()

# Read equilibrium and core_profiles IDSs
equilibrium = input.get('equilibrium') # All time slices
core_profiles = input.get_slice('core_profiles',253,2) # Only at t=253s, with interpolation method '2'

print(equilibrium.time)
print(core_profiles.profiles_1d[0].electrons.temperature)

# Close input datafile
input.close()
