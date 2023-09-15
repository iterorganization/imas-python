import copy

import imaspy
from imaspy.ids_structure import IDSStructure
from imaspy.ids_struct_array import IDSStructArray
from imaspy.test.test_helpers import fill_with_random_data, compare_children


def validate_parent(node):
    for child in node:
        assert child._parent is node
        if isinstance(child, (IDSStructure, IDSStructArray)):
            validate_parent(child)


def test_deepcopy():
    factory = imaspy.IDSFactory("3.38.1")
    cp = factory.core_profiles()
    fill_with_random_data(cp)

    cp2 = copy.deepcopy(cp)
    compare_children(cp, cp2)

    validate_parent(cp)
    validate_parent(cp2)
