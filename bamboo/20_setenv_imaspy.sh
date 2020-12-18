#!/bin/sh
# Set up IMASPy Python environment
export PYTHON_INSTALL_DIR=${PYTHON_INSTALL_DIR:-`pwd`/install}
export build_deps=$(cat pyproject.toml | grep requires | cut -d'=' -f2- | tr -d ,\"\' | sed "s/^ \[//" | sed "s/\]$//")
cd `pwd`
pwd
ls
export run_dep_files=$(find 'requirements_*' -maxdepth 1 -and -not -name "*test*" -and -not -name "*backends_al*" -and -not -name "*examples*")
export test_deps=$(find requirements_* -maxdepth 1 -and -name "*test*")

export PATH=$PYTHON_INSTALL_DIR/bin:${PATH}
export PYTHONPATH=$PYTHON_INSTALL_DIR:${PYTHONPATH}
export PYTHONUSERBASE=$PYTHON_INSTALL_DIR
export PIP="python -m pip"
export PYTEST="python -m pytest"
