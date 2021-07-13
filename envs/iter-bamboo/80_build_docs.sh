#!/bin/sh
# Build HTML pages from source
set -xe
my_dir=$(dirname $0)

# Use the sphinx matching the venv we are in using SPHINXBUILD
make -C docs html SPHINXBUILD="$PYTHON -m sphinx"
