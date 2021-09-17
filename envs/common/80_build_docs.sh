#!/bin/sh
# Build HTML pages from source
set -xeuf -o pipefail

my_dir=$(dirname $0)

# Use the sphinx matching the venv we are in using SPHINXBUILD
VENV_SPHINX_BUILD='../venv_imaspy/bin/sphinx-build'
make -C docs html SPHINXBUILD="$PYTHON $VENV_SPHINX_BUILD"
