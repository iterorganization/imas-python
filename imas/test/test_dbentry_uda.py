from pathlib import Path
import os
from unittest.mock import patch

import pytest
from packaging.version import Version

from imas import DBEntry
from imas.ids_defs import READ_OP


@pytest.fixture
def mock_read_data():
    return {
        "ids_properties/homogeneous_time": 1,
        "ids_properties/version_put/data_dictionary": "4.0.0",
    }


@pytest.fixture
def mock_ll_interface(mock_read_data):
    """Mock the IMAS lowlevel interface so we can still test the our UDA-specific logic.

    Since we don't have a public UDA server available to test against, this is the
    next-best thing.
    """
    with patch("imas.backends.imas_core.db_entry_al.ll_interface") as mock_ll_interface:
        mock_ll_interface.begin_dataentry_action.return_value = (0, 0)
        mock_ll_interface.begin_global_action.return_value = (0, 0)
        mock_ll_interface.begin_arraystruct_action.return_value = (0, 0, 0)
        mock_ll_interface.close_pulse.return_value = 0
        mock_ll_interface._al_version = Version("5.6.0")

        def read_data(ctx, fieldPath, pyTimebasePath, ualDataType, dim):
            return 0, mock_read_data.get(fieldPath)

        mock_ll_interface.read_data.side_effect = read_data

        # Also patch in al_context.py:
        with patch(
            "imas.backends.imas_core.al_context.ll_interface", mock_ll_interface
        ):
            yield mock_ll_interface


def test_uda_idsdef_path(mock_ll_interface):
    # Check that IDSDEF_PATH env variable is set for the UDA backend
    with DBEntry("imas:uda?mock", "r", dd_version="4.0.0"):
        assert "IDSDEF_PATH" in os.environ
        path1 = Path(os.environ["IDSDEF_PATH"])
        assert path1.exists()
    with DBEntry("imas:uda?mock", "r", dd_version="3.42.0"):
        assert "IDSDEF_PATH" in os.environ
        path2 = Path(os.environ["IDSDEF_PATH"])
        assert path2.exists()
    assert path1 != path2


def test_uda_datapath(mock_ll_interface):
    # Check that datapath is set when requesting the dd version
    with DBEntry("imas:uda?mock", "r", dd_version="4.0.0") as entry:
        mock_ll_interface.begin_global_action.assert_not_called()
        entry.get("mhd", lazy=True)
        # pulseCtx=0, dataobjectname="mhd", rwmode=READ_OP, datapath="ids_properties"
        mock_ll_interface.begin_global_action.assert_called_with(
            0, "mhd", READ_OP, "ids_properties"
        )


def test_uda_version_mismatch_exception(mock_ll_interface):
    # Check that we get an exception when versions mismatch
    with pytest.raises(RuntimeError, match="Data Dictionary version"):
        DBEntry("imas:uda?path=mock", "r", dd_version="4.1.0").get("mhd")
    # No exceptions when using cache_mode=none
    DBEntry("imas:uda?path=mock&cache_mode=none", "r", dd_version="4.1.0").get("mhd")
    # Or when using fetch
    DBEntry("imas:uda?path=mock&fetch=true", "r", dd_version="4.1.0").get("mhd")
    DBEntry("imas:uda?path=mock&fetch=1", "r", dd_version="4.1.0").get("mhd")
    # Or when using the exact same DD version
    DBEntry("imas:uda?path=mock", "r", dd_version="4.0.0").get("mhd")
