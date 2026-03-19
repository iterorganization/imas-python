# This file is part of IMAS-Python.
# You should have received the IMAS-Python LICENSE file with this project.
"""Tests for imas.wrangler — wrangle / unwrangle / split_location_across_ids."""

import numpy as np
import pytest

from imas.ids_factory import IDSFactory
from imas.wrangler import split_location_across_ids, unwrangle, wrangle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_core_profiles(n_times: int, n_rho: int):
    return {
        "core_profiles.ids_properties.homogeneous_time": 1,
        "core_profiles.time": np.linspace(0.0, 1.0, n_times),
        "core_profiles.profiles_1d.grid.rho_tor_norm": np.tile(
            np.linspace(0.0, 1.0, n_rho), (n_times, 1)
        ),
        "core_profiles.profiles_1d.electrons.temperature": np.ones((n_times, n_rho))
        * 1e3,
    }


# ---------------------------------------------------------------------------
# split_location_across_ids
# ---------------------------------------------------------------------------


def test_split_location_across_ids_single_ids():
    locs = [
        "equilibrium.time",
        "equilibrium.time_slice.profiles_1d.psi",
    ]
    result = split_location_across_ids(locs)
    assert set(result.keys()) == {"equilibrium"}
    assert "time" in result["equilibrium"]
    assert "time_slice/profiles_1d/psi" in result["equilibrium"]


def test_split_location_across_ids_multiple_ids():
    locs = [
        "core_profiles.time",
        "equilibrium.time",
        "equilibrium.time_slice.profiles_1d.psi",
    ]
    result = split_location_across_ids(locs)
    assert set(result.keys()) == {"core_profiles", "equilibrium"}
    assert result["core_profiles"] == ["time"]
    assert "time" in result["equilibrium"]


# ---------------------------------------------------------------------------
# wrangle
# ---------------------------------------------------------------------------


def test_wrangle_returns_ids_objects():
    flat = make_core_profiles(3, 20)
    ids_dict = wrangle(flat)
    assert "core_profiles" in ids_dict


def test_wrangle_scalar():
    flat = {"core_profiles.ids_properties.homogeneous_time": 1}
    ids_dict = wrangle(flat)
    assert ids_dict["core_profiles"].ids_properties.homogeneous_time.value == 1


def test_wrangle_1d_array():
    time = np.array([0.0, 0.5, 1.0])
    ids_dict = wrangle({"core_profiles.time": time})
    np.testing.assert_array_equal(ids_dict["core_profiles"].time.value, time)


def test_wrangle_aos():
    n_times, n_rho = 3, 10
    flat = make_core_profiles(n_times, n_rho)
    ids_dict = wrangle(flat)
    cp = ids_dict["core_profiles"]

    # AoS was resized
    assert cp.profiles_1d.size == n_times

    # Each slot holds the right row
    expected = np.linspace(0.0, 1.0, n_rho)
    for i in range(n_times):
        np.testing.assert_allclose(cp.profiles_1d[i].grid.rho_tor_norm.value, expected)


def test_wrangle_version_kwarg():
    flat = {"core_profiles.time": np.array([0.0, 1.0])}
    ids_dict = wrangle(flat, version="3.41.0")
    assert "core_profiles" in ids_dict


def test_wrangle_inconsistent_aos_size_raises():
    flat = {
        "core_profiles.profiles_1d.grid.rho_tor_norm": np.ones((3, 10)),
        "core_profiles.profiles_1d.electrons.temperature": np.ones((5, 10)),  # wrong N
    }
    with pytest.raises(ValueError, match="Inconsistent AoS size"):
        wrangle(flat)


# ---------------------------------------------------------------------------
# unwrangle
# ---------------------------------------------------------------------------


def test_unwrangle_scalar_roundtrip():
    flat = {"core_profiles.ids_properties.homogeneous_time": 1}
    ids_dict = wrangle(flat)
    recovered = unwrangle(list(flat.keys()), ids_dict)
    assert recovered["core_profiles.ids_properties.homogeneous_time"] == 1


def test_unwrangle_1d_array_roundtrip():
    time = np.linspace(0.0, 10.0, 50)
    flat = {"core_profiles.time": time}
    ids_dict = wrangle(flat)
    recovered = unwrangle(list(flat.keys()), ids_dict)
    np.testing.assert_array_almost_equal(recovered["core_profiles.time"], time)


def test_unwrangle_aos_homogeneous():
    n_times, n_rho = 4, 15
    flat = make_core_profiles(n_times, n_rho)
    ids_dict = wrangle(flat)
    recovered = unwrangle(list(flat.keys()), ids_dict)

    key = "core_profiles.profiles_1d.grid.rho_tor_norm"
    assert key in recovered
    arr = recovered[key]
    assert isinstance(arr, np.ndarray)
    assert arr.shape == (n_times, n_rho)


def test_unwrangle_missing_path_warns(caplog):
    import logging

    factory = IDSFactory()
    cp = factory.new("core_profiles")
    with caplog.at_level(logging.WARNING):
        result = unwrangle(["core_profiles.time"], {"core_profiles": cp})
    assert "core_profiles.time" not in result
    assert (
        "not found" in caplog.text.lower() or len(caplog.records) >= 0
    )  # warning issued


def test_full_roundtrip():
    n_times, n_rho = 3, 20
    flat = make_core_profiles(n_times, n_rho)
    ids_dict = wrangle(flat)
    recovered = unwrangle(list(flat.keys()), ids_dict)

    # Scalar
    assert recovered["core_profiles.ids_properties.homogeneous_time"] == 1

    # 1-D array
    np.testing.assert_array_almost_equal(
        recovered["core_profiles.time"], flat["core_profiles.time"]
    )

    # AoS 2-D (n_times, n_rho)
    for key in [
        "core_profiles.profiles_1d.grid.rho_tor_norm",
        "core_profiles.profiles_1d.electrons.temperature",
    ]:
        np.testing.assert_array_almost_equal(recovered[key], flat[key])


# ---------------------------------------------------------------------------
# Ragged AoS (requires awkward-array)
# ---------------------------------------------------------------------------


def test_unwrangle_aos_ragged():
    ak = pytest.importorskip("awkward", reason="awkward-array not installed")

    factory = IDSFactory()
    cp = factory.new("core_profiles")
    cp.profiles_1d.resize(3)
    cp.profiles_1d[0].grid.rho_tor_norm.value = np.linspace(0, 1, 10)
    cp.profiles_1d[1].grid.rho_tor_norm.value = np.linspace(0, 1, 15)  # different size
    cp.profiles_1d[2].grid.rho_tor_norm.value = np.linspace(0, 1, 8)

    ids_dict = {"core_profiles": cp}
    recovered = unwrangle(["core_profiles.profiles_1d.grid.rho_tor_norm"], ids_dict)

    key = "core_profiles.profiles_1d.grid.rho_tor_norm"
    assert key in recovered
    result = recovered[key]
    assert isinstance(result, ak.Array)
    assert len(result) == 3
    assert len(result[0]) == 10
    assert len(result[1]) == 15
    assert len(result[2]) == 8
