# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
import os

import imas

# Open input datafile
shot, run, user, database = 134173, 106, "public", "ITER"
input = imas.DBEntry(imas.imasdef.MDSPLUS_BACKEND, database, shot, run, user)
input.open()

# Read Te profile and the associated normalised toroidal flux coordinate
eq = input.get_slice(
    "equilibrium",
    0,
    imas.imasdef.PREVIOUS_INTERP,
    occurrence=0,
)

# Close the datafile
input.close()

# Dump the data to ASCII
# Create output datafile
user = os.getenv("USER")

# Because we use the ASCII backend, this results in a .ids file in the cwd
output = imas.DBEntry(imas.imasdef.ASCII_BACKEND, database, shot, run, user)
output.create()

# Save the IDS
output.put(eq)

# Close the output datafile
output.close()
