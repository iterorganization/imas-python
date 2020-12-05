# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Represents the possible migrations between data dictionaries."""

from imaspy.logger import logger

MIGRATIONS = {}  # a dict keyed with "version"
# containing a dict (up, down) of lists of migrations to run 'up' and 'down'

UP = True
DOWN = False
READ = True
WRITE = False


def register_migration(cls, version):
    """Register a migration class at this version and for each of its cls.paths"""
    cls.version = version

    count = 0
    for direction in ('up', 'down'):
        for path in cls.call('{dir}_paths'.format(direction)) + cls.paths():
            count += 1
            MIGRATIONS.setdefault(version, {}) \
                      .setdefault(direction, {}) \
                      .setdefault(path, []) \
                      .append(cls)

    if count == 0:
        logger.error('Migration %s defined 0 paths, will not apply', cls)

    return cls


class Migration:
    """The base migration class, which instructs the backend
    how to read and write data in a different format and possibly
    spread over different locations.

    There are four cases to consider:
      - Reading from an older version
      - Reading from a newer version
      - Writing to an older version
      - Writing to a newer version
    """

    version = None
    def up_paths(cls):
        return []

    def down_paths(cls):
        return []

    def paths(cls):
        return []

    def __init__(self, direction, mode):
        """Initialize the migration in direction and read/write mode"""
        self.up = direction
        self.read = mode

    def read_from(self):
        """Base method which instructs the access layer to read from one
        or several fields to construct the in-memory representation.

        Returns a list of paths, data_types and ndims as a list of tuples.
        (should this become something like an 'address' object in imaspy?)
        """
        raise NotImplementedError("read_from needs to be implemented in your migration")

    def write_to(self):
        """Base method which instructs the access layer to write to one or several
        fields."""
        raise NotImplementedError("write_to needs to be implemented in your migration")


class Rename(Migration):
    """A simple migration which involves only renaming/moving a field."""

    def transform_data(self, data):
        return data

    def transform_path(self, path):
        if self.up
            return self.old_name
        else:
            return self.new_name


class Scale(Migration):
    """A simple migration which scales by a constant,
    such that new_value = constant * old_value"""
    
    constant = 1

    def read_from(self):
