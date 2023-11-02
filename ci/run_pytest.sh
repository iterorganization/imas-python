#!/bin/bash
# Bamboo CI script to install imaspy and run all tests
# Note: this script should be run from the root of the git repository

# Set up environment such that module files can be loaded
. /usr/share/Modules/init/sh
module purge

# Modules are supplied as arguments in the CI job:
module load $@

# Set up the testing venv
rm -rf venv  # Environment should be clean, but remove directory to be sure
python -m venv --system-site-packages venv
source venv/bin/activate

# Install imaspy and test dependencies
pip install --upgrade pip setuptools wheel
pip install .[test]

# Run pytest
# Clean artifacts created by pytest
rm -f junit.xml
rm -rf htmlcov
pytest -n=auto --cov=imaspy --cov-report=term-missing --cov-report=html --junit-xml=junit.xml
