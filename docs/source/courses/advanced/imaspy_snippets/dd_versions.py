import imaspy

# 1. Create an IDSFactory
default_factory = imaspy.IDSFactory()

# 2. Print the DD version used by the IDSFactory
#
# This factory will use the default DD version, because we didn't explicitly indicate
# which version of the DD we want to use:
print("Default DD version:", default_factory.version)

# 3. Create an empty IDS
pf_active = default_factory.new("pf_active")
print("DD version used for pf_active:", pf_active._dd_version)
# What do you notice? This is the same version as the IDSFactory that was used to create
# it.

# 4. Create a new DBEntry
default_entry = imaspy.DBEntry(imaspy.ids_defs.MEMORY_BACKEND, "test", 0, 0)
default_entry.create()
# Alternative URI syntax when using AL5.0.0:
# default_entry = imaspy.DBEntry("imas:memory?path=.")
print("DD version used for the DBEntry:", default_entry._dd_version)
# What do you notice? It is the same default version again.
