# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Represents the possible migrations between data dictionaries."""

from imaspy.migration import Rename, check_migration_order

# highest version first

Rename("3.30.0", old_name="/path/from", new_name="/path/to")


# TODO: build Rename migrations from
# change_nbc_version="3.30.0"
# change_nbc_description="leaf_renamed"
# change_nbc_previous_name="potential_plasma">

Rename("3.29.1", old_name="/path/from2", new_name="/path/to2")

check_migration_order()
