#!/bin/bash
# Build IMASPy to be maximally compatible with SDCC IMAS default module.
# this means reusing all dependencies from modules, skipping build isolation etc
set -eu

# clear any cache that may have remained from earlier builds
rm -Rf ${XDG_CACHE_DIR-~/.cache}/imaspy

# Load any ITER modules
source $(dirname ${BASH_SOURCE[0]})/iter-env.sh

# The build isolation causes a new version of numpy to be downloaded,
# which is not compatible with the one included with the IMAS SciPy-bundle
# module.
# See https://github.com/pypa/pip/issues/6264
# and accompanying error message
pip install --no-build-isolation -v -e .[test]
# when not using editable mode the compiled components cannot be found...

# Finally we can run our testcase
pytest imaspy --mini \
  -n=auto \
  --cov=imaspy \
  --cov-report=term \
  --cov-report=xml:./coverage.xml \
  --junitxml=./junit.xml
