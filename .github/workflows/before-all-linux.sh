#!/bin/bash

# Inspired by build process of spead2

set -e -u

dnf install -y boost-devel cln-devel gmp-devel glpk-devel hwloc-devel z3-devel xerces-c-devel eigen3-devel python3-devel # missing ginac

cd /tmp

# Install Python 3.10 from source
PYTHON_VERSION=3.10.18
NR_JOBS=$(nproc)

curl -fsSLO https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz
tar -xzf Python-${PYTHON_VERSION}.tgz
cd Python-${PYTHON_VERSION}

# Install build dependencies
dnf install -y gcc make openssl-devel bzip2-devel libffi-devel zlib-devel readline-devel sqlite-devel tk-devel xz-devel

./configure --enable-optimizations --with-ensurepip=install
make -j ${NR_JOBS}
make altinstall

cd ..

# Install python3.10-devel and python3.10-venv
PYTHON3_10_BIN=/usr/local/bin/python3.10

${PYTHON3_10_BIN} -m ensurepip
${PYTHON3_10_BIN} -m pip install --upgrade pip

# python3.10-devel is provided by headers and config files installed by make altinstall

# Install ginac
curl -fsSLO https://www.ginac.de/ginac-${ginac_version}.tar.bz2
tar -jxf ginac-${ginac_version}.tar.bz2
cd ginac-${ginac_version}
./configure CXXFLAGS="-O2"
make -j ${NR_JOBS}
make install
cd ..

# Install Storm
# git clone https://github.com/moves-rwth/storm.git -b ${STORM_VERSION}
# cd storm
# mkdir build
# cd build
# cmake .. -DSTORM_BUILD_TESTS=OFF -DSTORM_BUILD_EXECUTABLES=OFF -DSTORM_PORTABLE=ON
# make -j ${NR_JOBS}
# make install
# cd ..
# rm -rf build
