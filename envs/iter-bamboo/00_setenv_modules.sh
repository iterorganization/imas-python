#!/bin/sh
# Set up ITER modules environment
set -e

# Set up environment
. /usr/share/Modules/init/sh
module use /work/imas/etc/modulefiles
module use /work/imas/etc/modules/all
module purge
