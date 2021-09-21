#!/bin/bash
# Set up user-like IMAS env using the IMAS module

# Script boilerplate
export old_bash_state="$(shopt -po; shopt -p)"; [[ -o errexit ]] && old_bash_state="$old_bash_state; set -e"  # Save bash state
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=${my_dir}/../common
. $common_dir/00_common_bash.sh

set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

# Use specific IMAS prerequisites 
module load Python/3.6.4-intel-2018a
module load Cython/0.28.6-intel-2018a-Python-3.6.4

# But for now import IMAS itself
module load IMAS
