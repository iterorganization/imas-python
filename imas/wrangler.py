# This file is part of IMAS-Python.
# You should have received the IMAS-Python LICENSE file with this project.
"""Wrangling: convert between flat dot-path dicts and IMAS IDS objects."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np

from . import IDSFactory
from .backends.netcdf.iterators import indexed_tree_iter
from .ids_primitive import IDSPrimitive
from .ids_struct_array import IDSStructArray
from .ids_structure import IDSStructure
from .ids_toplevel import IDSToplevel

logger = logging.getLogger(__name__)

try:
    import awkward as ak
except ImportError:
    ak = None
    logger.debug("Could not import awkward-array", exc_info=True)


# ---------------------------------------------------------------------------
# wrangle: flat dict → IDS objects
# ---------------------------------------------------------------------------


def wrangle(flat: Dict, version: Optional[str] = None) -> Dict[str, IDSToplevel]:
    """Convert a flat dot-path dict into IDS toplevel objects.

    Args:
        flat: Keys are dot-separated paths like
            ``"equilibrium.time_slice.profiles_1d.psi"``.  Values are
            scalars, :class:`numpy.ndarray`, or :class:`awkward.Array`.
        version: Data Dictionary version string.  When ``None`` (default)
            the installed default DD version is used.

    Returns:
        Dict mapping IDS name → :class:`~imas.ids_toplevel.IDSToplevel`.
    """
    factory = IDSFactory(version) if version is not None else IDSFactory()
    wrangled: Dict[str, IDSToplevel] = {}

    for key, value in flat.items():
        ids_name, dot_path = key.split(".", 1)
        slash_path = dot_path.replace(".", "/")

        if ids_name not in wrangled:
            wrangled[ids_name] = factory.new(ids_name)

        _put_value(slash_path, value, wrangled[ids_name])

    return wrangled


def _put_value(slash_path: str, value: Any, node: IDSStructure) -> None:
    """Recursively navigate *node* along *slash_path* and set the leaf.

    Args:
        slash_path: Remaining IDS path using ``"/"`` as separator.
        value: Value to assign.  For AoS nodes this must be indexable
            (numpy array, ak.Array, or list) with a leading dimension equal
            to the number of AoS elements.
        node: Current IDS structure node (IDSToplevel or IDSStructure).
    """
    if "/" not in slash_path:
        # Leaf — assign directly via the IDS node
        node[slash_path].value = value
        return

    part, rest = slash_path.split("/", 1)
    child = node[part]

    if isinstance(child, IDSStructArray):
        # AoS: value has a leading dimension for the array elements
        N = len(value)
        if child.size == 0:
            child.resize(N)
        elif child.size != N:
            raise ValueError(
                f"Inconsistent AoS size at '{part}': "
                f"IDS has {child.size} elements, flat value has {N}."
            )
        for idx in range(N):
            _put_value(rest, value[idx], child[idx])

    elif isinstance(child, IDSStructure):
        _put_value(rest, value, child)

    else:
        # Primitive reached before end of path — should not happen for valid DD paths
        raise ValueError(
            f"Path component '{part}' resolved to a primitive node "
            f"but the remaining path '{rest}' is non-empty."
        )


# ---------------------------------------------------------------------------
# unwrangle: IDS objects → flat dict
# ---------------------------------------------------------------------------


def unwrangle(
    locations: List[str],
    ids_dict: Dict[str, IDSToplevel],
) -> Dict[str, Any]:
    """Convert IDS toplevel objects back to a flat dot-path dict.

    Uses :func:`~imas.backends.netcdf.iterators.indexed_tree_iter` to walk
    the IDS tree without going through the NetCDF tensorizer or NCMetadata.

    * Regular (homogeneous) AoS data is returned as a :class:`numpy.ndarray`
      with the AoS dimensions as the leading axes.
    * Ragged AoS data (elements with different array lengths) is returned as
      an :class:`awkward.Array`.
    * Scalars and non-AoS arrays are returned as plain numpy arrays / scalars.

    Args:
        locations: Dot-separated paths to extract, e.g.
            ``["equilibrium.time", "thomson_scattering.channel.t_e.data"]``.
        ids_dict: Mapping of IDS name → IDSToplevel.

    Returns:
        Dict mapping each location to its extracted value.
    """
    # Group requested slash-paths per IDS name
    by_ids: Dict[str, List[str]] = {}
    for loc in locations:
        ids_name, dot_path = loc.split(".", 1)
        by_ids.setdefault(ids_name, []).append(dot_path.replace(".", "/"))

    flat: Dict[str, Any] = {}

    for ids_name, slash_paths in by_ids.items():
        ids = ids_dict[ids_name]

        # Walk the full IDS tree once, collecting primitive leaf nodes.
        # data[slash_path] = {aos_index_tuple: node}
        data: Dict[str, Dict] = {}
        for aos_idx, node in indexed_tree_iter(ids):
            if not isinstance(node, IDSPrimitive):
                continue
            if not node.has_value:
                continue
            data.setdefault(node.metadata.path_string, {})[aos_idx] = node

        for slash_path in slash_paths:
            dot_key = ids_name + "." + slash_path.replace("/", ".")

            if slash_path not in data:
                logger.warning(
                    "Path '%s' not found or empty in IDS '%s'",
                    slash_path,
                    ids_name,
                )
                continue

            nodes_dict = data[slash_path]

            if () in nodes_dict:
                # No AoS ancestor — return the single leaf value directly
                flat[dot_key] = nodes_dict[()].value
            else:
                flat[dot_key] = _collect_aos_value(nodes_dict, dot_key)

    return flat


def _collect_aos_value(
    nodes_dict: Dict[tuple, IDSPrimitive],
    dot_key: str,
) -> Any:
    """Reconstruct a numpy array or ak.Array from an AoS nodes dict.

    *nodes_dict* maps AoS index tuples ``(i,)``, ``(i, j)``, … to leaf
    :class:`~imas.ids_primitive.IDSPrimitive` nodes.

    For homogeneous data (all leaf values have the same shape) the result is
    a :class:`numpy.ndarray` of shape ``(*aos_shape, *leaf_shape)``.

    For ragged data the result is an :class:`awkward.Array`.
    """
    indices = sorted(nodes_dict.keys())
    ndims_aos = len(indices[0])  # number of AoS nesting levels

    # Determine the size of each AoS dimension
    aos_shape = tuple(max(idx[d] for idx in indices) + 1 for d in range(ndims_aos))

    # Collect values in sorted index order to test homogeneity
    values = [nodes_dict[idx].value for idx in indices]
    shapes = [np.shape(v) for v in values]
    unique_shapes = set(shapes)

    all_filled = len(indices) == int(np.prod(aos_shape))

    if len(unique_shapes) == 1 and all_filled:
        # ----------------------------------------------------------------
        # Homogeneous and fully filled: reshape into a regular numpy array
        # ----------------------------------------------------------------
        leaf_shape = shapes[0]
        leaf_val = np.asarray(values[0])
        result = np.empty(aos_shape + leaf_shape, dtype=leaf_val.dtype)
        for idx_tuple, node in nodes_dict.items():
            result[idx_tuple] = node.value
        return result

    else:
        # ----------------------------------------------------------------
        # Ragged or sparse: build a nested list and wrap in ak.Array
        # ----------------------------------------------------------------
        if ak is None:
            raise ImportError(
                "awkward-array is required for ragged IDS data. "
                "Install it with: pip install imas-python[awkward]"
            )
        nested = _build_nested_list(
            nodes_dict, ndims_aos, aos_shape, depth=0, prefix=()
        )
        return ak.Array(nested)


def split_location_across_ids(locations: List[str]) -> Dict[str, List[str]]:
    """Group dot-path locations by IDS name, returning slash-separated sub-paths.

    Args:
        locations: Dot-separated paths like
            ``["equilibrium.time", "equilibrium.time_slice.profiles_1d.psi"]``.

    Returns:
        Dict mapping IDS name to a list of slash-separated sub-paths.
    """
    ids_locations: Dict[str, List[str]] = {}
    for location in locations:
        ids_name, dot_path = location.split(".", 1)
        ids_locations.setdefault(ids_name, []).append(dot_path.replace(".", "/"))
    return ids_locations


def _build_nested_list(
    nodes_dict: Dict[tuple, IDSPrimitive],
    ndims_aos: int,
    aos_shape: tuple,
    depth: int,
    prefix: tuple,
) -> list:
    """Recursively build a nested Python list matching the AoS structure.

    At the innermost level (``depth == ndims_aos - 1``) each slot holds
    the raw leaf value (numpy array or scalar).  Absent slots are ``None``.
    """
    size = aos_shape[depth]

    if depth == ndims_aos - 1:
        # Innermost AoS level: collect leaf values
        row = []
        for i in range(size):
            node = nodes_dict.get(prefix + (i,))
            row.append(node.value if node is not None else None)
        return row
    else:
        return [
            _build_nested_list(
                nodes_dict, ndims_aos, aos_shape, depth + 1, prefix + (i,)
            )
            for i in range(size)
        ]
