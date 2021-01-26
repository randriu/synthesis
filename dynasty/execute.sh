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

function run() {
    # timeout=2d
    parallel=true
    # verbose=true
    optimal=true
    
    # model=("cav/dice/3" 0 2 2 0.1)
    # model=("cav/dice/4" 0 2 2 0.1)

    model=("cav/dpm-main" 10 3000 3000 500.0)
    # model=("cav/dpm-test" 10 3000 3000 500.0)

    # model=("grid/big" 40 0.004 0.010 0.001)
    
    choose_model "${model[@]}"

    hybrid
    # cegar
    # cegis
    # onebyone
}

# --- execution ----------------------------------------------------------------

reset_log

# test_release
# tacas
run

exit

# --- halted -------------------------------------------------------------------

