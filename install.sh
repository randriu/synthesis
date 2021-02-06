#!/bin/bash

set -ex

TACAS=true
INSTALL_DEPENDENCIES=false

THREADS=$(nproc)
# THREADS=1 # uncomment this to disable multi-core compilation
STORM_VERSION=1.6.3

SYNTHESIS=`pwd`
PREREQUISITES=$SYNTHESIS/prerequisites
DOWNLOADS=$PREREQUISITES/downloads
SYNTHESIS_ENV=$SYNTHESIS/env

#unzip
cd $PREREQUISITES
unzip $DOWNLOADS/carl.zip
mv carl-master14 carl
unzip $DOWNLOADS/pycarl.zip
mv pycarl-master pycarl
cd ..
unzip $DOWNLOADS/storm.zip
mv storm-$STORM_VERSION storm
unzip $DOWNLOADS/stormpy.zip
mv stormpy-$STORM_VERSION stormpy

# patch
rsync -av $SYNTHESIS/patch/ $SYNTHESIS/

# dependencies
if [ "$INSTALL_DEPENDENCIES" = true ]; do
    sudo apt update
    sudo apt -y install build-essential git automake cmake libboost-all-dev libcln-dev libgmp-dev libginac-dev libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev
    sudo apt -y install texlive-latex-extra

    # not installed on sarka (+ means there is an included resourse):
        # carl:
            # libcln-dev (+, requires texinfo)
            # libginac-dev (+)
            # libeigen3-dev (+)
        # storm:
            # libglpk-dev (+)
            # libxerces-c-dev (we probably do not need --gspn)

    sudo apt -y install maven uuid-dev python3-dev libffi-dev libssl-dev python3-pip
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10
fi

# tacas dependencies
if [ "$TACAS" = true ]; do
    cd $PREREQUISITES
    unzip tacas-dependencies.zip
    cd tacas-dependencies
    pip3 install --no-index -f pip-packages -r python-requirements
    sudo dpkg -i apt-packages/*.deb
    sudo apt install -y python3-virtualenv
    cd ../..
fi

# set up python environment
virtualenv -p python3 $SYNTHESIS_ENV
source $SYNTHESIS_ENV/bin/activate
pip3 install pysmt z3-solver click
deactivate

# install prerequisites
cd $PREREQUISITES

# carl
mkdir -p carl/build
cd carl/build
cmake -DUSE_CLN_NUMBERS=ON -DUSE_GINAC=ON -DTHREAD_SAFE=ON ..
make lib_carl --jobs $THREADS
#[TEST] make test
cd ../..

#pycarl
cd pycarl
source $SYNTHESIS_ENV/bin/activate
python3 setup.py build_ext --jobs $THREADS --disable-parser develop
#[TEST] python3 setup.py test
deactivate
cd ..

cd ..

# storm
mkdir -p storm/build
if [ "$TACAS" = true ]; do
    cp $PREREQUISITES/tacas-dependencies/storm_3rdparty_CMakeLists.txt storm/resources/3rdparty/CMakeLists.txt
    mkdir -p storm/build/include/resources/3rdparty/
    cp -r $PREREQUISITES/tacas-dependencies/StormEigen/ storm/build/include/resources/3rdparty/
fi
cd storm/build
cmake ..
make storm-main --jobs $THREADS
#[TEST] make check --jobs $THREADS
cd ../..

# stormpy
cd stormpy
source $SYNTHESIS_ENV/bin/activate
python3 setup.py build_ext --jobs $THREADS develop
#[TEST] python3 setup.py test
deactivate
cd ..

# dynasty
cd dynasty
source $SYNTHESIS_ENV/bin/activate
python3 setup.py install
#[TEST] python3 setup.py test
deactivate
cd ..

# tacas21-install
