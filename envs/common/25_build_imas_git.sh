#!/bin/bash
# Build a copy of IMAS components need by IMASPy from the access-layer monorepo and
# data-dictionary repo. You can specify the AL version with $1 (usually "develop" or "master")
# The DDs will be scanned by IMASPy anyway, but we'll build the default branch as well

# Script boilerplate
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=$my_dir
. $common_dir/00_common_bash.sh

old_bash_state="$(get_bash_state "$old_bash_state")"
set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

# install a DD locally
if [ ! -d data-dictionary ]; then
    git clone ssh://git@git.iter.org/imas/data-dictionary.git
fi
cd data-dictionary

export IMAS_VERSION="${2:-`git tag | sort -V | tail -n 1`}"
git checkout "$IMAS_VERSION"
#git clean -xf
make

cd ..
# INSTALL the access layer locally (this might take a while)
if [ ! -d access-layer ]; then
    git clone ssh://git@git.iter.org/imas/access-layer.git
fi
cd access-layer
git checkout "$1"
#git clean -xf
if [ ! -L xml ]; then
    ln -s ../data-dictionary/ xml
fi

export UAL_VERSION=`git tag | sort -V | tail -n 1`
export IMAS_UDA=no \
    IMAS_HDF5=yes \
    IMAS_MATLAB=no \
    IMAS_MEX=no \
    IMAS_JAVA=no

export IMAS_PREFIX=`pwd`
export LIBRARY_PATH=`pwd`/lowlevel:${LIBRARY_PATH:=}
export C_INCLUDE_PATH=`pwd`/lowlevel:${C_INCLUDE_PATH:=}
export LD_LIBRARY_PATH=`pwd`/lowlevel:${LD_LIBRARY_PATH:=}

cd lowlevel
make -j`nproc`
cd ..

$PIP install numpy "cython < 3"

cd pythoninterface
make -j`nproc`
sed -e 's/imas_[^/."]*/imas/g' -i package/setup.py

# We do not always start from a cleaned virtual environment. Uninstall possible leftover packages
$PIP uninstall --yes imas || true

# Install locally
$PIP install -e package

# test if we can import the imas module
$PYTHON -c 'import imas'

cd ../../
