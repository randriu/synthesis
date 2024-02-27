#!/bin/bash

cd prerequisites/storm/build
make storm-main storm-pomdp --jobs 2

cd ../../stormpy
python3 setup.py build_ext --storm-dir /home/fpmk/synthesis-playground/prerequisites/storm/build --jobs 2 develop

cd ../../payntbind
python3 setup.py build_ext --storm-dir /home/fpmk/synthesis-playground/prerequisites/storm/build --jobs 2 develop

cd ..