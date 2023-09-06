# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

import numpy
import rich
import rich.columns
import rich.tree

from imaspy.ids_data_type import IDSDataType


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
    from imaspy.ids_primitive import (
        IDSPrimitive,
    )  # pylint: disable=import-outside-toplevel

    if isinstance(node, IDSPrimitive):
        # Leaf node
        func(node)
    else:
        if not leaf_only:
            func(node)
        for child in node:
            visit_children(func, child, leaf_only)


def print_tree(structure, hide_empty_nodes=True):
    with numpy.printoptions(threshold=5, linewidth=1024, precision=4):
        rich.print(make_tree(structure, hide_empty_nodes))


def make_tree(structure, hide_empty_nodes=True, *, tree=None):
    # FIXME: move imports to top of file after merging PR #127
    from imaspy.ids_primitive import IDSPrimitive
    from imaspy.ids_structure import IDSStructure
    from imaspy.ids_struct_array import IDSStructArray

    if tree is None:
        tree = rich.tree.Tree(structure.metadata.name)

    if not isinstance(structure, (IDSStructure, IDSStructArray)):
        raise TypeError()

    for child in structure:
        if hide_empty_nodes and not child.has_value:
            continue

        if isinstance(child, IDSPrimitive):
            if not child.has_value:
                value = "[bright_black]-"
            else:
                value = rich.pretty.Pretty(child.value)
            txt = f"[yellow]{child.metadata.name}[/]:"
            group = rich.columns.Columns([txt, value])
            tree.add(group)
        else:
            ntree = tree
            if isinstance(child, IDSStructure):
                txt = f"[magenta]{child._path}[/]"
                ntree = tree.add(txt)
            make_tree(child, hide_empty_nodes, tree=ntree)

    return tree
