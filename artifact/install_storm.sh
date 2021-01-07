#!/bin/bash
set -e
set -x

STORM_VERSION=1.6.3
THREADS=$(nproc)

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
