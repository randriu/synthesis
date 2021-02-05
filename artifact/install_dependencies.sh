#!/bin/bash
set -e
set -x

cd dependencies
PIP_PACK=pip-packages

pip3 install --no-index -f $PIP_PACK -r python-requirements

dpkg -i apt-packages/*.deb
bash install_carl.sh

STORM_VERSION=1.6.3
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
sudo python setup.py build_ext --carl-dir $DEP_DIR/carl/build --jobs $THREADS --disable-parser develop
cd ..

# storm
unzip storm.zip
mv storm-$STORM_VERSION storm
cp storm_3rdparty_CMakeLists.txt storm/resources/3rdparty/CMakeLists.txt
mkdir -p storm/build
cd storm/build
mkdir -p include/resources/3rdparty/
cp -r ../../StormEigen include/resources/3rdparty/
cmake ..
make storm-main --jobs $THREADS
cd ../../

# stormpy
unzip stormpy.zip
mv stormpy-$STORM_VERSION stormpy
cd stormpy
sudo pip3 install -ve .
cd ..

cd ..

# dynasty


