#!/bin/bash

set -x

source storm-alias.sh

export COMPILE_JOBS=8

export SYNTHESIS_TACAS21=false
export SYNTHESIS_INSTALL_DEPENDENCIES=false

synthesis-full
