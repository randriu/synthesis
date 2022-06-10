#!/bin/bash

# download prerequisites
# git clone -b master14 https://github.com/smtrat/carl
# git clone https://github.com/moves-rwth/pycarl.git
# wget https://github.com/moves-rwth/storm/archive/1.6.4.zip
# wget https://github.com/moves-rwth/stormpy/archive/1.6.4.zip

set -ex

INSTALL_DEPENDENCIES=true

if [ "$INSTALL_DEPENDENCIES" = true ]; then
    if [[ ! $(sudo echo 0) ]]; then echo "sudo authentication failed"; exit; fi
fi

THREADS=$(nproc)
# THREADS=1 # uncomment this to disable multi-core compilation

SYNTHESIS=`pwd`
PREREQUISITES=$SYNTHESIS/prerequisites
DOWNLOADS=$PREREQUISITES/downloads
TACAS_DEPENDENCIES=$PREREQUISITES/tacas-dependencies
SYNTHESIS_ENV=$SYNTHESIS/env

# unzip downloaded prerequisites
cd $PREREQUISITES
unzip $DOWNLOADS/carl.zip
mv carl-master14 carl
unzip $DOWNLOADS/pycarl.zip
mv pycarl-master pycarl
cd $SYNTHESIS

# dependencies
if [ "$INSTALL_DEPENDENCIES" = true ]; then
    # not installed on sarka (+ means there is an included resourse):
        # carl:
            # libcln-dev (+, requires texinfo)
            # libginac-dev (+)
            # libeigen3-dev (+)
        # storm:
            # libglpk-dev (+)
            # libxerces-c-dev (we probably do not need --gspn)

    sudo apt update
    sudo apt -y install build-essential git automake cmake libboost-all-dev libcln-dev libgmp-dev libginac-dev libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev
    sudo apt -y install texlive-latex-extra
    sudo apt -y install maven uuid-dev python3-dev libffi-dev libssl-dev python3-pip virtualenv
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10
fi


# set up python environment
virtualenv -p python3 $SYNTHESIS_ENV
source $SYNTHESIS_ENV/bin/activate
pip3 install pytest pytest-runner pytest-cov numpy scipy pysmt z3-solver click
pip3 install Cython scikit-build
deactivate

# build carl
mkdir -p $PREREQUISITES/carl/build
cd $PREREQUISITES/carl/build
cmake -DUSE_CLN_NUMBERS=ON -DUSE_GINAC=ON -DTHREAD_SAFE=ON ..
make lib_carl --jobs $THREADS
#[TEST] make test
cd -

# build pycarl
cd $PREREQUISITES/pycarl
enva
python3 setup.py build_ext --jobs $COMPILE_JOBS develop
#[TEST] python3 setup.py test
envd
cd -

# build cvc5 (optional)
cd $PREREQUISITES/cvc5
enva
./configure.sh --prefix="." --auto-download --python-bindings
cd build
make --jobs $COMPILE_JOBS
make install
envd
cd $SYNTHESIS

# build storm
mkdir -p $SYNTHESIS/storm/build
cd $SYNTHESIS/storm/build
cmake ..
make storm-main storm-synthesis --jobs $THREADS
#[TEST] make check --jobs $THREADS
cd -

# build stormpy
cd $SYNTHESIS/stormpy
source $SYNTHESIS_ENV/bin/activate
python3 setup.py build_ext --jobs $THREADS develop
#[TEST] python3 setup.py test
deactivate
cd -

# setup paynt
cd $SYNTHESIS/paynt
source $SYNTHESIS_ENV/bin/activate
python3 setup.py install
#[TEST] python3 setup.py test
deactivate
cd -

# test
# source env/bin/activate
# python3 paynt/paynt.py --project tacas21-benchmark/grid --properties easy.properties hybrid
