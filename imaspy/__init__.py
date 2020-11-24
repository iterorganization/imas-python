# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.

from .version import version as __version_from_scm__

# Set the package version equal to the one grabbed from the
# Source Management System
# For git-desribe (this repository) it is based on tagged commits
__version__ = __version_from_scm__

from imaspy import (
    setup_logging,
    imas_ual_env_parsing,
    ids_classes,
)

from imaspy.backends import (
    file_manager,
    xarray_core_indexing,
    xarray_core_utils,
    common,
    ual,
)
