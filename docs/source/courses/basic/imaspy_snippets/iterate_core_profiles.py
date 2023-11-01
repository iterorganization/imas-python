import imaspy.training

# Open input data entry
entry = imaspy.training.get_training_db_entry()

cp = entry.get("core_profiles")
for el in ["profiles_1d", "global_quantities", "code"]:
    print(cp[el])

# You can also get sub-elements by separating them with a '/':
print(cp["profiles_1d[0]/electrons/temperature"])
