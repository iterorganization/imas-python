# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""This file contains the implementation of all utility functions that need external
modules. Implementation has been removed from util.py to improve the performance of
``import imaspy``.
"""

import copy
import logging
from typing import Union

import numpy
import rich
import scipy.interpolate
from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from imaspy.ids_base import IDSBase
from imaspy.ids_data_type import IDSDataType
from imaspy.ids_defs import IDS_TIME_MODE_HOMOGENEOUS
from imaspy.ids_metadata import IDSMetadata
from imaspy.ids_primitive import IDSPrimitive
from imaspy.ids_struct_array import IDSStructArray
from imaspy.ids_structure import IDSStructure
from imaspy.ids_toplevel import IDSToplevel
from imaspy.util import visit_children

logger = logging.getLogger(__name__)


def resample_impl(node, old_time, new_time, homogeneousTime, inplace, **kwargs):
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


def print_tree_impl(structure, hide_empty_nodes):
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

    iterator = structure
    if hide_empty_nodes and isinstance(structure, IDSStructure):
        iterator = structure._iter_nonempty()
    for child in iterator:
        if isinstance(child, IDSPrimitive):
            if not child.has_value:
                value = "[bright_black]-"
            else:
                value = Pretty(child.value)
            txt = f"[yellow]{child.metadata.name}[/]:"
            group = Columns([txt, value])
            tree.add(group)
        else:
            if isinstance(child, IDSStructure):
                txt = f"[magenta]{child._path}[/]"
                ntree = tree.add(txt)
            elif isinstance(child, IDSStructArray):
                ntree = tree
                if not child.has_value:
                    tree.add(f"[magenta]{child._path}[][/]")
            _make_tree(child, hide_empty_nodes, tree=ntree)

    return tree


def print_metadata_tree_impl(
    structure: Union[IDSMetadata, IDSBase], maxdepth: int
) -> None:
    def _make_tree(tree: Tree, metadata: IDSMetadata, depth: int):
        for child in metadata._children.values():
            if child.data_type in (IDSDataType.STRUCTURE, IDSDataType.STRUCT_ARRAY):
                newtree = tree.add(f"[magenta]{child.path_doc}[/]")
                if maxdepth == 0 or depth < maxdepth:
                    _make_tree(newtree, child, depth + 1)
                else:
                    newtree.add("[bright_black]<hidden>[/]")
            else:
                tree.add(f"[yellow]{child.path_doc}")

    metadata = structure if isinstance(structure, IDSMetadata) else structure.metadata
    tree = Tree(f"[magenta]{metadata.name}")
    _make_tree(tree, metadata, 1)
    rich.print(tree)


def inspect_impl(ids_node, hide_empty_nodes):
    if not isinstance(ids_node, IDSBase):
        return rich.inspect(ids_node)
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
