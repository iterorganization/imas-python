import imaspy.util

# Open input data entry
entry = imaspy.DBEntry(
    imaspy.ids_defs.HDF5_BACKEND, "ITER_MD", 120000, 204, "public", data_version="3"
)
entry.open()

# Get the ec_launchers IDS
pf = entry.get("ec_launchers")

# Inspect the IDS
imaspy.util.inspect(pf, hide_empty_nodes=True)

entry.close()
