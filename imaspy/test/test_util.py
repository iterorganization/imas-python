import imaspy.util

from imaspy.test.test_helpers import fill_consistent


def test_inspect():
    cp = imaspy.IDSFactory("3.39.0").new("core_profiles")
    imaspy.util.inspect(cp)  # IDSToplevel
    imaspy.util.inspect(cp.ids_properties)  # IDSStructure
    cp.profiles_1d.resize(5)
    imaspy.util.inspect(cp.profiles_1d)  # IDSStructArray
    imaspy.util.inspect(cp.profiles_1d[1])  # IDSStructure inside array
    imaspy.util.inspect(cp.profiles_1d[1].grid)  # IDSStructure inside array
    imaspy.util.inspect(cp.profiles_1d[1].grid.rho_tor_norm)  # IDSPrimitive


def test_print_tree():
    cp = imaspy.IDSFactory("3.39.0").new("core_profiles")
    fill_consistent(cp)
    imaspy.util.print_tree(cp)  # Full IDS tree
    imaspy.util.print_tree(cp.ids_properties)  # Sub-tree


def test_print_metadata_tree():
    cp = imaspy.IDSFactory("3.39.0").new("core_profiles")
    imaspy.util.print_metadata_tree(cp, 1)
    imaspy.util.print_metadata_tree(cp.metadata, 1)
    imaspy.util.print_metadata_tree(cp.metadata["ids_properties"], 0)
    imaspy.util.print_metadata_tree(cp.metadata["profiles_1d/electrons"])


def test_find_paths():
    cp = imaspy.IDSFactory("3.39.0").new("core_profiles")
    matches = imaspy.util.find_paths(cp, "(^|/)time$")
    assert matches == ["profiles_1d/time", "profiles_2d/time", "time"]
