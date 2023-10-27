#!/bin/bash
# usage: source alias-storm.sh

# multi-core compilation
export COMPILE_JOBS=$(nproc)
# single-core compilation:
# export COMPILE_JOBS=1

# environment variables
export PROJECT_ROOT=`pwd`

# environment aliases
alias enva='source $PROJECT_ROOT/env/bin/activate'
alias envd='deactivate'


storm-dependencies() {
    sudo apt update
    sudo apt -y install build-essential git automake cmake libboost-all-dev libcln-dev libgmp-dev libginac-dev libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev
    sudo apt -y install maven uuid-dev python3-dev libffi-dev libssl-dev python3-pip python3-venv
    # apt -y install texlive-latex-extra
    # update-alternatives --install /usr/bin/python python /usr/bin/python3 10
}

download-prerequisites() {
    mkdir -p $PROJECT_ROOT/prerequisites
    cd $PROJECT_ROOT/prerequisites
    git clone --depth 1 https://github.com/moves-rwth/pycarl.git pycarl
    git clone --depth 1 --branch cvc5-1.0.0 https://github.com/cvc5/cvc5.git cvc5
    cd -
    cd $PROJECT_ROOT
    git clone https://github.com/moves-rwth/storm.git storm
    # git clone --branch stable https://github.com/moves-rwth/storm.git storm
    git clone --branch synthesis git@github.com:randriu/stormpy.git stormpy
    cd -
}

python-environment() {
    python3 -m venv $PROJECT_ROOT/env
    enva
    pip3 install pytest pytest-runner pytest-cov numpy scipy pysmt z3-solver click
    pip3 install toml
    pip3 install Cython scikit-build
    envd
}

pycarl-build() {
    cd $PROJECT_ROOT/prerequisites/pycarl
    enva
    python3 setup.py build_ext --jobs $COMPILE_JOBS develop
    #[TEST] python3 setup.py test
    envd
    cd -
}

cvc5-build() {
    cd $PROJECT_ROOT/prerequisites/cvc5
    enva
    ./configure.sh --prefix="." --auto-download --python-bindings
    cd build
    make --jobs $COMPILE_JOBS
    make install
    envd
    cd -
}

storm-build() {
    mkdir -p $PROJECT_ROOT/storm/build
    cd $PROJECT_ROOT/storm/build
    cmake ..
    make storm-main storm-pomdp --jobs $COMPILE_JOBS
    # make check --jobs $COMPILE_JOBS
    cd -
}

stormpy-build() {
    cd $PROJECT_ROOT/stormpy
    enva
    python3 setup.py build_ext --jobs $COMPILE_JOBS develop
    # python3 setup.py build_ext --storm-dir $PROJECT_ROOT/storm/build --jobs $COMPILE_JOBS develop
    # python3 setup.py test
    envd
    cd -
}

synthesis-install() {
    storm-dependencies
    download-prerequisites
    python-environment
    
    # building cvc5 is optional
    # cvc5-build

    # optional unless you don't have Storm installed
    # storm-build
    
    pycarl-build
    stormpy-build
}
