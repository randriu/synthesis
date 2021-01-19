#!/bin/bash

# merlin:
# wget https://www.stud.fit.vutbr.cz/~xandri03/synthesis.zip
# git:
# https://github.com/gargantophob/synthesis/archive/master.zip
# zenodo 0.1:
# wget https://zenodo.org/record/4422544/files/synthesis.zip
# zenodo 0.11: https://zenodo.org/record/4425438
# wget https://zenodo.org/record/4425438/files/synthesis.zip
# zenodo 0.12: TODO

# compilation parameters

export COMPILE_JOBS=$(nproc)
export SYNTHESIS_TACAS21=true
export SYNTHESIS_INSTALL_DEPENDENCIES=false

# environment variables

export SYNTHESIS=`pwd`
export PREREQUISITES=$SYNTHESIS/prerequisites
export SYNTHESIS_ENV=$SYNTHESIS/env

export STORM_DIR=$SYNTHESIS/storm
export STORM_SRC=$STORM_DIR/src
export STORM_BLD=$STORM_DIR/build

export STORMPY_DIR=$SYNTHESIS/stormpy
export DYNASTY_DIR=$SYNTHESIS/dynasty

export DICE=$DYNASTY_DIR/workspace/examples/msp/dice

### TACAS 2021 #################################################################

tacas21-download-dependencies() {
    cd artifact

    ROOT_DIR=$PWD
    ART_DIR=$ROOT_DIR/dependencies
    DEP_DIR=$ART_DIR/dependencies
    PACK_DIR=$DEP_DIR/apt-packages
    PIP_DIR=$DEP_DIR/pip-packages
    STORM_VERSION=1.6.3

    # download apt-packages
    PACK_URIS=$DEP_DIR/packages.uri
    mkdir -p $PACK_DIR
    sudo apt-get update
    apt-get install --print-uris libgmp-dev libglpk-dev libhwloc-dev z3 libboost-all-dev libeigen3-dev libginac-dev libpython3-dev automake | grep -oP "(?<=').*(?=')" > $PACK_URIS
    cd $PACK_DIR
    wget -i $PACK_URIS
    cd $ROOT_DIR

    # download pip packages
    pip3 download -d $PIP_DIR -r python-requirements

    # download carl & storm
    wget -O $DEP_DIR/carl.zip https://github.com/smtrat/carl/archive/master14.zip
    wget -O $DEP_DIR/pycarl.zip https://github.com/moves-rwth/pycarl/archive/master.zip
    wget -O $DEP_DIR/storm.zip https://github.com/moves-rwth/storm/archive/$STORM_VERSION.zip
    wget -O $DEP_DIR/stormpy.zip https://github.com/moves-rwth/stormpy/archive/$STORM_VERSION.zip

    # copy storm adjustments
    cp -r storm_3rdparty_CMakeLists.txt StormEigen $DEP_DIR

    # copy installation scripts
    cp install_carl.sh install_storm.sh python-requirements $DEP_DIR
    cp install_dependencies.sh $ART_DIR

    # zip everything
    zip -r ../dependencies.zip dependencies/*
    rm -rf dependencies
    cd ..
}

tacas21-prepare-artifact() {
    sudo apt install -y git
    git clone https://github.com/gargantophob/synthesis.git
    cd synthesis
    source storm-alias.sh
    tacas21-download-dependencies
    cd ..
    zip -r synthesis.zip synthesis
}

tacas21-install() {
    # install dependencies
    unzip dependencies.zip
    cd dependencies
    sudo ./install_dependencies.sh
    cd ..
    # apply patch and recompile
    sudo rsync -av patch/ dependencies/dependencies
    cd dependencies/dependencies/storm/build
    sudo cmake ..
    sudo make storm-main --jobs $COMPILE_JOBS
    cd -
    cd dependencies/dependencies/stormpy
    sudo pip3 install -ve .
    cd -
    # install dynasty
    cd dynasty
    python3 setup.py install
    cd -
}

### dependencies ###############################################################

dynasty-download() {
    local target_dir=$1
    mkdir -p ${target_dir}/prerequisites

    # mathsat
    # cd $PREREQUISITES
    # wget -O mathsat.tar.gz http://mathsat.fbk.eu/download.php?file=mathsat-5.5.4-linux-x86_64.tar.gz
    # tar -xf mathsat.tar.gz && rm mathsat.tar.gz && mv mathsat-5.5.4-linux-x86_64 mathsat
    # cd $OLDPWD
    # created folder: $PREREQUISITES/mathsat

    # carl
    cd ${target_dir}/prerequisites
    git clone -b master14 https://github.com/smtrat/carl
    cd -
    # created folder: prerequisites/carl

    # pycarl
    cd ${target_dir}/prerequisites
    git clone https://github.com/moves-rwth/pycarl.git
    cd -
    # created folder: prerequisites/pycarl

    # storm
    cd $target_dir
    wget https://zenodo.org/record/4288652/files/moves-rwth/storm-1.6.3.zip
    unzip storm-1.6.3.zip && rm storm-1.6.3.zip
    mv moves-rwth-storm-e763b83 storm
    cd -
    # created folder: storm

    # stormpy
    cd $target_dir
    wget https://github.com/moves-rwth/stormpy/archive/1.6.3.zip
    unzip 1.6.3.zip && rm 1.6.3.zip
    mv stormpy-1.6.3 stormpy
    cd -
    # created folder: stormpy
}

dynasty-dependencies() {
    sudo apt update
    sudo apt -y install build-essential git automake cmake libboost-all-dev libcln-dev libgmp-dev libginac-dev libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev
    sudo apt -y install texlive-latex-extra


    # not installed on sarka:
        # carl:
            # libcln-dev (+, requires texinfo)
            # libginac-dev (+)
            # libeigen3-dev (+)
        # storm:
            # libglpk-dev (+)
            # libxerces-c-dev (we probably do not need --gspn)

    sudo apt -y install maven uuid-dev python3-dev libffi-dev libssl-dev python3-pip
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10
}

synthesis-dependencies() {
    
    if [ "$SYNTHESIS_TACAS21" == "true" ]; then
        unzip dependencies.zip
        cp -r dependencies/prerequisites dependencies/storm dependencies/stormpy .
        cd dependencies/dependencies
        sudo dpkg -i apt-packages/*.deb
        pip3 install --no-index -f pip-packages -r python-requirements
        sudo echo "export PATH=$PATH:$HOME/.local/bin" >> $HOME/.profile
        source $HOME/.profile

        virtualenv -p python3 $SYNTHESIS_ENV
        source $SYNTHESIS_ENV/bin/activate
        pip3 install --no-index -f pip-packages -r python-requirements
        deactivate
        cd -
    else
        if [ "$SYNTHESIS_INSTALL_DEPENDENCIES" == "true" ]; then
            dynasty-dependencies
        fi
        dynasty-download $SYNTHESIS
        pip3 install virtualenv

        virtualenv -p python3 $SYNTHESIS_ENV
        source $SYNTHESIS_ENV/bin/activate
        pip3 install pysmt z3-solver click
        deactivate
    fi
    
}

### storm patch ################################################################

dynasty-patch-create() {
    echo "NOT IMPLEMENTED YET"
}

dynasty-patch() {
    rsync -av $SYNTHESIS/patch/ $SYNTHESIS/
}

### preparing prerequisites ####################################################

carl-build() {
    mkdir -p $PREREQUISITES/carl/build
    cd $PREREQUISITES/carl/build
    cmake -DUSE_CLN_NUMBERS=ON -DUSE_GINAC=ON -DTHREAD_SAFE=ON ..
    make lib_carl --jobs $COMPILE_JOBS
    # make test
    cd $OLDPWD
}

# build-carl-parser() {
#     cd $PREREQUISITES
#     cd carl-parser && mkdir -p build && cd build
#     cmake ..
#     sed -i ' 1 s/$/ -lgmp -lcln -lginac/' test/CMakeFiles/carl-parser-test.dir/link.txt
#     make --jobs $COMPILE_JOBS
# }

pycarl-build() {
    cd $PREREQUISITES/pycarl
    source $SYNTHESIS_ENV/bin/activate
    python3 setup.py build_ext --carl-dir $PREREQUISITES/carl/build --jobs $COMPILE_JOBS develop
    # python setup.py test
    deactivate
    cd $OLDPWD
}

### storm and stormpy ##########################################################

storm-config() {
    mkdir -p $STORM_BLD
    cd $STORM_BLD
    # cmake -DSTORM_USE_LTO=OFF ..
    # cmake --DSTORM_PORTABLE=ON ..
    cmake ..
    cd $OLDPWD
}

storm-build() {
    cd $STORM_BLD
    make storm-main --jobs $COMPILE_JOBS
    # make check --jobs $COMPILE_JOBS
    cd $OLDPWD
}

stormpy-build() {
    cd $STORMPY_DIR
    source $SYNTHESIS_ENV/bin/activate
    python3 setup.py build_ext --storm-dir $STORM_BLD --jobs $COMPILE_JOBS develop
    # python setup.py test
    deactivate
    cd $OLDPWD
}

dynasty-install() {
    cd $DYNASTY_DIR
    source $SYNTHESIS_ENV/bin/activate
    python3 setup.py install
    # python setup.py test
    deactivate
    cd $OLDPWD
}

# aggregated functions

synthesis-install() {
    carl-build
    pycarl-build

    dynasty-patch
    storm-config
    storm-build
    stormpy-build

    dynasty-install
}

synthesis-full() {
    synthesis-dependencies
    synthesis-install
}

### development ################################################################

#recompilation

storm-rebuild() {
    storm-config
    storm-build
}

stormpy-rebuild() {
    storm-rebuild
    stormpy-build
}

# aliases

alias sc='storm-config'
alias sb='storm-build'
alias pb='stormpy-build'
alias sr='storm-rebuild'

alias synthesis='cd $SYNTHESIS'
alias dynasty='cd $SYNTHESIS/dynasty'

alias enva='source $SYNTHESIS_ENV/bin/activate'
alias envd='deactivate'

alias tb='dynasty; enva; subl $SYNTHESIS/dynasty/dynasty/family_checkers/integrated_checker.py; subl $SYNTHESIS/dynasty/execute.sh'
alias tf='envd'

# execution

dynrun() {
    dynasty
    enva
    make c$1 & disown
    envd
    cd $OLDPWD
}

alias dpid='pgrep -f "^python dynasty.py .*"'
alias dtime='ps -aux | grep "python dynasty.py"'
alias dshow='pgrep -af "^python dynasty.py .*"'
alias dcount='pgrep -afc "^python dynasty.py .*"'
alias dkill='dpid | xargs kill'


dlog() {
    cat $SYNTHESIS/dynasty/workspace/log/log_$1.txt
}

dhead() {
    dlog $1 | head -n 20
}
dtail() {
    dlog $1 | tail -n 20
}

dgrep() {
    cat $SYNTHESIS/dynasty/workspace/log/log_grep_$1.txt
}

diter() {
    dlog $1 | grep "iteration " | tail -n 1
}

diteri() {
    dlog $1 | grep "CEGIS: iteration " | tail -n 1
}

ditera() {
    dlog $1 | grep "CEGAR: iteration " | tail -n 1
}

dfamily() {
    dlog $1 | grep "family size" | tail -n 1
}
ddtmc() {
    dlog $1 | grep "Constructed DTMC"
}

dopt() {
    dlog $1 | grep "Optimal value" | tail -n 1
}

dbounds() {
    dlog $1 | grep "Result for initial"
}

dperf() {
     dlog $1 | grep "Performance" | tail -n 1
}

dhole() {
    dlog $1 | grep "hole assignment:" | awk '{print $3}'
}

### tmp ################################################################

export DPM=$DYNASTY_DIR/workspace/examples/msp/dpm
export DICE=$DYNASTY_DIR/workspace/examples/msp/dice

storm() {
    cd $STORM_BLD/bin
    local cmd="./storm --explchecks --build-overlapping-guards-label $1 --prop $2 --constants $3"
    eval $cmd
    cd -
}
dice() {
    storm "--prism $DICE/sketch.templ" $DICE/compute.properties "CMAX=0,THRESHOLD=0,$1"
}
dpm() {
    storm "--prism $DPM/sketch.templ" $DPM/compute.properties "CMAX=10,THRESHOLD=0,T2=5,$1"
}
dpmread() {
    local hole=`dhole $1`
    dpm $hole
}

