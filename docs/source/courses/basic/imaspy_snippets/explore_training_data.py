import imaspy.util
import imaspy.training

# Open input data entry
entry = imaspy.training.get_training_db_entry()

# Get the core_profiles IDS
cp = entry.get("core_profiles")

# Inspect the IDS
imaspy.util.inspect(cp, hide_empty_nodes=True)

entry.close()