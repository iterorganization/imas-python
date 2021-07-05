#!/bin/sh
# Install build dependencies and build IMASPy
# IMAS dependencies are build in another file
set -xe

# Pip install build dependencies
# Make sure build dependencies are up to date
# Assume we are in a venv
pyproject_deps=`cat pyproject.toml | grep requires | cut -d= -f2- | sed "s/,//g" | sed 's/"//g'`
IMASPY_BUILD_DEPS=${pyproject_deps:2:-1}
$PIP install --upgrade pip setuptools
$PIP install --upgrade $IMASPY_BUILD_DEPS

$PYTHON setup.py build
$PYTHON setup.py sdist bdist_wheel
