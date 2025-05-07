#!/bin/bash

# multi-core compilation
COMPILE_JOBS=$(nproc)
# single-core compilation:
# export COMPILE_JOBS=1

# environment variables
PAYNT_ROOT=`pwd`
PREREQUISITES=${PAYNT_ROOT}/prerequisites

# storm and stormpy dependencies
sudo apt update -qq
sudo apt install -y build-essential git cmake libboost-all-dev libcln-dev libgmp-dev libginac-dev automake libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev
sudo apt install -y maven uuid-dev python3-dev python3-venv python3-pip

# prerequisites
mkdir -p ${PREREQUISITES}

# build storm
cd ${PREREQUISITES}
git clone https://github.com/moves-rwth/storm.git storm -b 1.9.0
mkdir -p ${PREREQUISITES}/storm/build
cd ${PREREQUISITES}/storm/build
cmake ..
make --jobs ${COMPILE_JOBS}

export STORM_DIR=${PREREQUISITES}/storm
export PATH=$PATH:$STORM_DIR/build/bin

# setup and activate python environment
python3 -m venv ${PREREQUISITES}/venv
source ${PREREQUISITES}/venv/bin/activate
pip3 install wheel

# build carl
cd ${PREREQUISITES}
git clone https://github.com/moves-rwth/carl-storm carl
mkdir -p ${PREREQUISITES}/carl/build
cd ${PREREQUISITES}/carl/build
cmake ..
make lib_carl

# build pycarl
cd ${PREREQUISITES}
git clone https://github.com/moves-rwth/pycarl.git pycarl -b 2.3.0
cd ${PREREQUISITES}/pycarl
python3 setup.py develop

# build stormpy
cd ${PREREQUISITES}
git clone https://github.com/moves-rwth/stormpy.git stormpy -b 1.9.0
cd ${PREREQUISITES}/stormpy
python3 setup.py develop

# build dtcontrol
cd ${PREREQUISITES}
git clone https://gitlab.com/live-lab/software/dtcontrol.git dtcontrol -b paynt-colab
cd ${PREREQUISITES}/dtcontrol
pip install .

# paynt dependencies
sudo apt -y install graphviz
pip3 install click z3-solver psutil graphviz

# build payntbind
cd ${PAYNT_ROOT}/payntbind
python3 setup.py develop
cd ${PAYNT_ROOT}

# done
deactivate
