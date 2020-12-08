#!/bin/bash

# general

alias dot_clean='find ~ -name "._*" -delete; find . -name ".DS_Store" -delete'

# environment variables

export SYNTHESIS=`pwd`
export PREREQUISITES=$SYNTHESIS/prerequisites
export SYNTHESIS_ENV=$SYNTHESIS/env

export STORM_DIR=$SYNTHESIS/storm
export STORM_SRC=$STORM_DIR/src
export STORM_BLD=$STORM_DIR/build

export STORMPY_DIR=$SYNTHESIS/stormpy
export DYNASTY_DIR=$SYNTHESIS/dynasty

# building
export COMPILE_JOBS='8'

# functions

storm-dependencies() {
    sudo apt update
    sudo apt -y install git cmake automake libboost-all-dev libcln-dev libgmp-dev libginac-dev libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev

    sudo apt -y install maven uuid-dev python3-dev libffi-dev libssl-dev python3-pip
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10
}

storm-download() {
    mkdir -p $PREREQUISITES

    # mathsat
    # cd $PREREQUISITES
    # wget -O mathsat.tar.gz http://mathsat.fbk.eu/download.php?file=mathsat-5.5.4-linux-x86_64.tar.gz
    # tar -xf mathsat.tar.gz && rm mathsat.tar.gz && mv mathsat-5.5.4-linux-x86_64 mathsat
    # cd $OLDPWD
    # created folder: $PREREQUISITES/mathsat

    # carl
    cd $PREREQUISITES
    git clone -b master14 https://github.com/smtrat/carl
    cd $OLDPWD
    # created folder: $PREREQUISITES/carl

    # pycarl
    cd $PREREQUISITES
    git clone https://github.com/moves-rwth/pycarl.git
    cd $OLDPWD
    # created folder: $PREREQUISITES/pycarl

    # storm
    wget https://zenodo.org/record/3885454/files/moves-rwth/storm-1.6.0.zip
    unzip storm-1.6.0.zip && rm storm-1.6.0.zip
    # created folder: moves-rwth-storm-058fed3

    # stormpy
    wget https://github.com/moves-rwth/stormpy/archive/1.6.0.zip
    unzip 1.6.0.zip && rm 1.6.0.zip
    # created folder: stormpy-1.6.0
}

storm-patch() {
    rsync -av storm/ moves-rwth-storm-058fed3/ && rm -rf storm && mv moves-rwth-storm-058fed3 storm
    rsync -av stormpy/ stormpy-1.6.0/ && rm -rf stormpy && mv stormpy-1.6.0 stormpy
}

storm-setup-python() {
    pip3 install virtualenv
    virtualenv -p python3 $SYNTHESIS_ENV
}

build-carl() {
    cd $PREREQUISITES
    cd carl && mkdir -p build && cd build
    cmake -DUSE_CLN_NUMBERS=ON -DUSE_GINAC=ON -DTHREAD_SAFE=ON ..
    make --jobs $COMPILE_JOBS
    make lib_carl
}

# build-carl-parser() {
#     cd $PREREQUISITES
#     cd carl-parser && mkdir -p build && cd build
#     cmake ..
#     sed -i ' 1 s/$/ -lgmp -lcln -lginac/' test/CMakeFiles/carl-parser-test.dir/link.txt
#     make --jobs $COMPILE_JOBS

# }

build-pycarl() {
    cd $PREREQUISITES/pycarl
    source $SYNTHESIS_ENV/bin/activate
    python3 setup.py build_ext --carl-dir $PREREQUISITES/carl --jobs $COMPILE_JOBS develop
    deactivate
}

storm-config() {
    dot_clean
    mkdir $STORM_BLD
    cd $STORM_BLD
    cmake ..
    cd $OLDPWD
}

storm-build() {
    dot_clean
    cd $STORM_BLD
    make storm-main --jobs $COMPILE_JOBS
    cd $OLDPWD
}

stormpy-build() {
    dot_clean
    cd $STORMPY_DIR
    source $SYNTHESIS_ENV/bin/activate
    python3 setup.py build_ext --storm-dir $STORM_BLD --jobs $COMPILE_JOBS develop
    deactivate
    cd $OLDPWD
}

install-dynasty() {
    dot_clean
    cd $DYNASTY_DIR
    source $SYNTHESIS_ENV/bin/activate
    python3 setup.py install
    deactivate
    cd $OLDPWD
}