# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

import copy
import logging
import re
from typing import List

import numpy
import rich
from rich.console import Group
from rich.columns import Columns
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
import scipy.interpolate

from imaspy.ids_defs import IDS_TIME_MODE_HOMOGENEOUS
from imaspy.ids_mixin import IDSMixin
from imaspy.ids_primitive import IDSPrimitive
from imaspy.ids_structure import IDSStructure
from imaspy.ids_struct_array import IDSStructArray
from imaspy.ids_toplevel import IDSToplevel

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
    if homogeneousTime is None:
        homogeneousTime = node._time_mode

    if homogeneousTime is None:
        raise ValueError(
            "homogeneous_time is not specified in ids_properties nor given"
            " as keyword argument"
        )

    if homogeneousTime != IDS_TIME_MODE_HOMOGENEOUS:
        # TODO: implement also for IDS_TIME_MODE_INDEPENDENT
        # (and what about converting between time modes? this gets tricky fast)
        raise NotImplementedError(
            "resample is only implemented for IDS_TIME_MODE_HOMOGENEOUS"
        )

    def visitor(el):
        if not el.has_value:
            return
        if el.metadata.type.is_dynamic and el.metadata.name != "time":
            # effectively a guard to get only idsPrimitive
            # TODO: also support time axes as dimension of IDSStructArray
            time_axis = None
            if hasattr(el, "coordinates"):
                time_axis = el.coordinates.time_index
            if time_axis is None:
                logger.warning(
                    "No time axis found for dynamic structure %s", node._path
                )
            interpolator = scipy.interpolate.interp1d(
                old_time.value, el.value, axis=time_axis, **kwargs
            )
            el.value = interpolator(new_time)

    if not inplace:
        el = copy.deepcopy(node)
    else:
        el = node

    visit_children(visitor, el)

    if isinstance(el, IDSToplevel):
        el.time = new_time
    else:
        logger.warning(
            "Performing resampling on non-toplevel. "
            "Be careful to adjust your time base manually"
        )

    return el


def print_tree(structure, hide_empty_nodes=True):
    """Print the full tree of an IDS or IDS structure.

    Args:
        structure: IDS structure to print
        hide_empty_nodes: Show or hide nodes without value.
    """
    with numpy.printoptions(threshold=5, linewidth=1024, precision=4):
        rich.print(_make_tree(structure, hide_empty_nodes))


def _make_tree(structure, hide_empty_nodes=True, *, tree=None):
    """Build the ``rich.tree.Tree`` for display in :py:meth:`print_tree`.

    Args:
        structure: IDS structure to add to the tree
        hide_empty_nodes: Show or hide nodes without value.

    Keyword Args:
        tree: If provided, child items will be added to this Tree object. Otherwise a
            new Tree is constructed.
    """
    if tree is None:
        tree = Tree(f"[magenta]{structure.metadata.name}")

    if not isinstance(structure, (IDSStructure, IDSStructArray)):
        raise TypeError()

    for child in structure:
        if hide_empty_nodes and not child.has_value:
            continue

        if isinstance(child, IDSPrimitive):
            if not child.has_value:
                value = "[bright_black]-"
            else:
                value = Pretty(child.value)
            txt = f"[yellow]{child.metadata.name}[/]:"
            group = Columns([txt, value])
            tree.add(group)
        else:
            ntree = tree
            if isinstance(child, IDSStructure):
                txt = f"[magenta]{child._path}[/]"
                ntree = tree.add(txt)
            _make_tree(child, hide_empty_nodes, tree=ntree)

    return tree


def inspect(ids_node, hide_empty_nodes=False):
    """Inspect and print an IDS node.

    Inspired by `rich.inspect`, but customized to accomadate IDS specifics.
    """
    # Title
    if isinstance(ids_node, IDSToplevel):
        title = f"IDS: [green]{ids_node.metadata.name}"
    elif isinstance(ids_node, IDSStructure):
        title = f"IDS structure: [green]{ids_node._path}"
    elif isinstance(ids_node, IDSStructArray):
        title = f"IDS array of structures: [green]{ids_node._path}"
    else:
        title = f"IDS value: [green]{ids_node._path}"
    if ids_node._version:
        title += f" [/](DD version [bold cyan]{ids_node._version}[/])"

    renderables = []
    # Documentation
    renderables.append(Text(ids_node.metadata.documentation, style="inspect.help"))

    # Value
    if isinstance(ids_node, (IDSStructArray, IDSPrimitive)):
        val = Pretty(ids_node.value, indent_guides=True, max_length=10, max_string=60)
        value_text = Text.assemble(("value", "inspect.attr"), (" =", "inspect.equals"))
        table = Table.grid(padding=(0, 1), expand=False)
        table.add_column(justify="right")
        table.add_row(value_text, val)
        renderables.append(Panel(table, border_style="inspect.value.border"))

    attrs = set(name for name in dir(ids_node) if not name.startswith("_"))
    child_nodes = set()
    if isinstance(ids_node, IDSStructure):
        child_nodes = set(ids_node._children)
    attrs -= child_nodes
    attrs -= {"value"}

    # Properties
    if attrs:
        attrs_table = Table.grid(padding=(0, 1), expand=False)
        attrs_table.add_column(justify="right")

        for attr in sorted(attrs):
            try:
                value = getattr(ids_node, attr)
            except Exception:
                continue
            if callable(value):
                continue

            key_text = Text.assemble((attr, "inspect.attr"), (" =", "inspect.equals"))
            attrs_table.add_row(key_text, Pretty(value))

        renderables.append(Panel(attrs_table, title="Attributes"))

    if child_nodes:
        child_table = Table.grid(padding=(0, 1), expand=False)
        child_table.add_column(justify="right")

        for child in sorted(child_nodes):
            value = getattr(ids_node, child)
            if not value.has_value and hide_empty_nodes:
                continue
            key_text = Text.assemble((child, "inspect.attr"), (" =", "inspect.equals"))
            child_table.add_row(key_text, Pretty(value))

        renderables.append(Panel(child_table, title="Child nodes", style="cyan"))

    rich.print(Panel.fit(Group(*renderables), title=title, border_style="scope.border"))


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
    dd_element = node._structure_xml
    pattern = re.compile(query)
    matching_paths = []

    for element in dd_element.iter():
        path = element.get("path", "")
        if pattern.search(path) is not None:
            matching_paths.append(path)

    return matching_paths
