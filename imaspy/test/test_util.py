import imaspy
from imaspy.test.test_helpers import fill_consistent
from imaspy.training import get_training_db_entry
from imaspy.util import (
    find_paths,
    idsdiffgen,
    inspect,
    print_metadata_tree,
    print_tree,
    tree_iter,
)


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


def test_idsdiffgen():
    factory1 = imaspy.IDSFactory("3.39.0")
    factory2 = imaspy.IDSFactory("3.32.0")
    cp1 = factory1.new("core_profiles")
    cp2 = factory2.new("core_profiles")
    eq1 = factory1.new("equilibrium")

    # Test different DD versions
    diff = list(idsdiffgen(cp1, cp2))
    assert len(diff) == 1
    assert diff[0][1:] == ("3.39.0", "3.32.0")

    # Test different IDSs
    diff = list(idsdiffgen(cp1, eq1))
    assert len(diff) == 1
    assert diff[0][1:] == ("core_profiles", "equilibrium")

    cp2 = factory1.new("core_profiles")
    # Test different structures
    cp2.ids_properties.homogeneous_time = 1
    diff = list(idsdiffgen(cp1, cp2))
    assert len(diff) == 1
    assert diff[0] == ("ids_properties/homogeneous_time", None, 1)

    # Test different values
    cp1.ids_properties.homogeneous_time = 2
    diff = list(idsdiffgen(cp1, cp2))
    assert len(diff) == 1
    assert diff[0] == ("ids_properties/homogeneous_time", 2, 1)

    cp1.ids_properties.homogeneous_time = 1
    # Test missing values
    cp1.time = [1.0, 2.0]
    diff = list(idsdiffgen(cp1, cp2))
    assert len(diff) == 1
    assert diff[0] == ("time", cp1.time, None)

    # Test different array values
    cp2.time = [2.0, 1.0]
    diff = list(idsdiffgen(cp1, cp2))
    assert len(diff) == 1
    assert diff[0] == ("time", cp1.time, cp2.time)

    cp2.time = cp1.time
    # Test different AoS lengths
    cp1.profiles_1d.resize(1)
    cp2.profiles_1d.resize(2)
    diff = list(idsdiffgen(cp1, cp2))
    assert len(diff) == 1
    assert diff[0] == ("profiles_1d", cp1.profiles_1d, cp2.profiles_1d)

    # Test different values inside AoS
    cp2.profiles_1d.resize(1)
    cp1.profiles_1d[0].time = -1
    cp2.profiles_1d[0].time = 0
    diff = list(idsdiffgen(cp1, cp2))
    assert len(diff) == 1
    assert diff[0] == ("profiles_1d/time", -1, 0)


def test_idsdiff():
    # Test the diff rendering for two sample IDSs
    entry = imaspy.training.get_training_db_entry()
    imaspy.util.idsdiff(entry.get("core_profiles"), entry.get("equilibrium"))
