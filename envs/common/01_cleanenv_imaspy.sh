#!/bin/bash
# Clean IMASPy environment

# Script boilerplate
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=$my_dir
. $common_dir/00_common_bash.sh

old_bash_state="$(get_bash_state "$old_bash_state")"
set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

# Clean MDSplus model cache
chmod u+w -R ~/.cache/imaspy || true
rm -Rf ~/.cache/imaspy
