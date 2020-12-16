#!/bin/sh
# Bamboo Build script

set -x
set -e

# Set up environment
. /usr/share/Modules/init/sh
module use /work/imas/etc/modulefiles
module use /work/imas/etc/modules/all
module purge

# Use the develop IMAS split repo and pytest
module load Python/3.6.4-intel-2018a
module load Cython/0.28.6-intel-2018a-Python-3.6.4
module load IMAS


#tmp_dir=$(mktemp -d -p $bamboo_build_working_directory -t ci-XXX)

ids_path_old=${ids_path}

export ids_path="${tmp_dir};$ids_path"

# Set IMASPy variables
export PYTHON_INSTALL_DIR=${PYTHON_INSTALL_DIR:-`pwd`/install}
export build_deps=$(cat pyproject.toml | grep requires | cut -d'=' -f2- | tr -d ,\"\' | sed "s/^ \[//" | sed "s/\]$//")
export run_dep_files=$(find requirements_* -maxdepth 1 -and -not -name "*test*" -and -not -name "*backends_al*" -and -not -name "*examples*")
export test_deps=$(find requirements_* -maxdepth 1 -and -name "*test*")

export PATH=$PYTHON_INSTALL_DIR/bin:${PATH}
export PYTHONPATH=$PYTHON_INSTALL_DIR:${PYTHONPATH}
export PYTHONUSERBASE=$PYTHON_INSTALL_DIR
export PIP="python -m pip"

# Install build dependencies
$PIP install --user --ignore-installed pip setuptools
$PIP install --upgrade $build_deps

# installs into local /install folder
for file in $run_dep_files; do
    echo Installing $file
    $PIP install -r $file
done # Install run deps manually

#$PIP install --no-build-isolation --force-reinstall -r $test_deps # Install test dependencies manually
make install_package

# Run tests and generate reports
make tests
