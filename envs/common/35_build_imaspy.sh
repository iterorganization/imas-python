#!/bin/bash
# Install build dependencies and build IMASPy
# IMAS dependencies are build prior to this script

# Script boilerplate
export old_bash_state="$(shopt -po; shopt -p)"; [[ -o errexit ]] && old_bash_state="$old_bash_state; set -e"  # Save bash state
set -xeuf -o pipefail # Set default script debugging flags
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=$my_dir
. $common_dir/00_common_bash.sh

###############
# Script body #
###############

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
