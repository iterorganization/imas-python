# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Represents the possible migrations between data dictionaries."""

from imaspy.migration import Rename, Scale


Rename("3.30.0", old_name="/path/from", new_name="/path/to")
Scale("3.30.0", "/path/to/scale", 2)
