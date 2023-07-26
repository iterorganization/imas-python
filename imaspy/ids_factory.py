# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

from functools import partial
import logging
from typing import Any, Iterable, Iterator, Optional

from imaspy import dd_zip
from imaspy.ids_toplevel import IDSToplevel


logger = logging.getLogger(__name__)


class IDSFactory:
    """Factory class generating IDSToplevel elements for specific DD versions.

    Example:

    >>> factory = IDSFactory()
    >>> factory.core_profiles()
    <imaspy.ids_toplevel.IDSToplevel object at 0x7f6afa03cdf0>
    >>> factory.new("core_profiles")
    <imaspy.ids_toplevel.IDSToplevel object at 0x7f6afa03ccd0>
    """

    # IDSToplevels expect these on their parent
    # TODO: see if we can eliminate them
    depth = 0
    _path = ""

    def __init__(
        self, version: Optional[str] = None, xml_path: Optional[str] = None
    ) -> None:
        """Create a new IDS Factory

        See :meth:`imaspy.dd_zip.dd_etree` for further details on the ``version`` and
        ``xml_path`` arguments.

        Args:
            version: DD version string, e.g. "3.38.1".
            xml_path: XML file containing data dictionary definition.
        """
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
        if name in self._ids_elements:
            # Note: returning a partial to mimic AL HLI, e.g. factory.core_profiles()
            return partial(IDSToplevel, self, self._ids_elements[name])
        raise AttributeError(f"{type(self)!r} object has no attribute {name!r}")

    def __iter__(self) -> Iterator[str]:
        """Iterate over the IDS names defined by the loaded Data Dictionary"""
        return iter(self._ids_elements)

    def new(self, ids_name: str) -> IDSToplevel:
        """Create a new IDSToplevel element for the provided IDS name

        Args:
            ids_name: Name of the IDS toplevel to create, e.g. "core_profiles".
        """
        if ids_name not in self._ids_elements:
            raise ValueError(f"IDS {ids_name} not found in the Data Dictionary.")
        return IDSToplevel(self, self._ids_elements[ids_name])

    def exists(self, ids_name: str) -> bool:
        """Check if an IDS type with the given name exists."""
        return ids_name in self._ids_elements

    @property
    def version(self) -> str:
        """Get the DD version used by this IDS factory"""
        return self._version