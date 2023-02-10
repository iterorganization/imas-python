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
if [ -n "${XDG_CACHE_HOME:-}" ]; then
    echo "XDG_CACHE_HOME set to $XDG_CACHE_HOME"
    # IMASPy uses $XDG_CACHE_HOME/imaspy as cache folder
    chmod u+w -R "$XDG_CACHE_HOME/imaspy" || true
    rm -Rf "$XDG_CACHE_HOME/imaspy"
else
    # $XDG_CACHE_HOME unset: IMASPy uses ~/.cache/imaspy as cache folder
    echo "XDG_CACHE_HOME unset"
    chmod u+w -R ~/.cache/imaspy || true
    rm -Rf ~/.cache/imaspy
fi
