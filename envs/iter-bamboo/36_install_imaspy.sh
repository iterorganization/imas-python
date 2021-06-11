#!/bin/sh
# Pip install IMASPy package
set -xe

# This will install the latest IMASPy
# As we clear the dist folder with 01_cleanenv_imaspy.sh
# there will be only one candidate to install
#$PIP install --no-cache --find-links=dist imaspy[all]
$PIP install --pre --upgrade --find-links=dist imaspy[all]
