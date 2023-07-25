from importlib_resources import files
import os

import matplotlib
import imas
import imaspy

# To avoid possible display issues when Matplotlib uses a non-GUI backend
if "DISPLAY" not in os.environ:
    matplotlib.use("agg")
else:
    matplotlib.use("TKagg")

import matplotlib.pyplot as plt

shot, run, user, database = 134173, 106, "public", "ITER"
input = imas.DBEntry(imas.imasdef.ASCII_BACKEND, database, shot, run)
assets_path = files(imaspy) / "assets/"
input.open(options=f"-prefix {assets_path}/")

# Read Te profile and the associated normalised toroidal flux coordinate
t_closest = 1
cp = input.get("core_profiles")
te = cp.profiles_1d[t_closest].electrons.temperature
rho = cp.profiles_1d[t_closest].grid.rho_tor_norm

# Plot the figure
fig, ax = plt.subplots()
ax.plot(rho, te)
ax.set_ylabel(r"$T_e$")
ax.set_xlabel(r"$\rho_{tor, norm}$")
ax.ticklabel_format(axis="y", scilimits=(-1, 1))
plt.show()
