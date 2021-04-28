#!/bin/bash

# cd synthesis/prerequisites/tacas-dependencies
# bash create-artifact.sh

if [[ ! $(sudo echo 0) ]]; then echo "sudo authentication failed"; exit; fi

# download apt-packages
mkdir -p apt-packages
sudo apt-get update
sudo apt-get install --print-uris libgmp-dev libglpk-dev libhwloc-dev z3 libboost-all-dev libeigen3-dev libginac-dev libpython3-dev automake python3-virtualenv | grep -oP "(?<=').*(?=')" > packages.uri
cd apt-packages
wget -i ../packages.uri
cd ..

# download pip packages
pip3 download -d pip-packages -r python-requirements

# clean git and zip everything
cd ../..
rm -rf .git
cd ..
zip -r synthesis.zip synthesis
