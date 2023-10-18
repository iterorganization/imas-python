import imaspy.util

# Open input data entry
entry = imaspy.DBEntry(imaspy.ids_defs.HDF5_BACKEND, "ITER_MD", 111001, 103, "public")
entry.open()

# Get the pf_active IDS
pf = entry.get("pf_active")

# Inspect the IDS
imaspy.util.inspect(pf, hide_empty_nodes=True)

entry.close()
