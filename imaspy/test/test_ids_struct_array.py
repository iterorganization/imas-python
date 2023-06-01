import pytest
from copy import deepcopy

from imaspy.ids_toplevel import IDSToplevel
from imaspy.ids_struct_array import IDSStructArray


@pytest.fixture
def struct_array(fake_structure_xml):
    wavevector_xml = fake_structure_xml.find(".//*[@name='wavevector']")
    fake_structure_xml.remove(wavevector_xml)
    top = IDSToplevel(
        object(),
        fake_structure_xml,
    )
    struct_array = IDSStructArray(top, wavevector_xml)
    struct_array.resize(3)
    assert len(struct_array.value) == 3
    return struct_array


@pytest.mark.parametrize("keep", (True, False))
@pytest.mark.parametrize("target_len", (1, 3, 7))
def test_resize(keep, target_len, struct_array):
    pre_struct_array_len = len(struct_array)
    pre_struct_array = deepcopy(struct_array)
    n_comp_values = min(target_len, pre_struct_array_len)
    pre_values = [struct_array[ii] for ii in range(n_comp_values)]

    # Test if resize works for 3->1, 3->3, and 3->7
    struct_array.resize(target_len, keep=keep)

    # Test if internal data is the right length
    assert len(struct_array) == target_len

    # Test if internal data is explicitly new (keep = False) or
    # explicitly kept (keep = True)
    for ii in range(n_comp_values):
        if keep:
            assert (
                struct_array[ii] is pre_values[ii]
            ), f"On element {ii} of {struct_array.value} vs {pre_struct_array.value}"
        else:
            assert (
                struct_array[ii] is not pre_values[ii]
            ), f"On element {ii} of {struct_array.value} vs {pre_struct_array.value}"
