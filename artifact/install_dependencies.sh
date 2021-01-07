#!/bin/bash
set -e
set -x


cd dependencies
PIP_PACK=pip-packages

pip3 install --no-index -f $PIP_PACK -r python-requirements

dpkg -i apt-packages/*.deb
./install_carl.sh
./install_storm.sh
cd -
