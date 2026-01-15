# This file is part of IMAS-Python.
# You should have received the IMAS-Python LICENSE file with this project.
"""Tools for generating IDSs from a Data Dictionary version."""

from __future__ import annotations

import logging
import pathlib
from collections.abc import Iterable, Iterator
from functools import partial
from typing import Any

from imas import dd_zip
from imas.exception import IDSNameError
from imas.ids_toplevel import IDSToplevel

logger = logging.getLogger(__name__)


class IDSFactory:
    """Factory class generating IDSToplevel elements for specific DD versions.

    Example:

    >>> factory = IDSFactory()
    >>> factory.core_profiles()
    <imas.ids_toplevel.IDSToplevel object at 0x7f6afa03cdf0>
    >>> factory.new("core_profiles")
    <imas.ids_toplevel.IDSToplevel object at 0x7f6afa03ccd0>
    """

    def __init__(
        self, version: str | None = None, xml_path: str | pathlib.Path | None = None
    ) -> None:
        """Create a new IDS Factory

        See :meth:`imas.dd_zip.dd_etree` for further details on the ``version`` and
        ``xml_path`` arguments.

        Args:
            version: DD version string, e.g. "3.38.1".
            xml_path: XML file containing data dictionary definition.
        """
        if version is None and xml_path is None:
            # Defer loading the DD definitions until we really need them
            self.__deferred_init = True
        else:
            # If a specific version or xml_path is requested, we still load immediately
            # so any exceptions are raise when creating the IDSfactory
            self.__do_init(version, xml_path)
            self.__deferred_init = False

    def __do_init(self, version: str | None, xml_path: str | pathlib.Path | None):
        """Actual initialization logic"""
        self._xml_path = xml_path
        self._etree = dd_zip.dd_etree(version, xml_path)
        self._ids_elements = {
            ele.get("name"): ele for ele in self._etree.findall("IDS")
        }

        version_element = self._etree.find("version")
        if version_element is not None:
            self._version = version_element.text
        elif version:
            self._version = version
        else:
            logger.warning("Ignoring missing Data Dictionary version in loaded DD.")
            self._version = "-1"
        if version and version != self._version:
            raise RuntimeError(
                f"There is a mismatch between the requested DD version {version} and "
                f"the actual loaded DD version {self._version}."
            )

    def __copy__(self) -> "IDSFactory":
        return self

    def __deepcopy__(self, memo) -> "IDSFactory":
        return self

    def __dir__(self) -> Iterable[str]:
        return sorted(set(object.__dir__(self)).union(self._ids_elements))

    def __getattr__(self, name: str) -> Any:
        # Actually initialize when we deferred it before
        if self.__deferred_init:
            self.__do_init(None, None)
            self.__deferred_init = False
            return getattr(self, name)
        # Check if the name matches any IDS and return a 'constructor' for it
        if name in self._ids_elements:
            # Note: returning a partial to mimic AL HLI, e.g. factory.core_profiles()
            return partial(IDSToplevel, self, self._ids_elements[name])
        raise AttributeError(f"'IDSFactory' has no attribute {name!r}")

    def __iter__(self) -> Iterator[str]:
        """Iterate over the IDS names defined by the loaded Data Dictionary"""
        return iter(self._ids_elements)

    def ids_names(self) -> list[str]:
        """Get a list of all known IDS names in the loaded Data Dictionary"""
        return list(self._ids_elements)

    def new(self, ids_name: str, *, _lazy: bool = False) -> IDSToplevel:
        """Create a new IDSToplevel element for the provided IDS name

        Args:
            ids_name: Name of the IDS toplevel to create, e.g. "core_profiles".

        Keyword args:
            _lazy: Internal usage only! Create an IDS Toplevel suitable for lazy loading
                when set to True.
        """
        if ids_name not in self._ids_elements:
            raise IDSNameError(ids_name, self)
        return IDSToplevel(self, self._ids_elements[ids_name], _lazy)

    def exists(self, ids_name: str) -> bool:
        """Check if an IDS type with the given name exists."""
        return ids_name in self._ids_elements

    @property
    def version(self) -> str:
        """Get the DD version used by this IDS factory"""
        return self._version

    # dd_version is an alias for version
    dd_version = version
