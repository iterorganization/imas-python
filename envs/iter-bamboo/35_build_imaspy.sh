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

$PYTHON -m build
