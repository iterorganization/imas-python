#!/bin/sh
# Set up Python environment
set -xeuf -o pipefail

export PYTHON=${PYTHON:-python}
export PIP=${PIP:-$PYTHON -m pip}
export PYTEST=${PYTEST:-$PYTHON -m pytest}
export IMASPY_VENV=venv_imaspy

my_dir=$(dirname $0)
export SETUP_PY=${SETUP_PY:-$my_dir/../../setup.py}