#!/bin/bash

set -e

# Helper for travis folding
travis_fold() {
  local action=$1
  local name=$2
  echo -en "travis_fold:${action}:${name}\r"
}

# Helper for building and testing
run() {
  # We start in /opt/prophesy
  cd ..

  travis_fold start virtualenv
  if [[ "$CONFIG" != *Stormpy* ]]
  then
    # Create virtual environment
    virtualenv --python=$PYTHON venv
  fi
  # Activate virtual environment
  source venv/bin/activate
  # Print version
  python --version
  travis_fold end virtualenv

  # Build prophesy
  travis_fold start build_dynasty
  cd dynasty
  python setup.py develop
  travis_fold end build_dynasty

  # Perform task
  if [[ "$TASK" == *Test* ]]
  then
    # Install pytest
    pip install pytest
    # Run tests
    set +e
    python -m pytest dynasty_tests
  fi
}

run