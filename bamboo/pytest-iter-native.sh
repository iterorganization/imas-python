#!/bin/sh
# Set up ITER modules environment
set -e
my_dir=$(dirname $0)
. $my_dir/00_setenv_modules.sh
. $my_dir/10_setenv_imas_monorepo.sh
. $my_dir/20_setenv_imaspy.sh
. $my_dir/30_build_imaspy.sh
. $my_dir/40_install_imaspy.sh
. $my_dir/50_pytest_imaspy.sh ${1:=mini}
