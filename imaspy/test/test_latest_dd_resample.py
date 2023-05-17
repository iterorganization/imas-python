"""A testcase checking if resampling works for the latest data dictionary version.
"""

import imaspy
from imaspy.ids_defs import IDS_TIME_MODE_HOMOGENEOUS


def test_single_resample_inplace():
    ids = imaspy.ids_root.IDSRoot(1, 0)
    ids.nbi.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.nbi.time = [1, 2, 3]
    ids.nbi.unit.resize(1)
    ids.nbi.unit[0].energy.data = 2 * ids.nbi.time
    old_id = id(ids.nbi.unit[0].energy.data)

    assert ids.nbi.unit[0].energy.data.time_axis == 0

    ids.nbi.unit[0].energy.data.resample(
        ids.nbi.time,
        [0.5, 1.5],
        ids.nbi.ids_properties.homogeneous_time,
        inplace=True,
        fill_value="extrapolate",
    )

    assert old_id == id(ids.nbi.unit[0].energy.data)
    assert ids.nbi.unit[0].energy.data == [1, 3]


def test_single_resample_copy():
    ids = imaspy.ids_root.IDSRoot(1, 0)
    ids.nbi.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.nbi.time = [1, 2, 3]
    ids.nbi.unit.resize(1)
    ids.nbi.unit[0].energy.data = 2 * ids.nbi.time
    old_id = id(ids.nbi.unit[0].energy.data)

    assert ids.nbi.unit[0].energy.data.time_axis == 0

    new_data = ids.nbi.unit[0].energy.data.resample(
        ids.nbi.time,
        [0.5, 1.5],
        ids.nbi.ids_properties.homogeneous_time,
        inplace=False,
        fill_value="extrapolate",
    )

    assert old_id != id(new_data)
    assert new_data == [1, 3]


def test_full_resample_inplace():
    ids = imaspy.ids_root.IDSRoot(1, 0)
    ids.nbi.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.nbi.time = [1, 2, 3]
    ids.nbi.unit.resize(1)
    ids.nbi.unit[0].energy.data = 2 * ids.nbi.time
    old_id = id(ids.nbi.unit[0].energy.data)

    assert ids.nbi.unit[0].energy.data.time_axis == 0

    _ = ids.nbi.resample(
        ids.nbi.time,
        [0.5, 1.5],
        ids.nbi.ids_properties.homogeneous_time,
        inplace=True,
        fill_value="extrapolate",
    )

    assert old_id == id(ids.nbi.unit[0].energy.data)
    assert ids.nbi.unit[0].energy.data == [1, 3]
    assert ids.nbi.time == [0.5, 1.5]


def test_full_resample_copy():
    ids = imaspy.ids_root.IDSRoot(1, 0)
    ids.nbi.ids_properties.homogeneous_time = IDS_TIME_MODE_HOMOGENEOUS
    ids.nbi.time = [1, 2, 3]
    ids.nbi.unit.resize(1)
    ids.nbi.unit[0].energy.data = 2 * ids.nbi.time
    old_id = id(ids.nbi.unit[0].energy.data)

    assert ids.nbi.unit[0].energy.data.time_axis == 0

    new_nbi = ids.nbi.resample(
        ids.nbi.time,
        [0.5, 1.5],
        ids.nbi.ids_properties.homogeneous_time,
        inplace=False,
        fill_value="extrapolate",
    )

    assert old_id != id(new_nbi.unit[0].energy.data)
    assert new_nbi.unit[0].energy.data == [1, 3]
    assert new_nbi.time == [0.5, 1.5]
