#!/bin/sh
# Build HTML pages from source
set -xe
my_dir=$(dirname $0)

# Use the sphinx matching the venv we are in using SPHINXBUILD
# We should be in the ???? dir when running this
VENV_SPHINX_BUILD='../venv_imaspy/bin/sphinx-build'
make -C docs html SPHINXBUILD="$PYTHON $VENV_SPHINX_BUILD"
