#!/bin/bash
# enable SDCC module system
source /usr/share/Modules/init/sh
module purge

# Build the IMASPy package and run tests on an ITER SDCC-like environment
module load IMAS
# the MDSplus-Java module is needed for jTraverser.jar
module load MDSplus-Java/7.96.17-GCCcore-10.2.0-Java-11

# Create a new venv for a clean build
# use 'system-site-packages' to pick up modules
# this is optional, and the below will also work without it
python -m venv --system-site-packages --clear venv_imaspy
source venv_imaspy/bin/activate


# We need to upgrade a few modules beyond what SDCC provides:
# - tomli: needed for reading pyproject.toml
# - setuptools & pip: to read package information (name, dependencies) from pyproject.toml
pip install --upgrade pip setuptools tomli

# when disabling build isolation the build dependencies are not installed, install them manually
pip install --upgrade gitpython
