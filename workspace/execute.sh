#!/bin/bash

# command-line argument: core index
core=0
if [ -n "$1" ]; then
    core=$1
fi

# default parameters
timeout=100d
verbose=false
parallel=false

# workspace settings
paynt_exe="$SYNTHESIS/paynt/paynt.py"
projects_dir="$SYNTHESIS/workspace/examples"
log_dir="$SYNTHESIS/workspace/log"
log_file="${log_dir}/log_${core}.txt"
log_grep_file="${log_dir}/log_grep_${core}.txt"

# ------------------------------------------------------------------------------
# functions

function reset_log() {
    > ${log_file}
    > ${log_grep_file}
}

# function log() {
#     echo "$@"
#     echo "$@" >> ${log_dir}/log.txt
# }

function choose_project() {
    local arg=$1
    local preset=(`eval echo '${'${arg}'[@]}'`)
    project=${preset[0]}
    cmax=${preset[1]}
    t_min=${preset[2]}
    t_max=${preset[3]}
    t_step=${preset[4]}
}

function python_paynt() {
    local method=$1
    local paynt_call="python3 ${paynt_exe} --project ${projects_dir}/${project}/ $method --short-summary"
    local constants="--constants CMAX=${cmax},THRESHOLD=${threshold}"
    echo \$ ${paynt_call} ${constants} ${optimality}
    timeout ${timeout} ${paynt_call} ${constants} ${optimality}
}

function paynt() {
    local method=$1
    local parallelity=""
    if [ ${parallel} = "true" ]; then
        parallelity="&"
    fi
    local verbosity='tee >(cat >>${log_file}) >(grep "^> " | cat >>${log_grep_file})'
    if [ ${verbose} = "false" ]; then
        verbosity=${verbosity}' | grep "^> "'
    fi
    command="python_paynt $method | ${verbosity} ${parallelity}"
    eval ${command}
}

function try_thresholds() {
    local method=$1
    local project=$2
    choose_project $project
    for threshold in `seq ${t_min} ${t_step} ${t_max}`; do
        paynt $method
    done
    wait
}

function onebyone() {
    try_thresholds onebyone $1
}
function cegis() {
    try_thresholds cegis $1
}
function cegar() {
    try_thresholds cegar $1
}
function hybrid() {
    try_thresholds hybrid $1
}
function evo() {
    try_thresholds evo $1
}

function try_models() {
    local method=$1
    echo "----- $method"
    for model in "${models[@]}"; do
        echo "--- $model"
        choose_model $model
        try_thresholds $method
    done
}

# --- sandbox ------------------------------------------------------------------

function test_release() {
    timeout=1m
    parallel=true
    # verbose=true

    herman=("herman/release-test" 2 0.60 0.75 0.15)
    cegar herman
    echo "^ should be at 15 and 19 sec"
}


function run() {
    # timeout=1s
    parallel=true
    verbose=true
    
    # dpm=("dpm/orig-bat100" 3 140 140 1.0)
    pole=("pole/orig" 0 16.7 16.7 1.0)
    dice=("dice/5" 0 16.7 16.7 1.0)
    coin=("coin" 0 16.7 16.7 1.0)
    # maze=("maze/orig" 0 1 1 1.0)
    # maze=("maze/concise" 0 1 1 1.0)
    maze=("pomdp/maze" 0 2.5 2.5 1.0)
    # grid=("pomdp/grid" 0 2.5 2.5 1.0)
    
    # running ##########

    # model=pole
    # model=dice
    # model=coin
    model=maze
    # model=grid

    # evo dice
    # onebyone coin
    # evo coin
    
    onebyone $model
}

# --- execution ----------------------------------------------------------------

reset_log

# test_release
run

# exit

# --- archive ------------------------------------------------------------------

