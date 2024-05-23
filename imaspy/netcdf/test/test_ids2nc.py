import netCDF4
import numpy

from imaspy.ids_defs import IDS_TIME_MODE_HOMOGENEOUS
from imaspy.ids_factory import IDSFactory
from imaspy.netcdf.ids2nc import IDS2NC


def test_tensorization():
    group = netCDF4.Dataset("tmp.nc", "w", diskless=True)
    ids = IDSFactory("3.39.0").core_profiles()

    ids.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.time = [1.0, 2.0, 3.0]
    ids.profiles_1d.resize(3)
    for p1d in ids.profiles_1d:
        p1d.ion.resize(2)
        p1d.ion[0].label = "D"
        p1d.ion[0].z_ion = 1.0
        p1d.ion[0].element.resize(1)
        p1d.ion[0].element[0].a = 2.0
        p1d.ion[0].element[0].z_n = 1.0
        p1d.ion[0].element[0].atoms_n = 1

        p1d.ion[1].label = "OH-"
        p1d.ion[1].z_ion = -1.0
        p1d.ion[1].element.resize(2)
        p1d.ion[1].element[0].a = 1.0
        p1d.ion[1].element[0].z_n = 1.0
        p1d.ion[1].element[0].atoms_n = 1
        p1d.ion[1].element[1].a = 16.0
        p1d.ion[1].element[1].z_n = 8.0
        p1d.ion[1].element[1].atoms_n = 1

    IDS2NC(ids, group).run()
    # Test tensorized values
    expected = [["D", "OH-"]] * 3
    assert numpy.array_equal(group["profiles_1d.ion.label"], expected)

    expected = [[1.0, -1.0]] * 3
    assert numpy.array_equal(group["profiles_1d.ion.z_ion"], expected)

    expected = [[[2.0, netCDF4.default_fillvals["f8"]], [1.0, 16.0]]] * 3
    assert numpy.array_equal(group["profiles_1d.ion.element.a"], expected)

    expected = [[[1.0, netCDF4.default_fillvals["f8"]], [1.0, 8.0]]] * 3
    assert numpy.array_equal(group["profiles_1d.ion.element.z_n"], expected)

    expected = [[[1, netCDF4.default_fillvals["i4"]], [1, 1]]] * 3
    assert numpy.array_equal(group["profiles_1d.ion.element.atoms_n"], expected)

    # Test :shape arrays
    assert "profiles_1d:shape" not in group.variables
    assert "profiles_1d.ion:shape" not in group.variables
    assert "profiles_1d.ion.element:shape" in group.variables
    expected = [[[1], [2]]] * 3
    assert numpy.array_equal(group["profiles_1d.ion.element:shape"], expected)
