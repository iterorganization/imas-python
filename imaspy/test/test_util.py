import imaspy
from imaspy.test.test_helpers import fill_consistent
from imaspy.training import get_training_db_entry
from imaspy.util import find_paths, inspect, print_metadata_tree, print_tree, tree_iter


def test_tree_iter():
    cp = imaspy.IDSFactory("3.39.0").new("core_profiles")

    # Test tree iterator over empty IDS
    assert list(tree_iter(cp)) == []
    assert list(tree_iter(cp, leaf_only=False)) == []
    assert list(tree_iter(cp, leaf_only=False, include_node=True)) == [cp]

    # Fill some data and test again
    cp.ids_properties.homogeneous_time = 1
    ht = cp.ids_properties.homogeneous_time
    assert list(tree_iter(cp)) == [ht]
    assert list(tree_iter(cp, leaf_only=False)) == [cp.ids_properties, ht]
    expected = [cp, cp.ids_properties, ht]
    assert list(tree_iter(cp, leaf_only=False, include_node=True)) == expected

    # Test if empty values are iterated over as expected
    visit_empty = list(tree_iter(cp.ids_properties, visit_empty=True))
    ip = cp.ids_properties
    assert visit_empty[:4] == [ip.comment, ht, ip.source, ip.provider]


def test_inspect():
    cp = imaspy.IDSFactory("3.39.0").new("core_profiles")
    inspect(cp)  # IDSToplevel
    inspect(cp.ids_properties)  # IDSStructure
    cp.profiles_1d.resize(5)
    inspect(cp.profiles_1d)  # IDSStructArray
    inspect(cp.profiles_1d[1])  # IDSStructure inside array
    inspect(cp.profiles_1d[1].grid)  # IDSStructure inside array
    inspect(cp.profiles_1d[1].grid.rho_tor_norm)  # IDSPrimitive


def test_inspect_lazy():
    cp = get_training_db_entry().get("core_profiles", lazy=True)
    inspect(cp)


def test_print_tree():
    cp = imaspy.IDSFactory("3.39.0").new("core_profiles")
    fill_consistent(cp)
    print_tree(cp)  # Full IDS tree
    print_tree(cp.ids_properties)  # Sub-tree


def test_print_metadata_tree():
    cp = imaspy.IDSFactory("3.39.0").new("core_profiles")
    print_metadata_tree(cp, 1)
    print_metadata_tree(cp.metadata, 1)
    print_metadata_tree(cp.metadata["ids_properties"], 0)
    print_metadata_tree(cp.metadata["profiles_1d/electrons"])


def test_find_paths():
    cp = imaspy.IDSFactory("3.39.0").new("core_profiles")
    matches = find_paths(cp, "(^|/)time$")
    assert matches == ["profiles_1d/time", "profiles_2d/time", "time"]
