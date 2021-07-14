#!/bin/sh
# Set up Python environment
set -xeuf -o pipefail

# We assume we can use the build-in Python venv
# As the module environment handles many of the packages
# we use, give venv access to system site packages
$PYTHON --version
$PYTHON -m venv --system-site-packages --clear venv_imaspy
# Note that source venv_imaspy/bin/activate needs to be placed
# on top of every script that installs locally!
source $IMASPY_VENV/bin/activate
