# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.


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
