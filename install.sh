#!/bin/bash

set -ex

source storm-alias.sh

export COMPILE_JOBS=$(nproc)
# export COMPILE_JOBS=1 # uncomment this to enable single-core compilation

export SYNTHESIS_TACAS21=false
export SYNTHESIS_INSTALL_DEPENDENCIES=false

synthesis-full
