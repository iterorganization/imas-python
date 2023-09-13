import imas
import imaspy.training

# Open input data entry
entry = imaspy.training.get_training_imas_db_entry()
assert isinstance(entry, imas.DBEntry)

# Read Te profile and the associated normalised toroidal flux coordinate
cp = entry.get("core_profiles")
t_closest = 1
te = cp.profiles_1d[t_closest].electrons.temperature
rho = cp.profiles_1d[t_closest].grid.rho_tor_norm
print("te =", te)
print("rho =", rho)

# Close the data entry
entry.close()
