# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""Functionality for converting IDSToplevels between DD versions.
"""

import copy
from functools import lru_cache
import logging
from xml.etree.ElementTree import Element, ElementTree
from packaging.version import Version
from typing import Dict, Optional, Set

from imaspy.ids_factory import IDSFactory
from imaspy.ids_path import IDSPath
from imaspy.ids_struct_array import IDSStructArray
from imaspy.ids_structure import IDSStructure
from imaspy.ids_toplevel import IDSToplevel


logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
class DDVersionMap:
    RENAMED_DESCRIPTIONS = {"aos_renamed", "leaf_renamed", "structure_renamed"}
    STRUCTURE_TYPES = {"structure", "struct_array"}

    def __init__(
        self,
        ids_name: str,
        old_version: ElementTree,
        new_version: ElementTree,
        version_old: Version,
    ):
        self.ids_name = ids_name
        self.old_version = old_version
        self.new_version = new_version
        self.version_old = version_old

        # Dictionaries providing the mapping
        # - When no changes have occurred (which is assumed to be the default case), the
        #   path is not present in the dictionary.
        # - When an element is renamed it maps the old to the new name (and vice versa).
        # - When an element does not exist in the other version, it is mapped to None.
        self.old_to_new: Dict[str, Optional[str]] = {}  # Map of old_path -> new_path
        self.new_to_old: Dict[str, Optional[str]] = {}  # Map of new_path -> old_path

        old_ids_object = old_version.find(f"IDS[@name='{ids_name}']")
        new_ids_object = new_version.find(f"IDS[@name='{ids_name}']")
        if old_ids_object is None or new_ids_object is None:
            raise ValueError(
                f"Cannot find IDS {ids_name} in the provided DD definitions."
            )
        self._build_map(old_ids_object, new_ids_object)

    def _check_data_type(self, old_item: Element, new_item: Element):
        """Check if data type hasn't changed.

        Record paths in mapping if data type change is unsupported.

        Returns:
            True iff the data type of both items are the same.
        """
        if new_item.get("data_type") != old_item.get("data_type"):
            new_path = new_item.get("path")
            old_path = old_item.get("path")
            assert new_path is not None
            assert old_path is not None
            logger.error(
                "Data type of %s changed from %s to %s. This change is not "
                "supported by IMASPy: no conversion will be done.",
                new_item.get("path"),
                old_item.get("data_type"),
                new_item.get("data_type"),
            )
            self.new_to_old[new_path] = None
            self.old_to_new[old_path] = None
            return False
        return True

    def _build_map(self, old: Element, new: Element) -> None:
        """Build the NBC translation map between old <-> new."""
        old_paths = {field.get("path", ""): field for field in old.iterfind(".//field")}
        new_paths = {field.get("path", ""): field for field in new.iterfind(".//field")}
        old_path_set = set(old_paths)
        new_path_set = set(new_paths)

        def get_old_path(path: str, previous_name: str) -> str:
            """Calculate old path from the path and change_nbc_previous_name"""
            # Apply rename
            i_slash = path.rfind("/")
            if i_slash != -1:
                old_path = path[:i_slash] + "/" + previous_name
            else:
                old_path = previous_name
            # Apply any parent AoS/structure rename
            i_slash = old_path.find("/")
            while i_slash != -1:
                parent = old_path[:i_slash]
                parent_rename = self.new_to_old.get(parent)
                if parent_rename:
                    if new_paths[parent].get("data_type") in self.STRUCTURE_TYPES:
                        old_path = parent_rename + old_path[i_slash:]
                        i_slash = len(parent)
                i_slash = old_path.find("/", i_slash + 1)
            return old_path

        # Iterate through all NBC metadata and add entries
        for new_item in new.iterfind(".//field[@change_nbc_description]"):
            new_path = new_item.get("path")
            assert new_path is not None
            nbc_description = new_item.get("change_nbc_description")
            nbc_version = new_item.get("change_nbc_version")
            if Version(nbc_version) < self.version_old:
                continue
            if nbc_description in DDVersionMap.RENAMED_DESCRIPTIONS:
                previous_name = new_item.get("change_nbc_previous_name")
                assert previous_name is not None
                old_path = get_old_path(new_path, previous_name)
                old_item = old_paths.get(old_path)
                if old_item is None:
                    logger.debug(
                        "Skipped NBC change for %r: renamed path %r not found in %s.",
                        new_path,
                        old_path,
                        self.version_old,
                    )
                elif self._check_data_type(old_item, new_item):
                    self.new_to_old[new_path] = old_path
                    self.old_to_new[old_path] = new_path
                    if old_item.get("data_type") in DDVersionMap.STRUCTURE_TYPES:
                        # Add entries for common sub-elements
                        for path in old_paths:
                            if path.startswith(old_path):
                                npath = path.replace(old_path, new_path, 1)
                                if npath in new_path_set:
                                    self.new_to_old[npath] = path
                                    self.old_to_new[path] = npath
            else:  # Ignore unknown NBC changes
                log_args = (nbc_description, new_path)
                logger.error("Ignoring unsupported NBC change: %r for %r.", *log_args)

        # Check if all common elements are still valid
        for common_path in old_path_set & new_path_set:
            if common_path in self.new_to_old or common_path in self.old_to_new:
                continue  # This path is part of an NBC change, we can skip it
            self._check_data_type(old_paths[common_path], new_paths[common_path])

        # Record missing items
        self._map_missing(True, new_path_set.difference(old_path_set, self.new_to_old))
        self._map_missing(False, old_path_set.difference(new_path_set, self.old_to_new))

    def _map_missing(self, is_new: bool, missing_paths: Set[str]):
        rename_map = self.new_to_old if is_new else self.old_to_new
        # Find all structures which have a renamed sub-item
        structures_with_renames = set()
        for path in rename_map:
            i_slash = path.find("/")
            while i_slash != -1:
                structures_with_renames.add(path[:i_slash])
                i_slash = path.find("/", i_slash + 1)

        skipped_paths = set()
        for path in sorted(missing_paths):
            # Only mark a non-existing structure if there are no renames inside it, so a
            # structure marked in the rename_map as None can be skipped completely.
            if path not in structures_with_renames:
                # Only mark if there is no parent structure already skipped
                i_slash = path.find("/")
                while i_slash != -1:
                    if path[:i_slash] in skipped_paths:
                        break
                    i_slash = path.find("/", i_slash + 1)
                else:
                    skipped_paths.add(path)
        for path in skipped_paths:
            rename_map[path] = None


def convert_ids(
    toplevel: IDSToplevel,
    version: Optional[str],
    *,
    deepcopy: bool = False,
    xml_path: Optional[str] = None,
    factory: Optional[IDSFactory] = None,
    target: Optional[IDSToplevel] = None,
) -> IDSToplevel:
    """Convert an IDS to the specified data dictionary version.

    Newer data dictionary versions may introduce non-backwards-compatible (NBC) changes.
    For example, the ``global_quantities.power_from_plasma`` quantity in the ``wall``
    IDS was renamed in DD version 3.31.0 to ``global_quantities.power_incident``. When
    converting from a version older than 3.31.0 to a version that is newer than that,
    this method will migrate the data.

    By default, this method performs a `shallow copy` of numerical data. All
    multi-dimensional numpy arrays from the returned IDS share their data with the
    original IDS. When performing `in-place` operations on numpy arrays, the data will
    be changed in both IDSs! If this is not desired, you may set the ``deepcopy``
    keyword argument to True.

    Args:
        toplevel: The IDS element to convert.
        version: The data dictionary version to convert to, for example "3.38.0". Must
            be None when using ``xml_path`` or ``factory``.

    Keyword Args:
        deepcopy: When True, performs a deep copy of all data. When False (default),
            numpy arrays are not copied and the converted IDS shares the same underlying
            data buffers.
        xml_path: Path to a data dictionary XML file that should be used instead of the
            released data dictionary version specified by ``version``.
        factory: Existing IDSFactory to use for as target version.
        destination: Use this IDSToplevel as target toplevel instead of creating one.
    """
    ids_name = toplevel.metadata.name
    if target is None:
        if factory is None:
            factory = IDSFactory(version, xml_path)
        if not factory.exists(ids_name):
            raise RuntimeError(
                f"There is no IDS with name {ids_name} in DD version {version}."
            )
        target_ids = factory.new(ids_name)
    else:
        target_ids = target

    source_version = Version(toplevel._version)
    target_version = Version(target_ids._version)
    logger.info(
        "Starting conversion of IDS %s from version %s to version %s.",
        ids_name,
        source_version,
        target_version,
    )

    source_is_new = source_version > target_version
    source_etree = toplevel._parent._etree
    target_etree = target_ids._parent._etree
    if source_is_new:
        version_map = DDVersionMap(ids_name, target_etree, source_etree, target_version)
    else:
        version_map = DDVersionMap(ids_name, source_etree, target_etree, source_version)

    _copy_structure(toplevel, target_ids, deepcopy, source_is_new, version_map)

    return target_ids


def _copy_structure(
    source: IDSStructure,
    target: IDSStructure,
    deepcopy: bool,
    source_is_new: bool,
    version_map: DDVersionMap,
):
    """Recursively copy data, following NBC renames.

    Args:
        source: Source structure.
        target: Target structure.
        deepcopy: See :func:`convert_ids`.
        source_is_new: True iff the DD version of the source is newer than that of the
            target.
        version_map: Version map containing NBC renames.
    """
    rename_map = version_map.new_to_old if source_is_new else version_map.old_to_new
    for item in source:
        if not item.has_value:
            continue

        path = str(item.metadata.path)
        if path in rename_map:
            if rename_map[path] is None:
                logger.info("Element %r does not exist in the target IDS.", path)
                continue
            else:
                target_item = IDSPath(rename_map[path]).goto(target)
        else:  # Must exist in the target if path is not recorded in the map
            target_item = target[item.metadata.name]

        if isinstance(item, IDSStructArray):
            size = len(item)
            target_item.resize(size)
            for i in range(size):
                _copy_structure(
                    item[i], target_item[i], deepcopy, source_is_new, version_map
                )
        elif isinstance(item, IDSStructure):
            _copy_structure(item, target_item, deepcopy, source_is_new, version_map)
        else:
            if deepcopy:
                # No nested types are used as data, so a shallow copy is sufficient
                target_item.value = copy.copy(item.value)
            else:
                target_item.value = item.value
