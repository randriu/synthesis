#!/bin/bash

# Inspired by build process of spead2

set -e -u

brew install ccache automake boost cln ginac glpk hwloc z3 xerces-c
