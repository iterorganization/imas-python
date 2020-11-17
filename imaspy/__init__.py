# This file is part of IMASPy.
#
# IMASPy is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IMASPy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with IMASPy.  If not, see <https://www.gnu.org/licenses/>.

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
