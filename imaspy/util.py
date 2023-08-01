# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.


def visit_children(node, fun, leaf_only=False):
    """walk all children of this structure in order and execute fun on them"""
    from imaspy.ids_primitive import IDSPrimitive

    if isinstance(node, IDSPrimitive):
        # Leaf node
        fun(node)
    else:
        if not leaf_only:
            fun(node)
        for child in node:
            visit_children(child, fun, leaf_only)
