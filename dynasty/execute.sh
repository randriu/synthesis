#!/bin/bash

# command-line argument: core index
core=$1

# default parameters
timeout=100d
verbose=false
parallel=false
optimal=false

# workspace settings
models_dir="workspace/examples"
log_dir="workspace/log"
log_file="${log_dir}/log_${core}.txt"
log_grep_file="${log_dir}/log_grep_${core}.txt"

# ------------------------------------------------------------------------------
# presets


# ------------------------------------------------------------------------------
# functions

function reset_log() {
    > ${log_file}
    > ${log_grep_file}
}

function log() {
    echo "$@"
    echo "$@" >> ${log_dir}/log.txt
}

function choose_model() {
    preset=("$@")
    model=${preset[0]}
    cmax=${preset[1]}
    t_min=${preset[2]}
    t_max=${preset[3]}
    t_step=${preset[4]}
}

function python_dynasty() {
    local method=$1
    local dynasty="python dynasty.py --project ${models_dir}/${model}/ $method --short-summary"
    local constants="--constants CMAX=${cmax},THRESHOLD=${threshold}"
    local optimality=""
    if [ ${optimal} = "true" ]; then
        optimality="--optimality sketch.optimal --properties optimal.properties"
    fi
    echo \$ ${dynasty} ${constants} ${optimality}
    timeout ${timeout} ${dynasty} ${constants} ${optimality}
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
    for threshold in `seq ${t_min} ${t_step} ${t_max}`; do
        dynasty $method
    done
    wait
}

function onebyone() {
    try_thresholds onebyone
}
function cegis() {
    try_thresholds cegis
}
function cegar() {
    try_thresholds cegar
}
function hybrid() {
    try_thresholds hybrid
}

function try_models() {
    local method=$1
    echo "----- $method"
    for model in "${models[@]}"; do
        echo "--- $model"
        choose_model `eval echo '${'${model}'[@]}'`
        try_thresholds $method
    done
}

# --- sandbox ------------------------------------------------------------------

function test_release() {
    timeout=1m
    parallel=true
    # verbose=true
    # optimal=true

    model=("herman/release-test" 2 0.60 0.75 0.15)
    choose_model "${model[@]}"
    cegar
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

    # models=( grid maze dpm pole herman )
    models=( dpm )
    # try_models onebyone
    # try_models cegar
    try_models hybrid
}

function cav() {
    timeout=2d
    # parallel=true
    optimal=true

    dpm=("cav/dpm/orig-bat100" 10 140 140 1.0)
    maze=("cav/maze/fixed-full" 0 7.32 7.32 1.0)
    herman=("cav/herman/25-orig" 0 3.5 3.5 1.0)
    pole=("cav/pole/fixed" 0 16.6566 16.6566 1.0)
    grid=("cav/grid/big" 40 0.928 0.928 1.0)

    for method in hybrid onebyone; do
        log "----- ${method} -----"
        for model in dpm maze herman pole grid; do
            log "--- ${model}"
            choose_model `eval echo '${'${model}'[@]}'`
            eval $method
            cat ${log_file} | tail -n 12 >> ${log_dir}/log.txt
        done
    done
}

function run() {
    timeout=3h
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

    # models=( dpm maze herman pole grid )

    # for model in "${models[@]}"; do
    #     echo "--- $model" >> ${log_dir}/log.txt
    #     choose_model `eval echo '${'${model}'[@]}'`
    #     try_thresholds onebyone
    #     cat ${log_file} | tail -n 5 >> ${log_dir}/log.txt
    # done
    
    choose_model "${model[@]}"

    # hybrid
    # cegar
    # cegis
    onebyone
}

# --- execution ----------------------------------------------------------------

reset_log

# test_release
# tacas
cav
# run

exit

# --- halted -------------------------------------------------------------------

