#!/bin/sh
# Set up Python environment
set -e

export PYTHON_INSTALL_DIR=${PYTHON_INSTALL_DIR:-`make echo_env 2> /dev/null | grep PYTHON_INSTALL_DIR= | cut -d= -f2`}
export IMASPY_TMP_DIR=${IMASPY_TMP_DIR:-`make echo_env 2> /dev/null | grep IMASPY_TMP_DIR= | cut -d= -f2`}

#export PYTHONPATH=$PYTHON_INSTALL_DIR:$PYTHONPATH
export PATH=`pwd`$PYTHON_INSTALL_DIR/bin:$PATH
export PYTHONUSERBASE=`pwd`$PYTHON_INSTALL_DIR

echo [INFO] Preprended `pwd`$PYTHON_INSTALL_DIR to PATH
echo [INFO] Set UPYTHONUSERBASE to `pwd`$PYTHON_INSTALL_DIR
