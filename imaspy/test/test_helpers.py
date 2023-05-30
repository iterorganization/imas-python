import logging
import random
import string

import numpy as np

import imaspy

# TODO: import these from imaspy (i.e. expose them publicly?)
from imaspy.db_entry import DBEntry
from imaspy.ids_defs import ASCII_BACKEND, IDS_TIME_MODE_HOMOGENEOUS
from imaspy.ids_struct_array import IDSStructArray
from imaspy.ids_structure import IDSStructure
from imaspy.ids_toplevel import IDSToplevel

root_logger = logging.getLogger("imaspy")
logger = root_logger
logger.setLevel(logging.INFO)

BASE_STRING = string.ascii_uppercase + string.digits


def randdims(ndims):
    """Return a list of n random numbers representing
    the shapes in n dimensions"""
    return random.sample(range(1, 7), ndims)


def random_string():
    return "".join(random.choice(BASE_STRING) for i in range(random.randint(0, 128)))


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
        return np.random.randint(0, 2**31 - 1, size=randdims(ndims))
    elif ids_type == "INT":
        return np.random.randint(0, 2**31 - 1, size=randdims(ndims))
    elif ids_type == "FLT":
        return np.random.random_sample(size=randdims(ndims))
    elif ids_type == "CPX":
        size = randdims(ndims)
        return np.random.random_sample(size) + 1j * np.random.random_sample(size)
    else:
        logger.warn("Unknown data type %s requested to fill, ignoring", ids_type)


def fill_with_random_data(structure, max_children=3):
    """Fill a structure with random data.

    Sets homogeneous_time to homogeneous _always_.
    TODO: also test other time types

    Args:
        structure: IDS object to fill
        max_children: The maximum amount of children to create for IDSStructArrays.
    """
    for child_name in structure._children:
        child = structure[child_name]

        if type(child) in [IDSStructure, IDSToplevel]:
            fill_with_random_data(child, max_children)
        elif isinstance(child, IDSStructArray):
            if len(child.value) == 0:
                n_children = min(child.metadata.maxoccur or max_children, max_children)
                for _ in range(n_children):
                    child.append(child._element_structure)
                # choose which child will get the max number of grand-children
                max_child = random.randrange(n_children)
                for i, ch in enumerate(child.value):
                    max_grand_children = max_children if i == max_child else 1
                    fill_with_random_data(ch, max_grand_children)
        else:  # leaf node
            if child_name == "homogeneous_time":
                child.value = IDS_TIME_MODE_HOMOGENEOUS
            elif child_name == "time" and not isinstance(structure, IDSToplevel):
                pass  # skip non-root time arrays when in HOMOGENEOUS_TIME
            else:
                child.value = random_data(
                    child.metadata.data_type.value, child.metadata.ndim
                )


def compare_children(st1, st2, _ascii_empty_array_skip=False, deleted_paths=set()):
    """Perform a deep compare of two structures using asserts."""
    for child1, child2 in zip(st1, st2):
        assert child1.metadata.name == child2.metadata.name
        assert type(child1) == type(child2)

        if type(child1) in [IDSStructure, IDSToplevel]:
            compare_children(
                child1, child2, _ascii_empty_array_skip=_ascii_empty_array_skip, deleted_paths=deleted_paths
            )
        elif isinstance(child1, IDSStructArray):
            for ch1, ch2 in zip(child1.value, child2.value):
                compare_children(
                    ch1, ch2, _ascii_empty_array_skip=_ascii_empty_array_skip, deleted_paths=deleted_paths
                )
        else:  # leaf node
            path = str(child1.metadata.path)
            if "_error_" in path:
                # No duplicated entries for _error_upper, _error_lower and _error_index
                path = path[:path.find("_error_")]
            if path in deleted_paths:
                assert not child2.has_value
            elif isinstance(child1.value, (list, np.ndarray)):
                one = np.asarray(child1.value)
                two = np.asarray(child2.value)
                if (one.size == 0 or two.size == 0) and _ascii_empty_array_skip:
                    # check that they are both empty, or one is [] and one is ['']
                    assert (
                        (one.size == 0 and two.size == 1 and two[0] == "")
                        or (two.size == 0 and one.size == 1 and one[0] == "")
                        or (one.size == 0 and two.size == 0)
                    )
                else:
                    assert one.size == two.size
                    if one.size > 0 and two.size > 0:
                        assert np.array_equal(one, two)
            else:
                assert child1.value == child2.value


def open_dbentry(
    backend, mode, worker_id, tmp_path, version=None, xml_path=None
) -> DBEntry:
    """Open a DBEntry, with a tmpdir in place of the user argument"""
    if worker_id == "master":
        shot = 1
    else:
        shot = int(worker_id[2:]) + 1

    dbentry = DBEntry(
        backend, "test", shot, 0, str(tmp_path), version=version, xml_path=xml_path
    )
    options = f"-prefix {tmp_path}/" if backend == ASCII_BACKEND else None
    if mode == "w":
        dbentry.create(options=options)
    else:
        dbentry.open(options=options)

    return dbentry
