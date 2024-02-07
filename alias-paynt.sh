#!/bin/bash
# usage: source alias-storm.sh

# compilation parameters


export SYNTHESIS=`pwd`
export PREREQUISITES=$SYNTHESIS/prerequisites
export SYNTHESIS_ENV=$SYNTHESIS/env

export STORM_BLD=$SYNTHESIS/storm/build
export STORM_BLD_DEBUG=$SYNTHESIS/storm/build_debug

export STORMPY_BLD=$SYNTHESIS/stormpy/build

# environment aliases

alias enva='source prerequisites/venv/bin/activate'
alias envd='deactivate'

alias buildp='(
source prerequisites/venv/bin/activate
cd payntbind
python3 setup.py develop
cd ..
)'

alias runp='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/decpomdp/ --sketch 2generals.dpomdp 
)'

alias runb='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/decpomdp/ --sketch basic.dpomdp
)'

alias rund='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/decpomdp/ --sketch dectiger.dpomdp
)'
alias runpomdp='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/pomdp/ --sketch 4x3.95.pomdp
)'

