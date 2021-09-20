#!/bin/sh
# Install build dependencies and build IMASPy
# IMAS dependencies are build in another file
set -xeuf -o pipefail

# Build based on Python Packaging Authority recommendations
# https://packaging.python.org/guides/tool-recommendations/
# Use setuptools to define projects.
# Use build to create Source Distributions and wheels
$PIP install --upgrade pip
$PIP install --upgrade setuptools build

# Install build dependencies manually, PyPA build does not automatically install them
pyproject_deps=`cat pyproject.toml | grep requires | cut -d= -f2- | sed "s/,//g" | sed 's/"//g'`
IMASPY_BUILD_DEPS=${pyproject_deps:2:-1}
$PIP install --upgrade $IMASPY_BUILD_DEPS

# Do not use build isolation; we need IMAS components and Linux modules to be available
$PYTHON -m build --no-isolation
