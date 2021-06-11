#!/bin/sh
# Test installed package
PYTEST_FLAGS=${PYTEST_FLAG:--n=auto}
COV_FLAGS=${COV_FLAGS:---cov=imaspy --cov-report=term --cov-report=xml:./coverage.xml}
JUNIT_FLAGS=${JUNIT_FLAGS:---junit-xml=./junit.xml}
PYTEST_MARK=${PYTEST_MARK:-}
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
    $PYTEST $PYTEST_FLAGS $COV_FLAGS $JUNIT_FLAGS -m "$PYTEST_MARK" ../imaspy
fi

popd
