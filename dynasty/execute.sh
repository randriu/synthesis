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
    optimality="--optimality sketch.optimal"
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

    timeout=1h
    # parallel=true
    # verbose=true

    grid=("grid/orig" 40 0.004 0.019 0.015)
    gridbig=("grid/big" 40 0.928 0.931 0.003)
    maze=("maze/orig" 50 0.1612764 0.1612766 0.0000002)
    dpm=("dpm/orig" 12 0.078 0.080 0.002)
    pole=("pole/orig" 5 0.732 0.735 0.003)
    herman=("herman/orig" 2 0.60 0.75 0.15)

    models=("grid" "gridbig" "maze" "dpm" "pole" "herman")

    echo "----- CEGAR"
    for model in "${models[@]}"; do
        echo "--- $model"
        choose_model `eval echo '${'${model}'[@]}'`
        # cegar
    done

    echo "----- Hybrid"
    for model in "${models[@]}"; do
        echo "--- $model"
        choose_model `eval echo '${'${model}'[@]}'`
        hybrid
    done

}

function tacas_performance_2() {
    reset_log

    timeout=5m
    parallel=true
    # verbose=true

    # grid=("grid/big" 40 0.928 0.931 0.003)
    grid=("grid/big" 40 0.931 0.931 0.003)

    choose_model "${grid[@]}"

    hybrid
    # cegar
    # cegis
}

function run() {
    reset_log

    timeout=5m
    parallel=true
    verbose=true
    
    model=("grid/orig" 40 0.019 0.019 0.15)
    # model=("grid/big" 40 0.928 0.931 0.003)
    # model=("maze/orig" 50 0.1612764 0.1612764 0.0000002)
    # model=("pole/orig" 5 0.735 0.735 0.001)
    # model=("dpm/orig" 12 0.080 0.080 0.002)
    # model=("herman/orig" 2 0.60 0.60 0.15)

    # model=("herman/orig" 6 0.9254 0.9254 0.15)
    # model=("herman/orig-rew" 2 1.80 1.88 0.02)
    
    # model=("herman/553x_1_0_m" 0 1 1 0.1)

    # model=("herman/553x_1_3_m_r" 3 0.57 0.57 0.1)
    # model=("herman/553x_1_3_m_p" 3 0.57 0.57 0.1)
    # model=("herman/553x_1_3_m_rp" 3 0.57 0.57 0.1)

    # model=("herman/553x_new" 0 0.95 0.95 0.01)

    # models=("r" "rp")
    # for model in "${models[@]}"; do
    #     # echo "--- $model"
    #     choose_model `eval echo '${'${model}'[@]}'`
    #     hybrid
    #     # cegar
    # done

    # model=("herman/553x_r_0" 0 2.0 2.0 0.2)
    # model=("herman/5533_r_0" 0 1.0 1.0 0.2)
    # model=("herman/5555_r_0" 0 1.1 1.3 0.1)

    # ---

    # model=("herman/553x" 0 2 2 0.1)
    # model=("herman/553x-bitbit" 0 2 2 0.1)
    # model=("herman/553x-bitbitbit" 0 2 2 0.1)
    
    choose_model "${model[@]}"

    hybrid
    # cegar
    # cegis
    # onebyone
}

# --- execution ----------------------------------------------------------------

# test_release
# tacas_performance

tacas_performance_2

# run

exit

# --- halted -------------------------------------------------------------------

