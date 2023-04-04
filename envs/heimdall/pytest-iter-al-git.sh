#!/bin/sh
# Set up ITER modules environment
set -xeuf -o pipefail

my_dir=$(dirname $0)
common_dir=$(dirname $my_dir)/common

###############
# Script body #
###############


AL_GIT_IDENTIFIER=${1:-develop}
# use the latest tagged version if not given
DD_GIT_IDENTIFIER="${2:-}"

. $my_dir/00_setenv_modules.sh
. $common_dir/01_cleanenv_imaspy.sh
. $common_dir/10_setenv_python.sh
. $my_dir/20_setenv_imas_git.sh
. $common_dir/22_build_python_venv.sh
. $common_dir/25_build_imas_git.sh $AL_GIT_IDENTIFIER $DD_GIT_IDENTIFIER
. $common_dir/35_build_imaspy.sh
. $common_dir/36_install_imaspy.sh
. $common_dir/70_pytest_imaspy.sh mini
