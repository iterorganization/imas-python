import imaspy

# 1. Create test data
# Create an IDSFactory for DD 3.25.0
factory = imaspy.IDSFactory("3.25.0")

# Create a pulse_schedule IDS
pulse_schedule = factory.new("pulse_schedule")

# Fill the IDS with some test data
pulse_schedule.ids_properties.homogeneous_time = \
    imaspy.ids_defs.IDS_TIME_MODE_HOMOGENEOUS
pulse_schedule.ids_properties.comment = \
    "Testing renamed IDS nodes with IMASPy"
pulse_schedule.time = [1., 1.1, 1.2]

pulse_schedule.ec.antenna.resize(1)
antenna = pulse_schedule.ec.antenna[0]
antenna.name = "ec.antenna[0].name in DD 3.25.0"
antenna.launching_angle_pol.reference_name = \
    "ec.antenna[0].launching_angle_pol.reference_name in DD 3.25.0"
antenna.launching_angle_pol.reference.data = [2.1, 2.2, 2.3]
antenna.launching_angle_tor.reference_name = \
    "ec.antenna[0].launching_angle_tor.reference_name in DD 3.25.0"
antenna.launching_angle_tor.reference.data = [3.1, 3.2, 3.3]
antenna.phase.reference_name = "Phase reference name"

# And store the IDS in a DBEntry using DD 3.25.0
entry = imaspy.DBEntry(
    imaspy.ids_defs.ASCII_BACKEND, "autoconvert", 1, 1, dd_version="3.25.0"
)
entry.create()
entry.put(pulse_schedule)
entry.close()

# 2. Reopen the DBEntry with a default DD version:
entry = imaspy.DBEntry(imaspy.ids_defs.ASCII_BACKEND, "autoconvert", 1, 1)
entry.open()

# 3. Get the pulse schedule IDS
ps_autoconvert = entry.get("pulse_schedule")

print(f"{ps_autoconvert.ids_properties.version_put.data_dictionary=!s}")
print(f"{ps_autoconvert._dd_version=!s}")
# What do you notice?
#   version_put: 3.25.0
#   _dd_version: 3.40.0 -> the IDS was automatically converted

# 4. Print the data in the loaded IDS
imaspy.util.print_tree(ps_autoconvert)
# What do you notice?
#   1. The antenna AoS was renamed
#   2. Several nodes no longer exist!

print()
print("Disable autoconvert:")
print("====================")
# 5. Repeat steps 3 and 4 with autoconvert disabled:
ps_noconvert = entry.get("pulse_schedule", autoconvert=False)

print(f"{ps_noconvert.ids_properties.version_put.data_dictionary=!s}")
print(f"{ps_noconvert._dd_version=!s}")
# What do you notice?
#   version_put: 3.25.0
#   _dd_version: 3.25.0 -> the IDS was not converted!

# Print the data in the loaded IDS
imaspy.util.print_tree(ps_noconvert)
# What do you notice?
#   All data is here exactly as it was put at the beginnning of this exercise.
