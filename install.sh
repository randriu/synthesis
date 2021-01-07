#!/bin/bash

set -ex

source storm-alias.sh

# export COMPILE_JOBS=1 # uncomment this to disable multi-core compilation

export SYNTHESIS_INSTALL_DEPENDENCIES=false
export SYNTHESIS_TACAS21=true

synthesis-full
