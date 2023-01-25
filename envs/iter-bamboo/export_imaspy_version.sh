#!/bin/bash
# Set up a basic IMASPy environment and export the IMASPy version

# Script boilerplate
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && iter_dir=$(dirname ${BASH_SOURCE[0]}) || iter_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=${iter_dir}/../common
. $common_dir/00_common_bash.sh

old_bash_state="$(get_bash_state "$old_bash_state")"
set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

AL_GIT_IDENTIFIER="${1:-develop}"
# use the latest tagged version if not given
DD_GIT_IDENTIFIER="${2:-}"

. $iter_dir/00_setenv_modules.sh
. $common_dir/01_cleanenv_imaspy.sh
. $common_dir/10_setenv_python.sh
. $iter_dir/20_setenv_imas_git_sdcc.sh
source $IMASPY_VENV/bin/activate
export IMASPY_VERSION=`$PYTHON setup.py --version`