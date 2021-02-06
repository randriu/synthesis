#!/bin/bash

# compilation parameters

export COMPILE_JOBS=$(nproc)

# environment variables

export SYNTHESIS=`pwd`
export PREREQUISITES=$SYNTHESIS/prerequisites
export SYNTHESIS_ENV=$SYNTHESIS/env

export STORM_DIR=$SYNTHESIS/storm
export STORM_BLD=$STORM_DIR/build

export DYNASTY_DIR=$SYNTHESIS/dynasty

### storm patch ################################################################

dynasty-patch-create() {
    echo "NOT IMPLEMENTED YET"
}

dynasty-patch() {
    rsync -av $SYNTHESIS/patch/ $SYNTHESIS/
}

### storm and stormpy ##########################################################

storm-config() {
    mkdir -p $STORM_BLD
    cd $STORM_BLD
    cmake ..
    cd ~-
}

storm-build() {
    cd $STORM_BLD
    make storm-main --jobs $COMPILE_JOBS
    # make check --jobs $COMPILE_JOBS
    cd ~-
}

stormpy-build() {
    cd $SYNTHESIS/stormpy
    source $SYNTHESIS_ENV/bin/activate
    python3 setup.py build_ext --storm-dir $STORM_BLD --jobs $COMPILE_JOBS develop
    # python3 setup.py test
    deactivate
    cd ~-
}

dynasty-install() {
    cd $DYNASTY_DIR
    source $SYNTHESIS_ENV/bin/activate
    python3 setup.py install
    # python3 setup.py test
    deactivate
    cd ~-
}

synthesis-install() {
    cd $SYNTHESIS
    bash install.sh
    cd ~-
}

### development ################################################################

# recompilation

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


### executing dynasty ##########################################################

export WORKSPACE=$SYNTHESIS/workspace
export DYNASTY_LOG=$WORKSPACE/log

alias enva='source $SYNTHESIS_ENV/bin/activate'
alias envd='deactivate'

function dynasty() {
    local core=0
    if [ -n "$1" ]; then
        core=$1
    fi
    local exp_sh=$WORKSPACE/execute.sh
    local run_sh=$DYNASTY_LOG/run_${core}.sh

    cd $WORKSPACE
    mkdir -p $DYNASTY_LOG
    cp $exp_sh $run_sh
    source $SYNTHESIS_ENV/bin/activate
    bash $run_sh $core
    deactivate
    cd ~-
}
function d() {
    dynasty $1
}
function db() {
    dynasty $1 & disown
}

alias dpid='pgrep -f "^python dynasty.py .*"'
alias dtime='ps -aux | grep "python dynasty.py"'
alias dshow='pgrep -af "^python dynasty.py .*"'
alias dcount='pgrep -afc "^python dynasty.py .*"'
alias dkill='dpid | xargs kill'

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
dce() {
    dlog $1 | grep "generalized"
}
dperf() {
     dlog $1 | grep "Performance" | tail -n 1
}

dholes() {
    dlog $1 | grep "hole assignment:" | awk '{print $3}'
}

### binds ###

bind '"\ei"':"\"storm-config \C-m\""
bind '"\eo"':"\"storm-build \C-m\""
bind '"\ep"':"\"stormpy-build \C-m\""

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
    storm "--jani $DYNASTY_DIR/output_1.jani --prop $DYNASTY_DIR/workspace/examples/cav/maze/orig/compute.properties"
}

storm-eval() {
    storm "$1 --prop $2 --constants $3"
}

export DPM=$DYNASTY_DIR/workspace/examples/cav/dpm-main
export DICE=$DYNASTY_DIR/workspace/examples/cav/dice
export MAZE=$DYNASTY_DIR/workspace/examples/cav/maze

dice() {
    storm-eval "--prism $DICE/sketch.templ" $DICE/compute.properties "CMAX=0,THRESHOLD=0,$1"
}
dpm() {
    storm-eval "--prism $DPM/sketch.templ" $DPM/compute.properties "CMAX=10,THRESHOLD=0,T2=5,$1"
}


