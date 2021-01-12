#!/bin/bash

set -ex

source storm-alias.sh

# export COMPILE_JOBS=1 # uncomment this to disable multi-core compilation

# tacas21-install

export SYNTHESIS_TACAS21=false
export SYNTHESIS_INSTALL_DEPENDENCIES=false
synthesis-full
