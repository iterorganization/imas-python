#!/bin/sh
# Set up user-like IMAS env
set -xeuf -o pipefail

# install a DD locally
if [ ! -d data-dictionary ]; then
    git clone ssh://git@git.iter.org/imas/data-dictionary.git
fi
cd data-dictionary
# use the latest tagged version
export IMAS_VERSION=`git tag | sort -V | tail -n 1`
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

$PIP install numpy cython

cd pythoninterface
make -j`nproc`
sed -e 's/imas_[^/."]*/imas/g' -i package/setup.py

# install locally
$PIP install -e package

# test if we can import the imas module
$PYTHON -c 'import imas'

cd ../../
