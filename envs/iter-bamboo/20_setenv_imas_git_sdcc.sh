#!/bin/bash
# Use the separate parts of IMAS instead of the IMAS module

# Script boilerplate
export old_bash_state="$(shopt -po; shopt -p)"; [[ -o errexit ]] && old_bash_state="$old_bash_state; set -e"  # Save bash state
set -xeuf -o pipefail # Set default script debugging flags
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=${my_dir}/../common
. $common_dir/00_common_bash.sh

###############
# Script body #
###############

# Based on IMAS/3.32.1-4.9.1-2020b
# This is strictly versioned to catch errors early
module load GCCcore/10.2.0
module load Python/3.8.6-GCCcore-10.2.0
module load MDSplus/7.96.17-GCCcore-10.2.0
module load HDF5/1.10.7-iimpi-2020b  # TODO: Intel MPI version?
module load Boost/1.74.0-GCCcore-10.2.0

# Extra modules that we need to build
module load MDSplus-Java/7.96.17-GCCcore-10.2.0-Java-11
module load Saxon-HE/10.3-Java-11

# Documentation for data-dictionary
module load Doxygen/1.8.20-GCCcore-10.2.0

# Very ugly way to just get saxon-he-10.3.jar, which we need for the DD
export SAXONJARFILE=`echo $CLASSPATH | cut -d: -f4 | rev | cut -d/ -f1 | rev`
echo [INFO] Set SAXONJARFILE to $SAXONJARFILE

module list
