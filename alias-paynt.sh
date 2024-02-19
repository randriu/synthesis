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
python3 paynt.py --project models/cassandra/decpomdp/ --sketch 2generals.dpomdp --pomdp-memory-size 2
)'

alias runb='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/decpomdp/ --sketch basic.dpomdp --pomdp-memory-size 2
)'

alias rund='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/decpomdp/ --sketch dectiger.dpomdp --profiling --pomdp-memory-size 2
)'
alias rung='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/decpomdp/ --sketch gridsmall.dpomdp --pomdp-memory-size 2
)'

alias run43='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/decpomdp/ --sketch 4x3.95.dpomdp --pomdp-memory-size 2
)'


alias runt95='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/decpomdp/ --sketch tiger.95.dpomdp --pomdp-memory-size 1
)'
alias runt951='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/decpomdp/ --sketch tiger1.95.dpomdp --pomdp-memory-size 1
)'
alias runt95p='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/pomdp/ --sketch tiger.95.pomdp --pomdp-memory-size 1
)'

alias runparr='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/decpomdp/ --sketch parr95.95.dpomdp --pomdp-memory-size 1
)'

alias runparrp='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/pomdp/ --sketch parr95.95.pomdp --pomdp-memory-size 1
)'
alias runpomdp='(
source prerequisites/venv/bin/activate
python3 paynt.py --project models/cassandra/pomdp/ --sketch 4x3.95.pomdp
)'

