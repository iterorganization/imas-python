#!/bin/bash
# Bamboo CI script to build IDSDef.zip
# Note: this script should be run from the root of the git repository

# Debuggging:
set -e -o pipefail
echo "Loading modules..."

# Set up environment such that module files can be loaded
. /usr/share/Modules/init/sh
module purge
# Load modules required for building the DD zip:
# - Python (obviously)
# - GitPython (providing `git` package)
# - Saxon (required for building the DD)
module load Python/3.8.6-GCCcore-10.2.0 GitPython/3.1.14-GCCcore-10.2.0 Saxon-HE/10.3-Java-11

# Debuggging:
echo "Done loading modules"
set -x

# Build the DD zip
python imaspy/dd_helpers.py
