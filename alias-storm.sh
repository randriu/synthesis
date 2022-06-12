#!/bin/bash

# compilation parameters

export COMPILE_JOBS=$(nproc)

# environment variables

export SYNTHESIS=`pwd`
export PREREQUISITES=$SYNTHESIS/prerequisites
export PRE_DOWNLOADS=$PREREQUISITES/downloads
export PRE_TOOLS=$PREREQUISITES/tools


export SYNTHESIS_ENV=$SYNTHESIS/env

export STORM_DIR=$SYNTHESIS/storm
export STORM_BLD=$STORM_DIR/build
export STORM_BLD_DEBUG=$STORM_DIR/build_debug

export STORMPY_BLD=$SYNTHESIS/stormpy/build
export STORMPY_BLD_DEBUG=$SYNTHESIS/stormpy/build_debug

export PAYNT_DIR=$SYNTHESIS/paynt

### prerequisites ##############################################################

prerequisites-download() {
    mkdir -p $PRE_DOWNLOADS
    cd $PRE_DOWNLOADS
    
    git clone -b master14 https://github.com/ths-rwth/carl carl
    zip -r carl.zip carl && rm -rf carl
    git clone https://github.com/moves-rwth/pycarl.git pycarl
    zip -r pycarl.zip pycarl && rm -rf pycarl
    wget https://github.com/cvc5/cvc5/archive/refs/tags/cvc5-0.0.6.zip -O cvc5.zip
    # git clone -b stable https://github.com/moves-rwth/storm.git storm
    # git clone -b stable https://github.com/moves-rwth/stormpy.git stormpy
    
    cd -
}

prerequisites-prepare() {
    mkdir -p $PRE_TOOLS
    cd $PRE_TOOLS
    unzip $PRE_DOWNLOADS/carl.zip
    unzip $PRE_DOWNLOADS/pycarl.zip
    unzip $PRE_DOWNLOADS/cvc5.zip
    mv cvc5-cvc5-0.0.6 cvc5
    cd -
}

storm-dependencies() {
    sudo apt update
    sudo apt -y install build-essential git automake cmake libboost-all-dev libcln-dev libgmp-dev libginac-dev libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev
    sudo apt -y install texlive-latex-extra
    sudo apt -y install maven uuid-dev python3-dev libffi-dev libssl-dev python3-pip
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10
}

alias enva='source $SYNTHESIS_ENV/bin/activate'
alias envd='deactivate'

python-environment() {
    pip3 install virtualenv
    virtualenv -p python3 $SYNTHESIS_ENV
    enva
    pip3 install pytest pytest-runner pytest-cov numpy scipy pysmt z3-solver click
    pip3 install toml # CVC5
    pip3 install Cython scikit-build #Cprofile
    envd
}

prerequisites-build-carl() {
    mkdir -p $PRE_TOOLS/carl/build
    cd $PRE_TOOLS/carl/build
    cmake -DUSE_CLN_NUMBERS=ON -DUSE_GINAC=ON -DTHREAD_SAFE=ON ..
    make lib_carl --jobs $COMPILE_JOBS
    #[TEST] make test
    cd -
}

prerequisites-build-pycarl() {
    cd $PRE_TOOLS/pycarl
    enva
    python3 setup.py build_ext --jobs $COMPILE_JOBS develop
    #[TEST] python3 setup.py test
    envd
    cd -
}

prerequisites-build-cvc5() {
    cd $PRE_TOOLS/cvc5
    enva
    ./configure.sh --prefix="." --auto-download --python-bindings
    cd build
    make --jobs $COMPILE_JOBS
    make install
    envd
    cd -
}

### storm and stormpy ##########################################################

storm-config() {
    mkdir -p $STORM_BLD
    cd $STORM_BLD
    cmake ..
    cd -
}

storm-config-debug() {
    mkdir -p $STORM_BLD_DEBUG
    cd $STORM_BLD_DEBUG
    cmake .. -DSTORM_DEVELOPER=ON -DSTORM_USE_LTO=OFF
    cd -
}

storm-build() {
    cd $STORM_BLD
    make storm-main storm-synthesis --jobs $COMPILE_JOBS
    # make check --jobs $COMPILE_JOBS
    cd -
}

storm-build-debug() {
    cd $STORM_BLD_DEBUG
    make storm-main storm-synthesis --jobs $COMPILE_JOBS
    cd -
}

stormpy-build() {
    cd $SYNTHESIS/stormpy
    enva
    python3 setup.py build_ext --build-temp $STORMPY_BLD --storm-dir $STORM_BLD --jobs $COMPILE_JOBS develop
    # python3 setup.py test
    envd
    cd -
}

stormpy-build-debug() {
    cd $SYNTHESIS/stormpy
    enva
    python3 setup.py build_ext --build-temp $STORMPY_BLD --storm-dir $STORM_BLD_DEBUG --jobs $COMPILE_JOBS develop
    # python3 setup.py test
    envd
    cd -
}

paynt-install() {
    cd $PAYNT_DIR
    enva
    python3 setup.py install
    # python3 setup.py test
    envd
    cd -
}

synthesis-install() {

    # clone repository
    # git clone https://github.com/randriu/synthesis.git
    git clone git@github.com:randriu/synthesis.git
    cd synthesis
    
    # load aliases
    source workspace/storm-alias.sh
    
    # install dependencies
    storm-dependencies
    # setup python environment
    python-environment

    # unzip prerequisites
    prerequisites-prepare
    # build carl
    prerequisites-build-carl
    # build pycarl
    prerequisites-build-pycarl
    # build cvc5 (optional)
    prerequisites-build-cvc5

    # configure storm
    storm-config
    # build storm
    storm-build
    # build stomrpy
    stormpy-build
    # install paynt
    paynt-install

    # check
    # TODO
}

