# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Represents the possible migrations between data dictionaries."""

from imaspy.migration import register_migration, Rename


@register_migration("3.30.0")
class RenameBtorToBtoroidal(Rename):
    old_name = "/path/from"
    new_name = "/path/to"
