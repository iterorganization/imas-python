# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
"""Functionality for converting IDSToplevels between DD versions.
"""

import copy
import logging
from packaging.version import Version
from typing import Optional

from imaspy.ids_factory import IDSFactory
from imaspy.ids_struct_array import IDSStructArray
from imaspy.ids_structure import IDSStructure
from imaspy.ids_toplevel import IDSToplevel


logger = logging.getLogger(__name__)


def convert_ids(
    toplevel: IDSToplevel,
    version: Optional[str],
    *,
    deepcopy: bool = False,
    xml_path: Optional[str] = None,
    factory: Optional[IDSFactory] = None,
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
    """
    if factory is None:
        factory = IDSFactory(version, xml_path)
    ids_name = toplevel.metadata.name
    if not factory.exists(ids_name):
        raise RuntimeError(
            f"There is no IDS with name {ids_name} in DD version {version}."
        )
    target_ids = factory.new(ids_name)

    source_version = Version(toplevel._version)
    target_version = Version(target_ids._version)
    logger.info(
        "Starting conversion for IDS %s of version %s to version %s.",
        ids_name,
        source_version,
        target_version,
    )
    if source_version > target_version:
        _copy_data(toplevel, target_ids, deepcopy, True, target_version)
    else:
        _copy_data(target_ids, toplevel, deepcopy, False, source_version)
    logger.info("Conversion for IDS %s finished.", ids_name)
    return target_ids


def _copy_data(
    new: IDSStructure,
    old: IDSStructure,
    deepcopy: bool,
    new_is_source: bool,
    old_version: Version,
) -> None:
    """Recursively copy data, following non-backwards-compatible (NBC) renames.

    Args:
        new: IDSStructure of the most recent DD version.
        old: IDSStructure of the least recent DD version.
        deepcopy: See :func:`convert_ids`.
        new_is_source: True if the ``new`` structure is the source and the ``old``
            structure the target of the copy operation. False otherwise.
        old_version: The DD version of the old structure.
    """
    old_items = []
    for item in new:
        # Resolve NBC changes, if needed
        nbc_description = getattr(item.metadata, "change_nbc_description", None)
        nbc_version = getattr(item.metadata, "change_nbc_version", None)
        resolved_nbc = False
        if nbc_description is None or Version(nbc_version) < old_version:
            # No NBC changes, or NBC change is not relevant
            old_item = getattr(old, item.metadata.name, None)
        elif nbc_description in {"aos_renamed", "leaf_renamed", "structure_renamed"}:
            # Find the referred path
            nbc_previous_name = item.metadata.change_nbc_previous_name
            old_item = old
            for name in nbc_previous_name.split("/"):
                if old_item is not None:
                    old_item = getattr(old_item, name, None)
            if old_item is not None:
                log_args = (item.metadata.path, old_item.metadata.path)
                logger.debug("Converting %s -> %s.", *log_args)
            else:
                logger.debug("Cannot resolve previous name %r", nbc_previous_name)
            resolved_nbc = True

        # Copy the data or recurse into sub-structures
        from_item, to_item = (item, old_item) if new_is_source else (old_item, item)
        if old_item is None:
            if new_is_source:  # TODO, only log if new_item has data
                logger.info(
                    "Cannot find element %s/%s in DD %s. Data is not copied.",
                    old.metadata.path,
                    nbc_previous_name if resolved_nbc else item.metadata.name,
                    old_version,
                )

        elif type(old_item) != type(item):
            # TODO: Should we use logging.error instead?
            raise RuntimeError("Non-matching types of old and new items!")

        elif isinstance(from_item, IDSStructArray):
            size = len(from_item.value)
            if size > 0:
                to_item.resize(size)
            for i in range(size):
                _copy_data(item[i], old_item[i], deepcopy, new_is_source, old_version)

        elif isinstance(from_item, IDSStructure):
            _copy_data(item, old_item, deepcopy, new_is_source, old_version)

        else:  # Data elements
            # TODO: only copy if value is non-default
            if deepcopy:
                # Using deepcopy to deal with STR_1D (list of strings)
                # For numpy arrays and basic types, copy would be sufficient
                to_item.value = copy.deepcopy(from_item.value)
            else:
                to_item.value = from_item.value

        if old_item is not None:
            old_items.append(old_item)

    # Find out which elements were removed in the newer DD version
    if not new_is_source:
        for item in old:
            if item not in old_items:  # TODO, only log if old_item has data
                logger.info(
                    "Cannot find element %s in DD %s. Data might not be copied.",
                    item.metadata.path,
                    new._version,
                )
