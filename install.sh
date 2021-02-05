#!/bin/bash

set -ex

SYNTHESIS_TACAS21=false
SYNTHESIS_INSTALL_DEPENDENCIES=false

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
#[TACAS] cp $DOWNLOADS/storm_3rdparty_CMakeLists.txt storm/resources/3rdparty/CMakeLists.txt
unzip $DOWNLOADS/stormpy.zip
mv stormpy-$STORM_VERSION stormpy
rsync -av $SYNTHESIS/patch/ $SYNTHESIS/

# set up python environment
virtualenv -p python3 $SYNTHESIS_ENV
source $SYNTHESIS_ENV/bin/activate
pip3 install pysmt z3-solver click
deactivate

# install prerequisites (carl, carl-parser)
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
cd storm/build
#[TACAS] mkdir -p include/resources/3rdparty/
#[TACAS] cp -r ../../StormEigen include/resources/3rdparty/
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
