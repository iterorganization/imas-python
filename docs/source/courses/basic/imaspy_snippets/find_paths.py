import imaspy.util

factory = imaspy.IDSFactory()
core_profiles = factory.core_profiles()

print("Paths containing `rho`:")
print(imaspy.util.find_paths(core_profiles, "rho"))
print()

print("Paths containing `rho`, not followed by `error`:")
print(imaspy.util.find_paths(core_profiles, "rho(?!.*error)"))
print()

print("All paths ending with `time`:")
print(imaspy.util.find_paths(core_profiles, "time$"))
print()
