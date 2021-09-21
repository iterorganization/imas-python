#!/bin/bash
# Boilerplate scripts and functions needed for other scripts
set -xeuf -o pipefail
function finish {
  [[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_name=${BASH_SOURCE[0]} || my_name=$0
  if [[ "$my_name" == *.sh ]]; then
    echo '[DEBUG] Clearing set and shopt flags using eval "\$one_csmd"'
    # Wrap all set/shopt commands into a single big command
    one_cmd=${old_bash_state//$'\n'/'; '}$'\n'
    # Do not show the huge xtrace of this evail
    set +x
    eval "$one_cmd"
    set -x
  fi
}
trap finish EXIT RETURN
