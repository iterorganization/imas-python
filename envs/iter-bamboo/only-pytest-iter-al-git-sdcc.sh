#!/bin/bash
# Run only the testing for the IMASPy on an ITER SDCC-like environment

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
. $common_dir/10_setenv_python.sh
. $iter_dir/20_setenv_imas_git_sdcc.sh

# We assume the access layer Python components and DDs have been
# build previously with `$common_dir/25_build_imas_git.sh`. We
# just re-use those componants and steal the exports
export IMAS_VERSION=`git -C data-dictionary tag | sort -V | tail -n 1`
pushd access-layer
export UAL_VERSION=`git tag | sort -V | tail -n 1`

export IMAS_PREFIX=`pwd`
export LIBRARY_PATH=`pwd`/lowlevel:${LIBRARY_PATH:=}
export C_INCLUDE_PATH=`pwd`/lowlevel:${C_INCLUDE_PATH:=}
export LD_LIBRARY_PATH=`pwd`/lowlevel:${LD_LIBRARY_PATH:=}
popd

# We assume the venv has been build with
# `$common_dir/22_build_python_venv.sh`. We re-use that venv here.
source $IMASPY_VENV/bin/activate

$PYTHON -c 'import imas'

AL_GIT_IDENTIFIER="${1:-develop}"
TESTSET="${2:-mini}"
RUNMODE="${3:-normal}"
. $common_dir/70_pytest_imaspy.sh $TESTSET $RUNMODE
