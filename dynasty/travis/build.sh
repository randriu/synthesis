#!/bin/bash -x

# Helper for travis folding
travis_fold() {
  local action=$1
  local name=$2
  echo -en "travis_fold:${action}:${name}\r"
}

N_JOBS=2

OS=$TRAVIS_OS_NAME

case $OS in
linux)
    # Execute docker image on Linux
    # Stop previous session
    docker rm -f dynasty &>/dev/null
    # Run container
    set -e
    docker run -d -it --name dynasty --privileged movesrwth/$DOCKER
    # Copy local content into container
    docker exec dynasty mkdir /opt/dynasty
    docker cp . dynasty:/opt/dynasty

    # Install missing dependencies
    travis_fold start install_dependencies
    docker exec dynasty apt-get update
    docker exec dynasty apt-get install -qq -y z3
    if [[ "$CONFIG" != *Stormpy* ]]
    then
        # Virtual environment not yet present
        docker exec dynasty apt-get install -qq -y python python3 virtualenv
    fi
    travis_fold end install_dependencies
    set +e

    # Execute main process
    docker exec dynasty bash -c "
        export N_JOBS=$N_JOBS;
        export OS=$OS;
        export PYTHON=$PYTHON;
        export CONFIG=$CONFIG;
        export TASK=$TASK;
        export LANG=C.UTF-8;
        cd /opt/dynasty;
        travis/build-helper.sh"
    exit $?
    ;;

osx)
    echo "MacOS currently unsupported"
    exit 1
    ;;

*)
    # Other OS
    echo "Unsupported OS: $OS"
    exit 1
esac