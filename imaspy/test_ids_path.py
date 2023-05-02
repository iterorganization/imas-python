from imaspy.ids_path import IDSPath

import pytest


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
        path.immutable = True


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
    ],
)
def test_invalid_paths(path):
    with pytest.raises(ValueError):
        IDSPath(path)
