#!/bin/sh
# Set up Python environment
set -xe

export PYTHON=${PYTHON:-python}
export PIP=${PIP:-$PYTHON -m pip}
export PYTEST=${PYTEST:-$PYTHON -m pytest}
export IMASPY_VENV=venv_imaspy
