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

. $iter_dir/00_setenv_modules.sh
. $common_dir/01_cleanenv_imaspy.sh
. $common_dir/10_setenv_python.sh
. $iter_dir/20_setenv_imas_git_sdcc.sh
# Assume the access-layer et al. is already build; reuse definitions from 25_build_imas_git.sh
export LD_LIBRARY_PATH=`pwd`/access-layer/lowlevel:${LD_LIBRARY_PATH:=}
# Re-use the python env from 22_build_python_venv.sh
source $IMASPY_VENV/bin/activate
export IMASPY_VERSION=`imaspy print-version`
echo IMASPY_VERSION=$IMASPY_VERSION
