# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
import os
from pathlib import PosixPath
from importlib_resources import files

import imaspy
import pytest


def test_data_exists():
    data_file: PosixPath = files(imaspy) / "assets/ITER_134173_106_equilibrium.ids"
    assert data_file.exists()


@pytest.fixture
def test_data():
    data_file: PosixPath = files(imaspy) / "assets/ITER_134173_106_equilibrium.ids"
    shot, run, user, database = 134173, 106, "public", "ITER"
    assert data_file.exists()
    ocwd = os.getcwd()
    os.chdir(data_file.parent)
    db_entry = imaspy.DBEntry(imaspy.ids_defs.ASCII_BACKEND, database, shot, run)
    db_entry.open()
    yield db_entry
    os.chdir(ocwd)
    db_entry.close()


def test_data_is_sane(test_data):
    assert isinstance(test_data, imaspy.DBEntry)
    eq = test_data.get("equilibrium")
    assert len(eq.time_slice) == 1
    ts = eq.time_slice[0]
    r = ts.boundary.outline.r
    z = ts.boundary.outline.z

    # Test a few relevant numbers to check if data loading went okay
    assert r.value[0] == pytest.approx(7.2896011)
    assert r.value[-1] == pytest.approx(7.29120937)
    assert z.value[0] == pytest.approx(-1.00816660e-01)
    assert z.value[-1] == pytest.approx(-9.60027185e-14)
