import os

import matplotlib
import imaspy.training

# To avoid possible display issues when Matplotlib uses a non-GUI backend
if "DISPLAY" not in os.environ:
    matplotlib.use("agg")
else:
    matplotlib.use("TKagg")

import matplotlib.pyplot as plt

# Open input data entry
entry = imaspy.training.get_training_db_entry()
assert isinstance(entry, imaspy.DBEntry)

# Read Te profile and the associated normalised toroidal flux coordinate
cp = entry.get("core_profiles")
t_closest = 1
te = cp.profiles_1d[t_closest].electrons.temperature
rho = cp.profiles_1d[t_closest].grid.rho_tor_norm

# Plot the figure
fig, ax = plt.subplots()
ax.plot(rho.value, te.value)
ax.set_ylabel(r"$T_e$")
ax.set_xlabel(r"$\rho_{tor, norm}$")
ax.ticklabel_format(axis="y", scilimits=(-1, 1))
plt.show()
