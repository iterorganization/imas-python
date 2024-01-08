import imaspy
import imaspy.training

# 1. Load the training data for the ``core_profiles`` IDS
entry = imaspy.training.get_training_db_entry()
core_profiles = entry.get("core_profiles")

# 2. Print the DD version:
print(core_profiles._dd_version)

# 3. Create a new DBEntry with DD version 3.37.0
new_entry = imaspy.DBEntry(
    imaspy.ids_defs.MEMORY_BACKEND, "test", 0, 0, dd_version="3.37.0"
)
new_entry.create()

# 4. Put the core_profiles IDS in the new DBEntry
new_entry.put(core_profiles)

# 5. Print version_put.data_dictionary
print(core_profiles.ids_properties.version_put.data_dictionary)
# -> 3.37.0
# What do you notice?
#   The IDS was converted to the DD version of the DBEntry (3.37.0) when writing the
#   data to the backend.