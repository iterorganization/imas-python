# FileManager and DummyFileManager
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
import contextlib


class FileManager:
    """Manager for acquiring and closing a file object.

    Use FileManager subclasses (CachingFileManager in particular) on backend
    storage classes to automatically handle issues related to keeping track of
    many open files and transferring them between multiple processes.
    """

    def acquire(self, needs_lock=True):
        """Acquire the file object from this manager."""
        raise NotImplementedError()

    def acquire_context(self, needs_lock=True):
        """Context manager for acquiring a file. Yields a file object.

        The context manager unwinds any actions taken as part of acquisition
        (i.e., removes it from any cache) if an exception is raised from the
        context. It *does not* automatically close the file.
        """
        raise NotImplementedError()

    def close(self, needs_lock=True):
        """Close the file object associated with this manager, if needed."""
        raise NotImplementedError()


class DummyFileManager(FileManager):
    """FileManager that simply wraps an open file in the FileManager interface."""

    def __init__(self, value):
        self._value = value

    def acquire(self, needs_lock=True):
        del needs_lock  # ignored
        return self._value

    @contextlib.contextmanager
    def acquire_context(self, needs_lock=True):
        del needs_lock
        yield self._value

    def close(self, needs_lock=True):
        del needs_lock  # ignored
        self._value.close()
