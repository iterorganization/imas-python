import os

import matplotlib
import imas

# To avoid possible display issues when Matplotlib uses a non-GUI backend
if "DISPLAY" not in os.environ:
    matplotlib.use("agg")
else:
    matplotlib.use("TKagg")

import matplotlib.pyplot as plt

shot, run, user, database = 134173, 106, "public", "ITER"
input = imas.DBEntry(imas.imasdef.MDSPLUS_BACKEND, database, shot, run, user)
input.open()

# Read Te profile and the associated normalised toroidal flux coordinate
te = input.partial_get("core_profiles", "profiles_1d(261)/electrons/temperature")
rho = input.partial_get("core_profiles", "profiles_1d(261)/grid/rho_tor_norm")

# Plot the figure
fig, ax = plt.subplots()
ax.plot(rho, te)
ax.set_ylabel(r"$T_e$")
ax.set_xlabel(r"$\rho_{tor, norm}$")
ax.ticklabel_format(axis="y", scilimits=(-1, 1))
plt.show()
