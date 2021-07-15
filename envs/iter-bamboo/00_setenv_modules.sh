#!/bin/sh
# Set up ITER modules environment
set -xeuf -o pipefail

# For the bash starters, we use the following flags:
# https://tldp.org/LDP/abs/html/options.html
# -v          verbose       Print each command to stdout before executing it
# -x          xtrace        Similar to -v, but expands commands
# -e          errexit       Abort script at first error, when a command exits with non-zero status (except in until or while loops, if-tests, list constructs)
# -u          nounset       Attempt to use undefined variable outputs error message, and forces an exit
# -f          noglob        Filename expansion (globbing) disabled
# -o pipefail pipe failure  Causes a pipeline to return the exit status of the last command in the pipe that returned a non-zero return value.

# Set up environment
. /usr/share/Modules/init/sh
module use /work/imas/etc/modulefiles
module use /work/imas/etc/modules/all
module purge

# Load base "should be always there" modules
module load git
