#!/bin/bash

# compilation parameters

export COMPILE_JOBS=$(nproc)

# environment variables

export SYNTHESIS=`pwd`
export PREREQUISITES=$SYNTHESIS/prerequisites
export DOWNLOADS=$PREREQUISITES/downloads

export SYNTHESIS_ENV=$SYNTHESIS/env

export STORM_DIR=$SYNTHESIS/storm
export STORM_BLD=$STORM_DIR/build
export STORM_BLD_DEBUG=$STORM_DIR/build_debug

export STORMPY_BLD=$SYNTHESIS/stormpy/build
export STORMPY_BLD_DEBUG=$SYNTHESIS/stormpy/build_debug

export PAYNT_DIR=$SYNTHESIS/paynt

### prerequisites ##############################################################

prerequisites-download() {
    cd $DOWNLOADS
    wget https://github.com/ths-rwth/carl/archive/refs/heads/master14.zip -O carl.zip
    wget https://github.com/moves-rwth/pycarl/archive/refs/tags/2.0.5.zip -O pycarl.zip
    wget https://github.com/cvc5/cvc5/archive/refs/tags/cvc5-0.0.6.zip -O cvc5.zip
    # wget https://github.com/moves-rwth/storm/archive/refs/tags/1.6.4.zip -O storm.zip
    # wget https://github.com/moves-rwth/stormpy/archive/refs/tags/1.6.4.zip -O stormpy.zip
    cd -
}

prerequisites-prepare() {
    cd $PREREQUISITES    
    unzip $DOWNLOADS/carl.zip
    mv carl-master14 carl
    unzip $DOWNLOADS/pycarl.zip
    mv pycarl-2.0.5 pycarl
    unzip $DOWNLOADS/cvc5.zip
    mv cvc5-cvc5-0.0.6 cvc5
    cd -
}

alias enva='source $SYNTHESIS_ENV/bin/activate'
alias envd='deactivate'

python-environment() {
    pip3 install virtualenv
    virtualenv -p python3 $SYNTHESIS_ENV
    enva
    pip3 install pytest pytest-runner pytest-cov numpy scipy pysmt z3-solver click
    pip3 install Cython scikit-build
    envd
}

prerequisites-build-carl() {
    mkdir -p $PREREQUISITES/carl/build
    cd $PREREQUISITES/carl/build
    cmake -DUSE_CLN_NUMBERS=ON -DUSE_GINAC=ON -DTHREAD_SAFE=ON ..
    make lib_carl --jobs $COMPILE_JOBS
    #[TEST] make test
    cd -
}

prerequisites-build-pycarl() {
    cd $PREREQUISITES/pycarl
    enva
    python3 setup.py build_ext --jobs $COMPILE_JOBS develop
    #[TEST] python3 setup.py test
    envd
    cd -
}

prerequisites-build-cvc5() {
    # configuration
    cd $PREREQUISITES/cvc5
    enva
    ./configure.sh --prefix="." --auto-download --python-bindings
    cd build
    make --jobs $COMPILE_JOBS
    make install
    envd
    cd -
}

storm-dependencies() {
    sudo apt update
    sudo apt -y install build-essential git automake cmake libboost-all-dev libcln-dev libgmp-dev libginac-dev libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev
    sudo apt -y install texlive-latex-extra
    sudo apt -y install maven uuid-dev python3-dev libffi-dev libssl-dev python3-pip
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10
}

### storm and stormpy ##########################################################

storm-config() {
    mkdir -p $STORM_BLD
    cd $STORM_BLD
    cmake ..
    cd ~-
}

storm-config-debug() {
    mkdir -p $STORM_BLD_DEBUG
    cd $STORM_BLD_DEBUG
    cmake .. -DSTORM_DEVELOPER=ON -DSTORM_USE_LTO=OFF
    cd ~-
}

storm-build() {
    cd $STORM_BLD
    make storm-main storm-synthesis --jobs $COMPILE_JOBS
    # make check --jobs $COMPILE_JOBS
    cd ~-
}

storm-build-debug() {
    cd $STORM_BLD_DEBUG
    make storm-main storm-synthesis --jobs $COMPILE_JOBS
    cd ~-
}

stormpy-build() {
    cd $SYNTHESIS/stormpy
    enva
    python3 setup.py build_ext --build-temp $STORMPY_BLD --storm-dir $STORM_BLD --jobs $COMPILE_JOBS develop
    # python3 setup.py test
    envd
    cd ~-
}

stormpy-build-debug() {
    cd $SYNTHESIS/stormpy
    enva
    python3 setup.py build_ext --build-temp $STORMPY_BLD --storm-dir $STORM_BLD_DEBUG --jobs $COMPILE_JOBS develop
    # python3 setup.py test
    envd
    cd ~-
}

paynt-install() {
    cd $PAYNT_DIR
    enva
    python3 setup.py install
    # python3 setup.py test
    envd
    cd ~-
}

paynt-check() {
    cd $PAYNT_DIR
}

synthesis-install() {

    # clone repository
    git clone https://github.com/randriu/synthesis.git
    # git clone git@github.com:randriu/synthesis.git
    cd synthesis
    
    # load aliases
    source workspace/storm-alias.sh
    
    # install dependencies
    storm-dependencies
    # setup python environment
    python-environment

    # unzip prerequisites
    prerequisites-prepare
    # build carl
    prerequisites-build-carl
    # build pycarl
    prerequisites-build-pycarl
    # build cvc5 (optional)
    prerequisites-build-cvc5

    # configure storm
    storm-config
    # build storm
    storm-build
    # build stomrpy
    stormpy-build
    # install paynt
    paynt-install

    # check
    paynt workspace/examples/coin
}

### development ################################################################

# aliases

# alias sc='storm-config'
# alias sb='storm-build'
# alias pb='stormpy-build'
# alias sr='storm-rebuild'


### executing paynt ##########################################################

export WORKSPACE=$SYNTHESIS/workspace
export DYNASTY_LOG=$WORKSPACE/log

function paynt() {
    local project=$1
    enva
    python3 $PAYNT_DIR/paynt.py --project ${project} ar
    envd
}

function paynt-execute() {
    local core=0
    if [ -n "$1" ]; then
        core=$1
    fi
    local exp_sh=$WORKSPACE/execute.sh
    local run_sh=$DYNASTY_LOG/run_${core}.sh

    mkdir -p $DYNASTY_LOG
    cd $DYNASTY_LOG
    cp $exp_sh $run_sh
    enva
    bash $run_sh $core
    envd
    cd ~-
}
function d() {
    paynt-execute $1
}
function db() {
    paynt-execute $1 & disown
}

alias dpid='pgrep -f "^python3 .*/paynt.py .*"'
alias dtime='ps -aux | grep "python3 .*/paynt.py"'
alias dshow='pgrep -af "^python3 .*/paynt.py .*"'
alias dcount='pgrep -afc "^python3 .*/paynt.py .*"'
alias dkill='dpid | xargs kill'
alias k='dkill'
alias dclear='rm $DYNASTY_LOG/*'

dlog() {
    cat $DYNASTY_LOG/log_$1.txt
}
dgrep() {
    cat $DYNASTY_LOG/log_grep_$1.txt
}

dhead() {
    dlog $1 | head -n 50
}
dtail() {
    dlog $1 | tail -n 50
}


### binds ###

bind '"\ei"':"\"storm-config \C-m\""
bind '"\ek"':"\"storm-config-debug \C-m\""
bind '"\eo"':"\"storm-build \C-m\""
bind '"\el"':"\"storm-build-debug \C-m\""
bind '"\ep"':"\"stormpy-build \C-m\""
bind '"\e;"':"\"stormpy-build-debug \C-m\""

bind '"\ed"':"\"db \C-m\""
bind '"\e1"':"\"db 1 \C-m\""
bind '"\e2"':"\"db 2 \C-m\""
bind '"\e3"':"\"db 3 \C-m\""
bind '"\e4"':"\"db 4 \C-m\""
bind '"\e5"':"\"db 5 \C-m\""
bind '"\e6"':"\"db 6 \C-m\""
bind '"\e7"':"\"db 7 \C-m\""
bind '"\e8"':"\"db 8 \C-m\""

### executing storm  ###########################################################

storm() {
    cd $STORM_BLD/bin
    local cmd="./storm --explchecks --build-overlapping-guards-label $1"
    eval $cmd
    cd -
}

storm-jani() {
    storm "--jani $PAYNT_DIR/output_0.jani --prop $PAYNT_DIR/workspace/examples/cav/maze/orig/compute.properties"
}

storm-eval() {
    storm "$1 --prop $2 --constants $3"
}

export DPM=$SYNTHESIS/workspace/examples/cav/dpm-main
export DICE=$SYNTHESIS/workspace/examples/cav/dice
export MAZE=$SYNTHESIS/workspace/examples/cav/maze
export WALK=$SYNTHESIS/workspace/examples/random-walk
export MAZE2=$SYNTHESIS/workspace/examples/maze/orig

dice() {
    storm-eval "--prism $DICE/sketch.templ" $DICE/compute.properties "CMAX=0,THRESHOLD=0,$1"
}


# useful flags
# ./storm-pomdp --prism $SYNTHESIS/workspace/examples/pomdp/maze/concise/sketch.templ --constants CMAX=2,THRESHOLD=1.0 --prop $SYNTHESIS/workspace/examples/pomdp/maze/concise/sketch.properties -ec --io:exportexplicit test.drn

