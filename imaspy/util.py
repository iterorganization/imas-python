# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

import copy
import logging

import scipy.interpolate

from imaspy.ids_defs import IDS_TIME_MODE_HOMOGENEOUS
from imaspy.ids_primitive import IDSPrimitive
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
