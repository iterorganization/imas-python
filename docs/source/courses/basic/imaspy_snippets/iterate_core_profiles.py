import imaspy.training

# Open input data entry
entry = imaspy.training.get_training_db_entry()

cp = entry.get("core_profiles")
for el in ["profiles_1d", "global_quantities", "code"]:
    print(cp[el])
