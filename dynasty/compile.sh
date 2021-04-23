#!/bin/bash

cd ../storm/build
make storm-main storm-pars --jobs 8
cd ../../stormpy
python3 setup.py develop
cd ../dynasty
