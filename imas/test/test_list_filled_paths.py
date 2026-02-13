import pytest

import imas
from imas.backends.imas_core.imas_interface import ll_interface
from imas.exception import DataEntryException
from imas.ids_defs import IDS_TIME_MODE_HOMOGENEOUS, IDS_TIME_MODE_INDEPENDENT


if not hasattr(ll_interface, "list_all_occurrences"):
    marker = pytest.mark.xfail(reason="list_all_occurrences not available in imas_core")
else:
    marker = []


@pytest.fixture(params=["netcdf", pytest.param("hdf5", marks=marker)])
def testuri(request, tmp_path):
    if request.param == "netcdf":
        return str(tmp_path / "list_filled_paths.nc")
    return f"imas:{request.param}?path={tmp_path}/list_filled_paths_{request.param}"


def test_list_filled_paths(testuri):
    with imas.DBEntry(testuri, "w", dd_version="4.0.0") as dbentry:
        # No IDSs in the DBEntry yet, expect an exception
        with pytest.raises(DataEntryException):
            dbentry.list_filled_paths("core_profiles")

        cp = dbentry.factory.core_profiles()
        cp.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
        cp.ids_properties.comment = "comment"
        cp.time = [0.1, 0.2]
        cp.profiles_1d.resize(2)
        cp.profiles_1d[0].grid.rho_tor_norm = [1.0, 2.0]
        cp.profiles_1d[0].ion.resize(2)
        cp.profiles_1d[0].ion[1].temperature = [1.0, 2.0]
        cp.profiles_1d[1].grid.psi = [1.0, 2.0]
        cp.profiles_1d[1].q = [1.0, 2.0]
        cp.profiles_1d[1].e_field.radial = [1.0, 2.0]
        cp.profiles_1d[1].neutral.resize(2)
        cp.global_quantities.ip = [1.0, 2.0]

        dbentry.put(cp)

        filled_paths = dbentry.list_filled_paths("core_profiles")
        assert isinstance(filled_paths, list)
        assert set(filled_paths) == {
            "ids_properties/version_put/access_layer",
            "ids_properties/version_put/access_layer_language",
            "ids_properties/version_put/data_dictionary",
            "ids_properties/homogeneous_time",
            "ids_properties/comment",
            "time",
            "profiles_1d/grid/rho_tor_norm",
            "profiles_1d/ion/temperature",
            "profiles_1d/grid/psi",
            "profiles_1d/q",
            "profiles_1d/e_field/radial",
            "profiles_1d/e_field/radial",
            "global_quantities/ip",
        }
        # Other occurrence should still raise an error:
        with pytest.raises(DataEntryException):
            dbentry.list_filled_paths("core_profiles", 1)


def test_list_filled_paths_autoconvert(testuri):
    with imas.DBEntry(testuri, "w", dd_version="3.25.0") as entry:
        ps = entry.factory.pulse_schedule()
        ps.ids_properties.homogeneous_time = IDS_TIME_MODE_INDEPENDENT
        ps.ec.antenna.resize(1)
        ps.ec.antenna[0].launching_angle_pol.reference_name = "test"
        entry.put(ps)

        filled_paths = entry.list_filled_paths("pulse_schedule")
        assert set(filled_paths) == {
            "ids_properties/version_put/access_layer",
            "ids_properties/version_put/access_layer_language",
            "ids_properties/version_put/data_dictionary",
            "ids_properties/homogeneous_time",
            "ec/antenna/launching_angle_pol/reference_name",
        }

    # Check autoconvert with DD 3.28.0
    with imas.DBEntry(testuri, "r", dd_version="3.28.0") as entry:
        assert set(entry.list_filled_paths("pulse_schedule", autoconvert=False)) == {
            "ids_properties/version_put/access_layer",
            "ids_properties/version_put/access_layer_language",
            "ids_properties/version_put/data_dictionary",
            "ids_properties/homogeneous_time",
            "ec/antenna/launching_angle_pol/reference_name",  # original name
        }
        assert set(entry.list_filled_paths("pulse_schedule")) == {
            "ids_properties/version_put/access_layer",
            "ids_properties/version_put/access_layer_language",
            "ids_properties/version_put/data_dictionary",
            "ids_properties/homogeneous_time",
            "ec/launcher/steering_angle_pol/reference_name",  # autoconverted name
        }
