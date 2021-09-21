#!/bin/bash
# Pip install IMASPy package plus its (optional) dependencies

# Script boilerplate
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=$my_dir
. $common_dir/00_common_bash.sh

old_bash_state=$(get_bash_state)
set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

# This will install the latest IMASPy
# As we clear the dist folder with 01_cleanenv_imaspy.sh
# there will be only one candidate to install
#$PIP install --no-cache --find-links=dist imaspy[all]
$PIP install --pre --upgrade --find-links=dist imaspy[all]
