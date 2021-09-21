#!/bin/bash
# Build the IMASPy documentation pages

# Script boilerplate
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=${my_dir}/../common
. $common_dir/00_common_bash.sh

old_bash_state=$(get_bash_state)
set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

. $my_dir/00_setenv_modules.sh
. $common_dir/01_cleanenv_imaspy.sh
. $common_dir/10_setenv_python.sh
. $my_dir/20_setenv_imas_git_sdcc.sh
. $common_dir/22_build_python_venv.sh
. $common_dir/25_build_imas_git.sh ${1:-develop}
. $common_dir/35_build_imaspy.sh
. $common_dir/36_install_imaspy.sh
. $common_dir/80_build_docs.sh
