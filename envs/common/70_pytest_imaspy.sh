#!/bin/bash
# Run pytest with a standard collection of flags. These flags can be
# adjusted using environment variables

# Script boilerplate
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=$my_dir
. $common_dir/00_common_bash.sh

old_bash_state=$(get_bash_state)
set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

PYTEST_FLAGS=${PYTEST_FLAG:-'-n=auto'}
COV_FLAGS=${COV_FLAGS:-'--cov=imaspy --cov-report=term --cov-report=xml:./coverage.xml'}
JUNIT_FLAGS=${JUNIT_FLAGS:-'--junit-xml=./junit.xml'}
PYTEST_MARK=${PYTEST_MARK:-''}
IDSS=${IDSS:-pulse_schedule,ece}

source $IMASPY_VENV/bin/activate
# Run tests in different directory
mkdir -p empty
pushd empty

# Check if we can call pytest and show modules
$PYTEST -VV

if [ "$1" == "mini" ]; then
    $PYTEST --ids=$IDSS $PYTEST_FLAGS $COV_FLAGS $JUNIT_FLAGS -m "$PYTEST_MARK" ../imaspy
else
    echo Untested!
    exit 1
    #$PYTEST $PYTEST_FLAGS $COV_FLAGS $JUNIT_FLAGS -m "$PYTEST_MARK" ../imaspy
fi

popd
