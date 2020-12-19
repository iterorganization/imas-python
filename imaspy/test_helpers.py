import copy
import logging
import random
import string

import numpy as np

# TODO: import these from imaspy (i.e. expose them publicly?)
from imaspy.ids_defs import IDS_TIME_MODE_HOMOGENEOUS
from imaspy.ids_root import IDSRoot
from imaspy.ids_struct_array import IDSStructArray
from imaspy.ids_structure import IDSStructure
from imaspy.ids_toplevel import IDSToplevel

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.DEBUG)


def randdims(n):
    """Return a list of n random numbers between 1 and 10 representing
    the shapes in n dimensions"""
    return random.sample(range(1, 10), n)


def random_string():
    return "".join(
        random.choice(string.ascii_uppercase + string.digits)
        for i in range(random.randint(0, 1024))
    )


def random_data(ids_type, ndims):
    if ndims < 0:
        raise NotImplementedError("Negative dimensions are not supported")

    if ids_type == "STR":
        if ndims == 0:
            return random_string()
        elif ndims == 1:
            return [random_string() for i in range(random.randint(0, 3))]
        else:
            raise NotImplementedError(
                "Strings of dimension 2 or higher " "are not supported"
            )
        return np.random.randint(0, 1000, size=randdims(ndims))
    elif ids_type == "INT":
        return np.random.randint(0, 1000, size=randdims(ndims))
    elif ids_type == "FLT":
        return np.random.random_sample(size=randdims(ndims))
    else:
        logger.warn("Unknown data type %s requested to fill, ignoring", ids_type)


def fill_with_random_data(structure):
    """Fill a structure with random data.
    Sets homogeneous_time to independent _always_.
    TODO: also test other time types"""
    for child_name in structure._children:
        child = structure[child_name]

        if type(child) in [IDSStructure, IDSToplevel, IDSRoot]:
            fill_with_random_data(child)
        elif type(child) == IDSStructArray:
            if len(child.value) == 0:
                child.append(copy.deepcopy(child._element_structure))
                child.append(copy.deepcopy(child._element_structure))
                child.append(copy.deepcopy(child._element_structure))
                for a in child.value:
                    fill_with_random_data(a)
        else:  # leaf node
            if child_name == "homogeneous_time":
                child.value = IDS_TIME_MODE_HOMOGENEOUS
            else:
                child.value = random_data(child._ids_type, child._ndims)


def visit_children(structure, fun):
    """walk all children of this structure in order and execute fun on them"""
    for child_name in structure._children:
        child = structure[child_name]

        if type(child) in [IDSStructure, IDSToplevel, IDSRoot]:
            visit_children(child, fun)
        elif type(child) == IDSStructArray:
            for a in child.value:
                visit_children(a, fun)
        else:  # leaf node
            fun(child)


def compare_children(st1, st2):
    """Perform a deep compare of two structures using asserts."""
    for (name1, child1), (name2, child2) in zip(st1.items(), st2.items()):
        assert name1 == name2
        assert type(child1) == type(child2)

        if type(child1) in [IDSStructure, IDSToplevel, IDSRoot]:
            compare_children(child1, child2)
        elif type(child1) == IDSStructArray:
            for a, b in zip(child1.value, child2.value):
                compare_children(a, b)
        else:  # leaf node
            if isinstance(child1.value, np.ndarray):
                assert np.array_equal(child1.value, child2.value)
            else:
                assert child1.value == child2.value
