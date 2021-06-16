#!/bin/sh
# Set up ITER modules environment
set -e
my_dir=$(dirname $0)
. $my_dir/00_setenv_modules.sh
. $my_dir/01_cleanenv_imaspy.sh
. $my_dir/10_setenv_python.sh
. $my_dir/20_setenv_imas_git_sdcc.sh
. $my_dir/22_build_python_venv.sh
. $my_dir/25_build_imas_git.sh ${1:-develop}
. $my_dir/35_build_imaspy.sh
. $my_dir/36_install_imaspy.sh
. $my_dir/70_pytest_imaspy.sh mini
