#!/bin/bash

# compilation parameters

export COMPILE_JOBS='8'

# general

alias dot_clean='find ~ -name "._*" -delete; find . -name ".DS_Store" -delete'

# environment variables

export SYNTHESIS=`pwd`
export PREREQUISITES=$SYNTHESIS/prerequisites
export SYNTHESIS_ENV=$SYNTHESIS/env

export STORM_DIR=$SYNTHESIS/storm
export STORM_SRC=$STORM_DIR/src
export STORM_BLD=$STORM_DIR/build

export STORMPY_DIR=$SYNTHESIS/stormpy
export DYNASTY_DIR=$SYNTHESIS/dynasty

# functions

dynasty-dependencies() {
    sudo apt update
    sudo apt -y install git cmake automake libboost-all-dev libcln-dev libgmp-dev libginac-dev libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev

    sudo apt -y install maven uuid-dev python3-dev libffi-dev libssl-dev python3-pip
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10
}

dynasty-download() {
    mkdir -p $PREREQUISITES

    # mathsat
    # cd $PREREQUISITES
    # wget -O mathsat.tar.gz http://mathsat.fbk.eu/download.php?file=mathsat-5.5.4-linux-x86_64.tar.gz
    # tar -xf mathsat.tar.gz && rm mathsat.tar.gz && mv mathsat-5.5.4-linux-x86_64 mathsat
    # cd $OLDPWD
    # created folder: $PREREQUISITES/mathsat

    # carl
    cd $PREREQUISITES
    git clone -b master14 https://github.com/smtrat/carl
    cd $OLDPWD
    # created folder: $PREREQUISITES/carl

    # pycarl
    cd $PREREQUISITES
    git clone https://github.com/moves-rwth/pycarl.git
    cd $OLDPWD
    # created folder: $PREREQUISITES/pycarl

    # storm
    wget https://zenodo.org/record/3885454/files/moves-rwth/storm-1.6.0.zip
    unzip storm-1.6.0.zip && rm storm-1.6.0.zip
    # created folder: moves-rwth-storm-058fed3

    # stormpy
    wget https://github.com/moves-rwth/stormpy/archive/1.6.0.zip
    unzip 1.6.0.zip && rm 1.6.0.zip
    # created folder: stormpy-1.6.0
}

dynasty-patch-create() {
    rsync -av $SYNTHESIS/storm/src/storm-counterexamples
}

dynasty-patch() {
    rsync -av $SYNTHESIS/storm/ $SYNTHESIS/moves-rwth-storm-058fed3/
        rm -rf $SYNTHESIS/storm
        mv $SYNTHESIS/moves-rwth-storm-058fed3 $SYNTHESIS/storm
    rsync -av $SYNTHESIS/stormpy/ $SYNTHESIS/stormpy-1.6.0/
        rm -rf $SYNTHESIS/stormpy
        mv $SYNTHESIS/stormpy-1.6.0 $SYNTHESIS/stormpy
}

dynasty-setup-python() {
    pip3 install virtualenv
    virtualenv -p python3 $SYNTHESIS_ENV
    source $SYNTHESIS_ENV/bin/activate
    pip3 install pysmt z3-solver click
    deactivate
}

carl-build() {
    cd $PREREQUISITES
    cd carl && mkdir -p build && cd build
    cmake -DUSE_CLN_NUMBERS=ON -DUSE_GINAC=ON -DTHREAD_SAFE=ON ..
    make --jobs $COMPILE_JOBS
    make lib_carl
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
    python3 setup.py build_ext --carl-dir $PREREQUISITES/carl --jobs $COMPILE_JOBS develop
    deactivate
}

storm-config() {
    dot_clean
    mkdir -p $STORM_BLD
    cd $STORM_BLD
    cmake ..
    cd $OLDPWD
}

storm-build() {
    dot_clean
    cd $STORM_BLD
    make storm-main --jobs $COMPILE_JOBS
    cd $OLDPWD
}

stormpy-build() {
    dot_clean
    cd $STORMPY_DIR
    source $SYNTHESIS_ENV/bin/activate
    python3 setup.py build_ext --storm-dir $STORM_BLD --jobs $COMPILE_JOBS develop
    deactivate
    cd $OLDPWD
}

dynasty-install() {
    dot_clean
    cd $DYNASTY_DIR
    source $SYNTHESIS_ENV/bin/activate
    python3 setup.py install
    deactivate
    cd $OLDPWD
}

# aggregated functions

dynasty-nodep() {
    dynasty-download
    dynasty-patch
    dynasty-setup-python

    carl-build
    pycarl-build

    storm-config
    storm-build
    stormpy-build

    dynasty-install
}

dynasty-full() {
    # dynasty-dependencies
    dynasty-nodep
}

storm-rebuild() {
    storm-config
    storm-build
}

stormpy-rebuild() {
    storm-rebuild
    stormpy-build
}

################################################################################
# aliases

alias sc='storm-config'
alias sb='storm-build'
alias pb='stormpy-build'
alias sr='storm-rebuild'

alias synthesis='cd $SYNTHESIS'
alias dyn='cd $SYNTHESIS/dynasty'

alias enva='source $SYNTHESIS_ENV/bin/activate'
alias envd='deactivate'

alias tb='dyn; enva; subl $SYNTHESIS/dynasty/dynasty/family_checkers/integrated_checker.py; subl $SYNTHESIS/dynasty/execute.sh'
alias tf='envd'

# execution
alias dshow='ps -aux | grep "timeout"'
alias dtime='ps -aux | grep "python dynasty.py"'
alias dcount='echo `dshow | wc -l`-1 | bc'
alias dkill='killall bash; killall python'

dlog() {
    cat $SYNTHESIS/dynasty/workspace/log/log_$1.txt
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

ddtmc() {
    dlog $1 | grep "Constructed DTMC"
}

dopt() {
    dlog $1 | grep "Optimal value" | tail -n 1
}

dbounds() {
    dlog $1 | grep "Result for initial"
}
