# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
""" Represents the possible migrations between data dictionaries."""

from distutils.version import StrictVersion

from imaspy.logger import logger

MIGRATIONS_UP = {}  # a dict keyed with paths for migrating up (mem newer than file)
MIGRATIONS_DOWN = {}  # each of the values is a list of migrations

UP = True
DOWN = False
READ = True
WRITE = False


def get_migration_tree(version_mem, version_file, path):

    for ver in sorted(MIGRATIONS.keys()):
        if ver < vmin or ver > vmax:
            continue

        MIGRATIONS[ver]

def transform_path(version_mem, version_file, mode, path):
    """Find the list of paths to fetch from/write to"""
    # For this path, get the list of migrations and walk through them
    # (there will only be a few, so it is not so expensive)
    vmem = StrictVersion(version_mem)
    vfile = StrictVersion(version_file)
    if vmem == vfile:
        return [path]
    elif vmem < vfile:
        vmin = vmem
        vmax = vfile
        direction = DOWN
    else:
        vmin = vfile
        vmax = vmem
        direction = UP

    if direction == UP:
        for migration in MIGRATIONS_UP[path][::-1]:
            # vmem > vfile, and we would like to know which paths a mem path corresponds to.
            # we therefore have to go down from vmem to vfile
            # the migrations are ordered such that the oldest one come first
            if migration.version > vmem:
                continue
            if migration.version < 

def combine_migrations(one, two):
    """Combine migrations one and two such that they present a single 'front'"""
    pass


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

    def transform_path(self, direction, mode, path):
        return path

    def transform_data(self, direction, mode, data):
        return data

    def register(self):
        """Register a migration object at this version and for each of its paths."""
        count = 0
        for path in self.up_paths + self.paths:
            count += 1
            MIGRATIONS_UP.setdefault(path, []).append(self)
        for path in self.down_paths + self.paths:
            count += 1
            MIGRATIONS_DOWN.setdefault(path, []).append(self)

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


def check_migration_order():
    for mig_list in MIGRATIONS_UP + MIGRATIONS_DOWN:
        check_migration_list_order(mig_list)


def check_migration_list_order(mig_list):
    last_version = None
    for migration in mig_list:
        if last_version is None or last_version < migration.version:
            last_version = migration.version
        else:
            logger.critical("Migration %s at %s should be defined earlier",
                            migration, last_version)
            return
