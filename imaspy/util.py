# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.


def visit_children(node, fun, leaf_only=False):
    """walk all children of this structure in order and execute fun on them"""
    # you will have fun
    if hasattr(node, "__iter__"):
        if not leaf_only:
            fun(node)
        for child in node:
            visit_children(child, fun, leaf_only)
    else:  # it must be a child then?
        fun(node)
