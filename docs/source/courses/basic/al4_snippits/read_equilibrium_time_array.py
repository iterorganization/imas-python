import imas
import numpy as np

# Find nearest value and index in an array
def find_nearest(a, a0):
    "Element in nd array `a` closest to the scalar value `a0`"
    idx = np.abs(a - a0).argmin()
    return a.flat[idx],idx

# Open input datafile
shot,run,user,database = 134173,106,'public','ITER'
input = imas.DBEntry(imas.imasdef.MDSPLUS_BACKEND,database,shot,run,user)
input.open()

# Read the time array from the equilibrium IDS
time_array = input.partial_get(ids_name='equilibrium',data_path='time')

# Find the index of the desired time slice in the time array
t_closest,t_index=find_nearest(time_array,253.)
print('Time index = ',t_index)

# Close input datafile
input.close()
