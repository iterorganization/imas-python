#!/bin/bash
# Build the IMASPy package and run tests on an ITER SDCC-like environment with a monorepo build

# Script boilerplate
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && iter_dir=$(dirname ${BASH_SOURCE[0]}) || iter_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=${iter_dir}/../common
. $common_dir/00_common_bash.sh

old_bash_state="$(get_bash_state "$old_bash_state")"
set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

echo '[WARN] Not tested in CI! Warning!'

. $iter_dir/00_setenv_modules.sh
. $common_dir/01_cleanenv_imaspy.sh
. $common_dir/10_setenv_python.sh
. $iter_dir/21_setenv_imas_monorepo.sh
. $common_dir/35_build_imaspy.sh
. $common_dir/36_install_imaspy.sh
. $common_dir/70_pytest_imaspy.sh mini
