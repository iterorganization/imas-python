# ExplicitIndexer and ExplicitlyIndexed
# are taken from xarray c07160dd2d627a021e58515cbd7753c11fb56d94
#
# This code can be modified if you explicitly note your
# changes. However, it would be better to wrap these
# classes instead
#
#
# Copyright 2014-2020, xarray Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# xarray bundles portions of pandas, NumPy and Seaborn, all of which are available
# under a "3-clause BSD" license:
# - pandas: setup.py, xarray/util/print_versions.py
# - NumPy: xarray/core/npcompat.py
# - Seaborn: _determine_cmap_params in xarray/core/plot/utils.py
#
# xarray also bundles portions of CPython, which is available under the "Python
# Software Foundation License" in xarray/core/pycompat.py.
#
# xarray uses icons from the icomoon package (free version), which is
# available under the "CC BY 4.0" license.
#
# The full text of these licenses are included in the licenses directory.
class ExplicitlyIndexed:
    """Mixin to mark support for Indexer subclasses in indexing."""

    __slots__ = ()


class ExplicitIndexer:
    """Base class for explicit indexer objects.

    ExplicitIndexer objects wrap a tuple of values given by their ``tuple``
    property. These tuples should always have length equal to the number of
    dimensions on the indexed array.

    Do not instantiate BaseIndexer objects directly: instead, use one of the
    sub-classes BasicIndexer, OuterIndexer or VectorizedIndexer.
    """

    __slots__ = ("_key",)

    def __init__(self, key):
        if type(self) is ExplicitIndexer:
            raise TypeError("cannot instantiate base ExplicitIndexer objects")
        self._key = tuple(key)

    @property
    def tuple(self):
        return self._key

    def __repr__(self):
        return f"{type(self).__name__}({self.tuple})"
