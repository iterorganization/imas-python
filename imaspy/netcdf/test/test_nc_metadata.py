import pytest

from imaspy.exception import UnknownDDVersion
from imaspy.ids_factory import IDSFactory
from imaspy.netcdf.nc_metadata import NCMetadata, _get_aos_label_coordinates


def test_generate_nc_metadata(ids_name):
    ids = IDSFactory().new(ids_name)
    NCMetadata(ids.metadata)


def test_get_aos_label_coordinates():
    cp = IDSFactory("3.39.0").core_profiles()
    pfa = IDSFactory("3.39.0").pf_active()

    assert _get_aos_label_coordinates(cp.metadata["profiles_1d"]) == []
    expected = ["profiles_1d.ion.label"]
    assert _get_aos_label_coordinates(cp.metadata["profiles_1d/ion"]) == expected
    expected = ["coil.name", "coil.identifier"]
    assert _get_aos_label_coordinates(pfa.metadata["coil"]) == expected
    expected = ["coil.element.name", "coil.element.identifier"]
    assert _get_aos_label_coordinates(pfa.metadata["coil.element"]) == expected


def test_time_mode():
    cp = NCMetadata(IDSFactory("3.39.0").core_profiles().metadata)
    mag = NCMetadata(IDSFactory("3.39.0").magnetics().metadata)

    # These quantities always have root time as dimension
    assert cp.get_dimensions("time", True) == ("time",)
    assert cp.get_dimensions("time", False) == ("time",)
    assert cp.get_dimensions("global_quantities/ip", True) == ("time",)
    assert cp.get_dimensions("global_quantities/ip", False) == ("time",)

    assert cp.get_coordinates("time", True) == ""
    assert cp.get_coordinates("time", False) == ""
    assert cp.get_coordinates("global_quantities/ip", True) == "time"
    assert cp.get_coordinates("global_quantities/ip", False) == "time"

    # Dynamic array of structures
    assert cp.get_dimensions("profiles_1d", True) == ("time",)
    assert cp.get_dimensions("profiles_1d", False) == ("profiles_1d.time",)
    assert cp.get_dimensions("profiles_1d/grid/rho_tor", True)[0] == "time"
    assert cp.get_dimensions("profiles_1d/grid/rho_tor", False)[0] == "profiles_1d.time"

    assert cp.get_coordinates("profiles_1d", True) == "time"
    assert cp.get_coordinates("profiles_1d", False) == "profiles_1d.time"
    coors = cp.get_coordinates("profiles_1d/grid/rho_tor", True)
    assert coors == "time profiles_1d.grid.rho_tor_norm"
    coors = cp.get_coordinates("profiles_1d/grid/rho_tor", False)
    assert coors == "profiles_1d.time profiles_1d.grid.rho_tor_norm"

    # Sibling time nodes
    assert mag.get_dimensions("flux_loop/flux/data", True) == ("flux_loop:i", "time")
    dims = mag.get_dimensions("flux_loop/flux/data", False)
    assert dims == ("flux_loop:i", "flux_loop.flux.time:i")

    coors = mag.get_coordinates("flux_loop/flux/data", True)
    assert coors == "flux_loop.name flux_loop.identifier time"
    coors = mag.get_coordinates("flux_loop/flux/data", False)
    assert coors == "flux_loop.name flux_loop.identifier flux_loop.flux.time"


def test_dd3_alternative_coordinates():
    distr = NCMetadata(IDSFactory("3.39.0").distributions().metadata)

    # Dimension names use the first listed of the alternatives
    assert distr.get_dimensions("distribution/profiles_2d/density", True) == (
        "distribution:i",
        "time",
        "distribution.profiles_2d.grid.r:i",
        "distribution.profiles_2d.grid.z:i",
    )

    # Auxiliary coordinates list all, including the alternatives
    assert distr.get_coordinates("distribution/profiles_2d/density", True) == (
        "time "
        "distribution.profiles_2d.grid.r "
        "distribution.profiles_2d.grid.rho_tor_norm "
        "distribution.profiles_2d.grid.z "
        "distribution.profiles_2d.grid.theta_geometric "
        "distribution.profiles_2d.grid.theta_straight"
    )


@pytest.mark.xfail(reason="DDv4 not yet released", raises=UnknownDDVersion)
def test_dd4_alternative_coordinates():
    cp = NCMetadata(IDSFactory("4.0.0").core_profiles().metadata)

    # Dimension names use the first listed of the alternatives
    dims = cp.get_dimensions("profiles_1d/j_tor", True)
    assert dims == ("time", "profiles_1d.grid.rho_tor_norm:i")

    # Auxiliary coordinates list all, including the alternatives
    assert cp.get_coordinates("profiles_1d/j_tor", True) == (
        "time "
        "profiles_1d.grid.rho_tor_norm "
        "profiles_1d.grid.rho_tor "
        "profiles_1d.grid.psi "
        "profiles_1d.grid.volume "
        "profiles_1d.grid.area "
        "profiles_1d.grid.surface "
        "profiles_1d.grid.rho_pol_norm"
    )
