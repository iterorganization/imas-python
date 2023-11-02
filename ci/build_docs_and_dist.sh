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

# Create sdist and wheel
pip install --upgrade pip setuptools wheel build
rm -rf imaspy/dist
python -m build --no-isolation .

# Install imaspy and documentation dependencies from wheel
pip install "imaspy/dist/*.whl[docs]"

# Run sphinx to create the documentation
export SPHINXOPTS='-W --keep-going'  # Treat all warnings as errors
make -C docs clean html
