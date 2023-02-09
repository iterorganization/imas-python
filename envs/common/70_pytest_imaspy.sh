#!/bin/bash
# Run pytest with a standard collection of flags. These flags can be
# adjusted using environment variables

# Script boilerplate
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && my_dir=$(dirname ${BASH_SOURCE[0]}) || my_dir=$(dirname $0)  # Determine script dir even when sourcing

common_dir=$my_dir
. $common_dir/00_common_bash.sh

old_bash_state="$(get_bash_state "$old_bash_state")"
set -xeuf -o pipefail # Set default script debugging flags

###############
# Script body #
###############

# Read CLI arguments
TESTSET="${1:-mini}"
#normal: Set up env and run pytest
#env: Only set up env, don't run pytest
#only: Only run pytest, do not set up env
RUNMODE="${2:-normal}"

if [ "$RUNMODE" == "normal" ] || [ "$RUNMODE" == "env" ]; then
    export PYTEST_FLAGS=${PYTEST_FLAGS:-'-n=auto'}
    export COV_FLAGS=${COV_FLAGS:-'--cov=imaspy --cov-report=term --cov-report=xml:./coverage.xml'}
    export JUNIT_FLAGS=${JUNIT_FLAGS:-'--junit-xml=./junit.xml'}
    export PYTEST_MARK=${PYTEST_MARK:-''}
    export IDSS=${IDSS:-pulse_schedule,ece}

    source $IMASPY_VENV/bin/activate

    # Check if we can call pytest and show modules
    $PYTEST -VV
fi

echo "70_pytest_imaspy packages"
$PIP freeze

if [ "$RUNMODE" == "normal" ] || [ "$RUNMODE" == "only" ]; then
    # Run tests in different empty directory
    rm -rf empty
    mkdir -p empty
    pushd empty
    if [ $TESTSET == "mini" ]; then
        # Do not exit when tests fail
        set +e
        $PYTEST --ids=$IDSS $PYTEST_FLAGS $COV_FLAGS $JUNIT_FLAGS -m "$PYTEST_MARK" ../imaspy
        set -e
    else
        echo Untested! Dropping shell!
        exit 1
    fi
fi

popd
