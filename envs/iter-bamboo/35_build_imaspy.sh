#!/bin/sh
# Install build dependencies and build IMASPy
# IMAS dependencies are build in another file
set -xeuf -o pipefail

# Pip install build dependencies
$PIP install --upgrade pip setuptools

$PYTHON $SETUP_PY build build_ext
$PYTHON $SETUP_PY sdist bdist_wheel
