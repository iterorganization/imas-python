#!/bin/bash
# Bamboo CI script to build IDSDef.zip
# Note: this script should be run from the root of the git repository

# Debuggging:
set -e -o pipefail
echo "Loading modules..."

# Set up environment such that module files can be loaded
. /usr/share/Modules/init/sh
module purge
# Modules are supplied as arguments in the CI job:
module load $@

# Debuggging:
echo "Done loading modules"
set -x

# Build the DD zip
python imaspy/dd_helpers.py
