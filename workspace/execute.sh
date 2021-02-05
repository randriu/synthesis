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
optimal=false

# workspace settings
dynasty_exe="$SYNTHESIS/dynasty/dynasty.py"
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
    echo $cmax
    t_min=${preset[2]}
    t_max=${preset[3]}
    t_step=${preset[4]}
}

function python_dynasty() {
    local method=$1
    local dynasty_call="python3 ${dynasty_exe} --project ${projects_dir}/${project}/ $method --short-summary"
    local constants="--constants CMAX=${cmax},THRESHOLD=${threshold}"
    local optimality=""
    if [ ${optimal} = "true" ]; then
        optimality="--optimality sketch.optimal --properties optimal.properties"
    fi
    echo \$ ${dynasty_call} ${constants} ${optimality}
    timeout ${timeout} ${dynasty_call} ${constants} ${optimality}
}

function dynasty() {
    local method=$1
    local parallelity=""
    if [ ${parallel} = "true" ]; then
        parallelity="&"
    fi
    local verbosity='tee >(cat >>${log_file}) >(grep "^> " | cat >>${log_grep_file})'
    if [ ${verbose} = "false" ]; then
        verbosity=${verbosity}' | grep "^> "'
    fi
    command="python_dynasty $method | ${verbosity} ${parallelity}"
    eval ${command}
}

function try_thresholds() {
    local method=$1
    local project=$2
    choose_project $project
    for threshold in `seq ${t_min} ${t_step} ${t_max}`; do
        dynasty $method
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
    # optimal=true

    herman=("herman/release-test" 2 0.60 0.75 0.15)
    cegar herman
    echo "^ should be at 15 and 19 sec"
}

function tacas() {
    timeout=10m
    parallel=true

    grid=("grid/big" 40 0.931 0.927 -0.004)
    maze=("maze/orig" 50 0.1612764 0.1612766 0.0000002)
    dpm=("dpm/half" 12 0.078 0.0818 0.0038)
    pole=("pole/orig" 0 3.350 3.355 0.005)
    herman=("herman/orig" 2 1.2 1.8 0.6)

    models=( grid maze dpm pole herman )
    # try_models onebyone
    # try_models cegar
    try_models hybrid
}

function cav() {
    mkdir -p $log_dir/cav

    timeout=7d
    # parallel=true

    dpm=("cav/dpm/orig-bat100" 10 140 140 1.0)
    maze=("cav/maze/fixed-full" 0 7.32 7.32 1.0)
    herman=("cav/herman/25-orig" 0 3.5 3.5 1.0)
    pole=("cav/pole/fixed" 0 16.6566 16.6566 1.0)
    grid=("cav/grid/big" 40 0.928 0.928 1.0)

    optimal=false
    for model in dpm maze herman pole grid; do
        log_file=$log_dir/cav/hybrid_f_$model.txt
        hybrid $model
    done
    optimal=true
    for model in dpm maze herman pole grid; do
        log_file=$log_dir/cav/hybrid_0_$model.txt
        hybrid $model
    done
    optimal=true
    for model in dpm maze herman pole grid; do
        log_file=$log_dir/cav/onebyone_$model.txt
        onebyone $model &
    done
    wait
}

function cav_summary() {
    for log in $log_dir/cav/*.txt; do
        echo "--- ${log} --"
        head $log -n 100 >> ${log}_2
        tail $log -n 100 >> ${log}_2
        mv ${log}_2 ${log}
        cat $log | tail -n 12
    done
}

function run() {
    timeout=3s
    parallel=true
    # verbose=true
    optimal=true
    
    # dpm ##########

    # model=("cav/dpm/demo" 10 1 1 1.0)
    # model=("cav/dpm/orig" 10 5000 5000 1.0)
    # model=("cav/dpm/orig-bat100" 10 140 140 1.0)
    # model=("cav/dpm/orig-bat100" 10 138 138 1.0)

    # maze ##########

    # model=("cav/maze/orig-partial" 0 1 1 1.0)
    # model=("cav/maze/orig-full" 0 1 1 1.0)

    # model=("cav/maze/fixed-partial" 0 1 1 1.0)
    # model=("cav/maze/fixed-full" 0 6.50 6.50 1.0)
    
    # model=("cav/maze/new-partial" 0 1 1 1.0)
    # model=("cav/maze/new-full" 0 1 1 1.0)

    # herman ##########

    # model=("cav/herman/25-orig" 0 3.5 3.5 1.0)
    # model=("cav/herman/25-int" 0 3.89 3.89 1.0)
    
    # grid ##########

    # model=("cav/grid/big" 40 0.928 0.928 1.0)

    # pole ##########

    # model=("cav/pole/fixed" 0 16.6566 16.6566 1.0)

    # selected benchmark #######################################################

    dpm=("cav/dpm/orig-bat100" 10 140 140 1.0)
    maze=("cav/maze/fixed-full" 0 7.32 7.32 1.0)
    herman=("cav/herman/25-orig" 0 3.5 3.5 1.0)
    pole=("cav/pole/fixed" 0 16.6566 16.6566 1.0)
    grid=("cav/grid/big" 40 0.928 0.928 1.0)
    
    # running ##########

    model=grid

    hybrid $model
    # onebyone $model
}

# --- execution ----------------------------------------------------------------

reset_log

test_release
# run

# tacas

# cav
# cav_summary

# exit

# --- halted -------------------------------------------------------------------

