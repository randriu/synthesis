#!/bin/bash

# command-line argument: core index
core=$1

# default parameters
primary_method=hybrid
regime=2
timeout=10d
verbose=false
parallel=false

# workspace settings
models_dir="workspace/examples"
log_dir="workspace/log"
parameters_file="${log_dir}/parameters.txt"
log_file="${log_dir}/log_${core}.txt"
log_grep_file="${log_dir}/log_grep_${core}.txt"

# ------------------------------------------------------------------------------

# presets: TACAS
grid=("grid/orig" 40 0.004 0.019 0.003)
gridbig=("grid/big" 40 0.927 0.931 0.001)
maze=("maze/orig" 50 0.16127640 0.16127660 0.00000005)
pole=("pole/orig" 5 0.732 0.736 0.001)
dpm=("dpm/orig" 12 0.078 0.081 0.001)
herman=("herman/orig" 2 0.60 0.75 0.05)

CMAX=6
herbig=("herman/big" ${CMAX} 0.95 0.95 0.3)


# ------------------------------------------------------------------------------
# functions

function choose_model() {
    preset=("$@")
    model=${preset[0]}
    cmax=${preset[1]}
    t_min=${preset[2]}
    t_max=${preset[3]}
    t_step=${preset[4]}
}

function log_output() {
    while read input; do
        if [ ${verbose} = "true" ]; then
            echo ${input} | tee --append ${log_file}
        else
            echo ${input} | tee --append ${log_file} | grep "^> " | tee --append ${log_grep_file}
        fi
    done
}

function dynasty() {
    dynasty="python dynasty.py hybrid --regime $1 --project ${models_dir}/${model}/ --short-summary"
    constants="--constants CMAX=${cmax},THRESHOLD=${threshold}"
    # optimality="--optimality sketch.optimal"
    echo ${dynasty} ${constants} ${optimality}
    timeout ${timeout} ${dynasty} ${constants} ${optimality}
}

function try_thresholds() {
    for threshold in `seq ${t_min} ${t_step} ${t_max}`; do
        if [ ${parallel} = "false" ]; then
            dynasty $1 | log_output
        else
            dynasty $1 | log_output &
        fi
    done
    wait
}

function reset_log() {
    > ${log_file}
    > ${log_grep_file}
}

function onebyone() {
    try_thresholds 0
}

function cegis() {
    try_thresholds 1
}

function cegar() {
    try_thresholds 2
}

function hybrid() {
    try_thresholds 3
}

function try_models() {
    echo "----- $1"
    for model in "${models[@]}"; do
        choose_model `eval echo '${'${model}'[@]}'`
        echo "--- $model"
        $1
    done
}
# --- sandbox ------------------------------------------------------------------

function test_release() {
    parallel=true
    reset_log
    model=("herman/orig" 2 0.60 0.75 0.15)
    choose_model "${model[@]}"
    cegar
    echo "^ should be at 15 and 18 sec"
}

function tacas_performance() {
    reset_log

    timeout=5m
    parallel=true
    # verbose=true

    grid=("grid/big" 40 0.931 0.927 -0.004)
    maze=("maze/orig" 50 0.1612764 0.1612766 0.0000002)
    dpm=("dpm/half" 12 0.078 0.0818 0.0038)
    pole=("pole/orig" 0 3.350 3.355 0.005)
    herman=("herman/orig" 2 1.2 1.8 0.6)

    models=("grid" "maze" "dpm" "pole" "herman")

    try_models cegis
    # try_models cegar
    # try_models hybrid
}

function try_herman() {
    reset_log

    timeout=1s
    parallel=true
    # verbose=true

    # model=("herman/3_1" 0 0.0 0.9 0.1)
    
    # model=("herman/5_feas" 0 18.0 19.0 0.1)
    # model=("herman/5_opt" 0 0 0 0.1)
    
    # model=("herman/10_1" 0 0.1 0.1 0.1)
    # model=("herman/15_1" 0 0 0 1.0)
    # model=("herman/20_1" 0 0 0 1.0)
    
    model=("herman/25_feas" 0 3.6 4.0 0.4)
    # model=("herman/25_opt" 0 0.0 0.0 1.0)
    
    choose_model "${model[@]}"

    # hybrid
    # cegar
    cegis
    # onebyone
}

# --- execution ----------------------------------------------------------------

# test_release

# tacas_performance
try_herman

# run

exit

# --- halted -------------------------------------------------------------------

