#!/bin/bash
# Set up Python environment

# Script boilerplate
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=$my_dir
. $common_dir/00_common_bash.sh

old_bash_state=$(get_bash_state)
set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

export PYTHON=${PYTHON:-python}
export PIP=${PIP:-$PYTHON -m pip}
export PYTEST=${PYTEST:-$PYTHON -m pytest}
export IMASPY_VENV=venv_imaspy

export SETUP_PY=${SETUP_PY:-$my_dir/../../setup.py}
