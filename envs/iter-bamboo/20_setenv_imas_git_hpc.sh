#!/bin/bash
# Use the separate parts of IMAS instead of the IMAS module

# Script boilerplate
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=${my_dir}/../common
. $common_dir/00_common_bash.sh

old_bash_state="$(get_bash_state "$old_bash_state")"
set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

set -xeuf -o pipefail
module load GCC/9.3.0
module load Python/3.8.2-GCCcore-9.3.0
module load Saxon-HE/9.9.1.7-Java-13
module load MDSplus/7.96.12-GCCcore-9.3.0
module load MDSplus-Java/7.96.12-GCCcore-9.3.0-Java-13
module load HDF5/1.12.0-gompi-2020a
module load Boost/1.72.0-GCCcore-9.3.0-no_mpi
module list

