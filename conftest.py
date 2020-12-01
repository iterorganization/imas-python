# This file is part of IMASPy.
# You should have received IMASPy LICENSE file with this project.
#
# Set up pytest so that any mention of 'backend' as a test argument
# gets run with all four backends.
# Same for ids_type, with all types

from imaspy.ids_defs import ASCII_BACKEND, HDF5_BACKEND, MDSPLUS_BACKEND, MEMORY_BACKEND
from imaspy.test_minimal_types_io import TEST_DATA


def pytest_addoption(parser):
    parser.addoption(
        "--memory", action="store_true", help="test with memory backend only"
    )
    parser.addoption(
        "--ascii", action="store_true", help="test with ascii backend only"
    )


def pytest_generate_tests(metafunc):
    if "backend" in metafunc.fixturenames:
        if metafunc.config.getoption("ascii"):
            metafunc.parametrize("backend", [ASCII_BACKEND])
        elif metafunc.config.getoption("memory"):
            metafunc.parametrize("backend", [MEMORY_BACKEND])
        else:
            metafunc.parametrize(
                "backend",
                [MEMORY_BACKEND, ASCII_BACKEND, MDSPLUS_BACKEND, HDF5_BACKEND],
            )
    if "ids_type" in metafunc.fixturenames:
        metafunc.parametrize("ids_type", [None] + list(TEST_DATA.keys()))
