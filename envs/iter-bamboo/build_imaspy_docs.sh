#!/bin/sh
# Set up ITER modules environment
set -e
my_dir=$(dirname $0)

. $my_dir/00_setenv_modules.sh
. $my_dir/01_cleanenv_imaspy.sh
. $my_dir/10_setenv_python.sh
. $my_dir/20_build_imas_git.sh master
. $my_dir/30_setenv_imaspy.sh
. $my_dir/35_build_imaspy.sh
. $my_dir/36_install_imaspy.sh
. $my_dir/80_build_docs.sh
