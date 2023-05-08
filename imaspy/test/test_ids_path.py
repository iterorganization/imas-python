from imaspy.ids_path import IDSPath
from imaspy.ids_root import IDSRoot

import pytest


def test_path_cache():
    path = IDSPath("uniq")
    path2 = IDSPath("uniq")
    assert path is path2


def test_empty_path():
    path = IDSPath("")
    assert path.parts == ()
    assert path.indices == ()


def test_path_without_slashes_and_indices():
    path = IDSPath("ids_properties")
    assert path.parts == ("ids_properties",)
    assert path.indices == (None,)


def test_path_without_slashes():
    path = IDSPath("profiles_1d(itime)")
    assert path.parts == ("profiles_1d",)
    assert path.indices == ("itime",)


def test_path_without_indices():
    path = IDSPath("ids_properties/version_put/data_dictionary")
    assert path.parts == ("ids_properties", "version_put", "data_dictionary")
    assert path.indices == (None, None, None)


def test_path_with_dummy_indices():
    path = IDSPath(
        "time_slice(itime)/ggd(i1)/grid/space(i2)/objects_per_dimension(i3)/"
        "object(i4)/boundary(i5)"
    )
    assert path.parts == (
        "time_slice",
        "ggd",
        "grid",
        "space",
        "objects_per_dimension",
        "object",
        "boundary",
    )
    assert path.indices == ("itime", "i1", None, "i2", "i3", "i4", "i5")


def test_path_with_path_index():
    path = IDSPath("coordinate_system(process(i1)/coordinate_index)/coordinate(1)")
    assert path.parts == ("coordinate_system", "coordinate")
    assert isinstance(path.indices[0], IDSPath)
    assert path.indices[0].parts == ("process", "coordinate_index")
    assert path.indices[0].indices == ("i1", None)
    assert path.indices[1] == 1
    assert len(path.indices) == 2


def test_path_with_slices():
    path = IDSPath("distribution(1:3)/process(:)/nbi_unit")
    assert path.parts == ("distribution", "process", "nbi_unit")
    assert path.indices == (slice(1, 3), slice(None), None)


def test_path_immutable():
    path = IDSPath("")
    with pytest.raises(RuntimeError):
        path.some_attr = True
    with pytest.raises(RuntimeError):
        path.parts = (1, 2)


def test_path_time():
    assert not IDSPath("no_time").is_time_path
    assert IDSPath("time").is_time_path
    assert IDSPath("profiles_1d(itime)/time").is_time_path


@pytest.mark.parametrize(
    "path",
    [
        "empty//part",
        "(empty_part)",
        "_invalid_node_name",
        "another__invalid_node_name",
        "CAPS_IS_ALSO_NOT_ALLOWED",
        "nor are spaces",
        "or.periods",
        "or_commas,",
        "unmatched(parentheses()",
        "unmatched)(parentheses",
    ],
)
def test_invalid_paths(path):
    with pytest.raises(ValueError):
        IDSPath(path)


def test_path_goto(fake_toplevel_xml):
    ids = IDSRoot(xml_path=fake_toplevel_xml).gyrokinetics

    version_put_path = IDSPath("ids_properties/version_put")
    assert version_put_path.goto(ids) is ids.ids_properties.version_put

    ids.wavevector.resize(2)
    ids.wavevector[0].eigenmode.resize(2)

    ids.wavevector[0].eigenmode[0].growth_rate_norm = 1.23
    growth_rate_norm_path = IDSPath("wavevector(i1)/eigenmode(i2)/growth_rate_norm")
    # We cannot address this path from the root (because of the dummy 'i1' and 'i2'):
    with pytest.raises(ValueError):
        growth_rate_norm_path.goto(ids)
    # But we can when there is a common parent
    assert (
        growth_rate_norm_path.goto(ids.wavevector[0].eigenmode[0].frequency_norm)
        is ids.wavevector[0].eigenmode[0].growth_rate_norm
    )
    # One common parent (of the two) is not enough
    with pytest.raises(ValueError):
        growth_rate_norm_path.goto(ids.wavevector[0])

    # With explicit (1-based) indices we can resolve from ids
    growth_rate_norm_path2 = IDSPath("wavevector(1)/eigenmode(1)/growth_rate_norm")
    assert (
        growth_rate_norm_path2.goto(ids)
        is ids.wavevector[0].eigenmode[0].growth_rate_norm
    )

    radial_component_norm_path = IDSPath("wavevector(i1)/radial_component_norm")
    assert (
        radial_component_norm_path.goto(ids.wavevector[0].eigenmode[0].frequency_norm)
        is ids.wavevector[0].radial_component_norm
    )

    # Use homogeneous_time (the only INT_0D in this fake IDS) as an indirect index
    ids.ids_properties.homogeneous_time = 1
    indirect_path = IDSPath("wavevector(ids_properties/homogeneous_time)")
    assert indirect_path.goto(ids) is ids.wavevector[0]
    ids.ids_properties.homogeneous_time = 2
    assert indirect_path.goto(ids) is ids.wavevector[1]

    # But it's not allowed to use a non INT_0D as indirect index
    with pytest.raises(ValueError):
        IDSPath("wavevector(ids_properties/comment)").goto(ids)