# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

import logging
import re
from typing import List

from imaspy.ids_mixin import IDSMixin
from imaspy.ids_primitive import IDSPrimitive

logger = logging.getLogger(__name__)


def visit_children(func, node, leaf_only=True):
    """Apply a function to node and its children

    IMASPy objects generally live in a tree structure. Similar to Pythons
    :py:meth:`map`, this method can be used to apply a function to objects
    within this tree structure.

    Args:
        func: Function to apply to each selected node.
        node: Node that function ``func`` will be applied to.
            The function will be applied to the node itself and
            all its descendants, depending on `leaf_only`.
        leaf_only: Apply function to:

            * ``True``: Only leaf nodes, not internal nodes
            * ``False``: All nodes, including internal nodes

    Example:
        .. code-block:: python

            # Print all filled leaf nodes in a given IMASPy IDSToplevel
            visit_children(
                lambda x: print(x) if x.has_value else None,
                toplevel,
            )
    """
    if isinstance(node, IDSPrimitive):
        # Leaf node
        func(node)
    else:
        if not leaf_only:
            func(node)
        for child in node:
            visit_children(func, child, leaf_only)


def resample(node, old_time, new_time, homogeneousTime=None, inplace=False, **kwargs):
    """Resample all primitives in their time dimension to a new time array"""
    import imaspy._util as _util

    return _util.resample_impl(
        node, old_time, new_time, homogeneousTime, inplace, **kwargs
    )


def print_tree(structure, hide_empty_nodes=True):
    """Print the full tree of an IDS or IDS structure.

    Args:
        structure: IDS structure to print
        hide_empty_nodes: Show or hide nodes without value.
    """
    import imaspy._util as _util

    return _util.print_tree_impl(structure, hide_empty_nodes)


def inspect(ids_node, hide_empty_nodes=False):
    """Inspect and print an IDS node.

    Inspired by `rich.inspect`, but customized to accomadate IDS specifics.
    """
    import imaspy._util as _util

    return _util.inspect_impl(ids_node, hide_empty_nodes)


def find_paths(node: IDSMixin, query: str) -> List[str]:
    """Find all paths in the provided DD node (including children) that match the query.

    Matching is checked with :external:py:func:`re.search`.

    Args:
        node: An IDS node (e.g. an IDS or sub-structure) to search in.
        query: Regular Expression. See the Python doumentation for :external:py:mod:`re`
            for more details.

    Returns:
        A list of matching paths.

    Example:
        >>> factory = imaspy.IDSFactory()
        >>> core_profiles = factory.new("core_profiles")
        >>> imaspy.util.find_paths(core_profiles, "(^|/)time$")
        ['profiles_1d/time', 'profiles_2d/time', 'time']
    """
    dd_element = node.metadata._structure_xml
    pattern = re.compile(query)
    matching_paths = []

    for element in dd_element.iter():
        path = element.get("path", "")
        if pattern.search(path) is not None:
            matching_paths.append(path)

    return matching_paths


def calc_hash(node: IDSMixin) -> bytes:
    """Calculate the hash of the provided IDS object.

    Hashes are calculated as follows:

    1.  Data nodes:

        a.  ``STR_0D``: hash of value (encoded as UTF-8)
        b.  ``STR_1D``: hash of concatenation of

            -   Length of the STR_1D (64-bit little-endian integer)
            -   hash of value[0] (encoded as UTF-8)
            -   hash of value[1] (encoded as UTF-8)
            -   ...

        c.  ``INT_0D``: hash of value (32-bit little-endian signed integer)
        d.  ``FLT_0D``: hash of value (64-bit IEEE 754 floating point number)
        e.  ``CPX_0D``: hash of value (128-bit: real, imag)
        f.  ``ND`` arrays: hash of concatenation of

            -   Dimension (8-bit integer)
            -   Shape (dimension * 64-bits little-endian integer)
            -   Concatenated data (little-endian, C memory layout)

    2.  Array of structures nodes: hash of concatenation of

        -   Length of the AoS (64-bit little-endian integer)
        -   Hash of structure[0]
        -   Hash of structure[1]
        -   ...

    3.  Structure nodes:

        a.  Sort all children alphabetically
        b.  Remove empty children. Children are empty when:

            -   ``INT_0D``: equal to ``EMPTY_INT``
            -   ``FLT_0D``: equal to ``EMPTY_FLOAT``
            -   ``CPX_0D``: equal to ``EMPTY_COMPLEX``
            -   ``ND`` arrays: array is empty
            -   ``STR_0D``: equal to ``""``
            -   ``STR_1D``: length is 0
            -   Array of structures: length is 0
            -   Structure: all children are empty

        c.  Remove ``ids_properties/version_put`` structure
        d.  Calculate hash of concatenation of

            -   Name of child[0] (encoded as UTF-8)
            -   Hash of child[0]
            -   ...

    The hash function used is ``xxhash.xxh3_64`` from the ``xxhash`` package.

    Example:
        .. code-block:: python

            cp = imaspy.IDSFactory().core_profiles()
            cp.ids_properties.homogeneous_time = 0
            
            print(imaspy.util.calc_hash(cp).hex())  # 3b9b929756a242fd
    """
    return node._xxhash()
