import imaspy

# IMASPy has multiple DD versions inside, which makes this exercise harder.
# We provide possible solutions here

# Option 1: Print the IDSs in the default-selected DD version
factory = imaspy.IDSFactory()
print("IDSs available in DD version", factory.version)
print(list(factory))

# Alternative:
for ids_name in factory:
    print(ids_name, end=", ")
print()

# Option 2: Print the IDSs in a specific DD version
factory = imaspy.IDSFactory("3.39.0")
print("IDSs available in DD version", factory.version)
print(list(factory))
