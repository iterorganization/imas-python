# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Represents the possible migrations between data dictionaries."""

from distutils.version import StrictVersion

from imaspy.logger import logger

MIGRATIONS = {}  # a dict keyed with "version"
# containing a dict (up, down) of lists of migrations to run 'up' and 'down'

UP = True
DOWN = False
READ = True
WRITE = False


def get_migration_tree(version_mem, version_file, path):
    vmem = StrictVersion(version_mem)
    vfile = StrictVersion(version_file)
    if vmem == vfile:
        logger.info("migration tree requested for identical versions, returning empty")
    elif vmem < vfile:
        vmin = vmem
        vmax = vfile
        direction = DOWN
    else:
        vmin = vfile
        vmax = vmem
        direction = UP

    for ver in sorted(MIGRATIONS.keys()):
        if ver < vmin or ver > vmax:
            continue

        MIGRATIONS[ver]


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
    up_paths = []
    down_paths = []
    paths = []

    def __init__(self, version):
        """Initialize the migration in direction and read/write mode"""
        self.version = StrictVersion(version)
        self.register()

    def transform_path(self, up, read, path):
        return path

    def transform_data(self, up, read, data):
        return data

    def register(self):
        """Register a migration object at this version and for each of its paths.
        Paths may be regexes or strings."""
        count = 0
        for direction in ("up", "down"):
            for path in self.getattr(direction + "_paths") + self.paths:
                count += 1
                MIGRATIONS.setdefault(self.version, {}).setdefault(
                    direction, {}
                ).setdefault(path, []).append(self)

        if count == 0:
            logger.error("Migration %s defined 0 paths, will not apply", self)


class Rename(Migration):
    """A simple migration which involves only renaming/moving a field."""

    def __init__(self, version, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name

        self.up_paths = [self.new_name]
        self.down_paths = [self.old_name]

        super(version)

    def transform_data(self, direction, mode, data):
        return data

    def transform_path(self, direction, mode, path):
        if direction == UP:  # then memory is new and backend is old
            return self.old_name
        else:
            return self.new_name


class Scale(Migration):
    """A simple migration which scales by a constant,
    such that new_value = constant * old_value"""

    def __init__(self, version, path, scale_factor):
        self.constant = scale_factor

    def transform_data(self, direction, mode, data):
        if (direction == UP and mode == READ) or (direction == DOWN and mode == WRITE):
            return data * self.constant
        else:
            return data / self.constant
