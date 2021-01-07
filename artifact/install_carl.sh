#!/bin/bash
set -e
set -x

THREADS=$(nproc)
DEP_DIR=$PWD

# carl
unzip carl.zip
mv carl-master14 carl
mkdir -p carl/build
cd carl/build
cmake -DUSE_CLN_NUMBERS=ON -DUSE_GINAC=ON -DTHREAD_SAFE=ON ..
make lib_carl -j$THREADS
cd ../../

# pycarl
unzip pycarl.zip
mv pycarl-master pycarl
cd pycarl
sudo python setup.py build_ext --carl-dir $DEP_DIR/carl/build --jobs $COMPILE_JOBS develop --disable-parser develop
cd ..
