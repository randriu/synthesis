#!/bin/bash

# multi-core compilation
COMPILE_JOBS=$(nproc)
# single-core compilation:
# export COMPILE_JOBS=1

# environment variables
PAYNT_ROOT=`pwd`
PREREQUISITES=${PAYNT_ROOT}/prerequisites # modify this to install prerequisites outside of Paynt

# storm and stormpy dependencies
sudo apt update -qq
sudo apt install -y build-essential git cmake libboost-all-dev libcln-dev libgmp-dev libginac-dev automake libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev
sudo apt install -y maven uuid-dev python3-dev python3-venv python3-pip

# prerequisites
mkdir -p ${PREREQUISITES}

# build cvc5 (optional)
# cd ${PREREQUISITES}
# git clone --depth 1 --branch cvc5-1.0.0 https://github.com/cvc5/cvc5.git cvc5
# cd ${PREREQUISITES}/cvc5
# source ${PAYNT_ROOT}/env/bin/activate
# ./configure.sh --prefix="." --auto-download --python-bindings
# cd build
# make --jobs ${COMPILE_JOBS}
# make install
# deactivate

# build storm
cd ${PREREQUISITES}
git clone https://github.com/moves-rwth/storm.git storm
# git clone --branch stable https://github.com/moves-rwth/storm.git storm
mkdir -p ${PREREQUISITES}/storm/build
cd ${PREREQUISITES}/storm/build
cmake ..
make storm-main storm-pomdp --jobs ${COMPILE_JOBS}
# make check --jobs ${COMPILE_JOBS}

# setup and activate python environment
python3 -m venv ${PREREQUISITES}/venv
source ${PREREQUISITES}/venv/bin/activate
pip3 install wheel

# build pycarl
cd ${PREREQUISITES}
git clone https://github.com/moves-rwth/pycarl.git pycarl
cd ${PREREQUISITES}/pycarl
python3 setup.py develop
#[TEST] python3 setup.py test

# build stormpy
cd ${PREREQUISITES}
git clone https://github.com/moves-rwth/stormpy.git stormpy
# git clone --branch stable https://github.com/moves-rwth/stormpy.git stormpy
cd ${PREREQUISITES}/stormpy
python3 setup.py develop
# python3 setup.py test

# paynt dependencies
sudo apt -y install graphviz
pip3 install click z3-solver graphviz

# build payntbind
cd ${PAYNT_ROOT}/payntbind
python3 setup.py develop
cd ${PAYNT_ROOT}

# done
deactivate
