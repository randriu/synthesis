#!/bin/bash

# multi-core compilation
COMPILE_JOBS=$(nproc)
# single-core compilation:
# export COMPILE_JOBS=1

# environment variables
PAYNT_ROOT=`pwd`

# storm-dependencies
sudo apt update
sudo apt -y install build-essential git automake cmake libboost-all-dev libcln-dev libgmp-dev libginac-dev libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev graphviz
sudo apt -y install maven uuid-dev python3-dev libffi-dev libssl-dev python3-pip python3-venv
# apt -y install texlive-latex-extra
# update-alternatives --install /usr/bin/python python /usr/bin/python3 10

# prerequisites
mkdir -p ${PAYNT_ROOT}/prerequisites

# cvc5-build (optional)
# cd ${PAYNT_ROOT}/prerequisites
# git clone --depth 1 --branch cvc5-1.0.0 https://github.com/cvc5/cvc5.git cvc5
# cd ${PAYNT_ROOT}/prerequisites/cvc5
# source ${PAYNT_ROOT}/env/bin/activate
# ./configure.sh --prefix="." --auto-download --python-bindings
# cd build
# make --jobs ${COMPILE_JOBS}
# make install
# deactivate

# storm
cd ${PAYNT_ROOT}/prerequisites
git clone https://github.com/moves-rwth/storm.git storm
# git clone --branch stable https://github.com/moves-rwth/storm.git storm
mkdir -p ${PAYNT_ROOT}/storm/build
cd ${PAYNT_ROOT}/storm/build
cmake ..
make storm-main storm-pomdp --jobs ${COMPILE_JOBS}
# make check --jobs ${COMPILE_JOBS}


# python-environment
python3 -m venv ${PAYNT_ROOT}/env
source ${PAYNT_ROOT}/env/bin/activate
pip3 install pytest pytest-runner pytest-cov numpy scipy toml Cython scikit-build
pip3 install graphviz pysmt z3-solver click

# pycarl-build
cd ${PAYNT_ROOT}/prerequisites
git clone https://github.com/moves-rwth/pycarl.git pycarl
cd ${PAYNT_ROOT}/prerequisites/pycarl
python3 setup.py build_ext --jobs ${COMPILE_JOBS} develop
#[TEST] python3 setup.py test

# stormpy-build
cd ${PAYNT_ROOT}/prerequisites
git clone https://github.com/moves-rwth/stormpy.git stormpy
# git clone --branch stable https://github.com/moves-rwth/stormpy.git stormpy
cd ${PAYNT_ROOT}/prerequisites/stormpy
python3 setup.py build_ext --jobs ${COMPILE_JOBS} develop
# python3 setup.py build_ext --storm-dir ${PAYNT_ROOT}/prerequisites/storm/build --jobs ${COMPILE_JOBS} develop
# python3 setup.py test
deactivate

# done
cd ${PAYNT_ROOT}
