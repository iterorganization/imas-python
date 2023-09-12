"""A testcase checking if resampling works for the latest data dictionary version.
"""

import imaspy
from imaspy.ids_factory import IDSFactory
from imaspy.ids_defs import IDS_TIME_MODE_HOMOGENEOUS


def test_single_resample_inplace():
    nbi = IDSFactory().new("nbi")
    nbi.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    nbi.time = [1, 2, 3]
    nbi.unit.resize(1)
    nbi.unit[0].energy.data = 2 * nbi.time
    old_id = id(nbi.unit[0].energy.data)

    assert nbi.unit[0].energy.data.coordinates.time_index == 0

    imaspy.util.resample(
        nbi.unit[0].energy.data,
        nbi.time,
        [0.5, 1.5],
        nbi.ids_properties.homogeneous_time,
        inplace=True,
        fill_value="extrapolate",
    )

    assert old_id == id(nbi.unit[0].energy.data)
    assert nbi.unit[0].energy.data == [1, 3]


def test_single_resample_copy():
    nbi = IDSFactory().new("nbi")
    nbi.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    nbi.time = [1, 2, 3]
    nbi.unit.resize(1)
    nbi.unit[0].energy.data = 2 * nbi.time
    old_id = id(nbi.unit[0].energy.data)

    assert nbi.unit[0].energy.data.coordinates.time_index == 0

    new_data = imaspy.util.resample(
        nbi.unit[0].energy.data,
        nbi.time,
        [0.5, 1.5],
        nbi.ids_properties.homogeneous_time,
        inplace=False,
        fill_value="extrapolate",
    )

    assert old_id != id(new_data)
    assert new_data == [1, 3]


def test_full_resample_inplace():
    nbi = IDSFactory().new("nbi")
    nbi.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    nbi.time = [1, 2, 3]
    nbi.unit.resize(1)
    nbi.unit[0].energy.data = 2 * nbi.time
    old_id = id(nbi.unit[0].energy.data)

    assert nbi.unit[0].energy.data.coordinates.time_index == 0

    _ = imaspy.util.resample(
        nbi,
        nbi.time,
        [0.5, 1.5],
        nbi.ids_properties.homogeneous_time,
        inplace=True,
        fill_value="extrapolate",
    )

    assert old_id == id(nbi.unit[0].energy.data)
    assert nbi.unit[0].energy.data == [1, 3]
    assert nbi.time == [0.5, 1.5]


def test_full_resample_copy():
    nbi = IDSFactory().new("nbi")
    nbi.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    nbi.time = [1, 2, 3]
    nbi.unit.resize(1)
    nbi.unit[0].energy.data = 2 * nbi.time
    old_id = id(nbi.unit[0].energy.data)

    assert nbi.unit[0].energy.data.coordinates.time_index == 0

    new_nbi = imaspy.util.resample(
        nbi,
        nbi.time,
        [0.5, 1.5],
        nbi.ids_properties.homogeneous_time,
        inplace=False,
        fill_value="extrapolate",
    )

    assert old_id != id(new_nbi.unit[0].energy.data)
    assert new_nbi.unit[0].energy.data == [1, 3]
    assert new_nbi.time == [0.5, 1.5]
