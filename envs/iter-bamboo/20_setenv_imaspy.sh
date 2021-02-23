#!/bin/sh
# Set up IMASPy Python environment
export PYTHON_INSTALL_DIR=${PYTHON_INSTALL_DIR:-`pwd`/install}

export PATH=$PYTHON_INSTALL_DIR/bin:${PATH}
export PYTHONPATH=$PYTHON_INSTALL_DIR:${PYTHONPATH}
export PYTHONUSERBASE=$PYTHON_INSTALL_DIR
export PIP="python -m pip"
export PYTEST="python -m pytest"
