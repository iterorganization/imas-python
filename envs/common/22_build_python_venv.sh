#!/bin/bash
# Set up Python venv

# Script boilerplate
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=$my_dir
. $common_dir/00_common_bash.sh

old_bash_state="$(get_bash_state "$old_bash_state")"
set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

# We assume we can use the build-in Python venv
# As the module environment handles many of the packages
# we use, give venv access to system site packages
$PYTHON --version
$PYTHON -m venv --system-site-packages --clear venv_imaspy
# Note that source venv_imaspy/bin/activate needs to be placed
# on top of every script that installs locally!
source $IMASPY_VENV/bin/activate

echo "22_build_python_venv packages"
$PIP freeze
