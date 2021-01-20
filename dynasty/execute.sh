#!/bin/bash

# command-line argument: core index
core=$1

# default parameters
primary_method=hybrid
regime=2
timeout=10d
verbose=false
parallel=false
optimal=false

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

function python-dynasty() {
    local dynasty="python dynasty.py --project ${models_dir}/${model}/ $1 --short-summary"
    local constants="--constants CMAX=${cmax},THRESHOLD=${threshold}"
    local optimality=""
    if [ ${optimal} = "true" ]; then
        optimality="--optimality sketch.optimal --properties optimal.properties"
    fi
    echo \$ ${dynasty} ${constants} ${optimality}
    timeout ${timeout} ${dynasty} ${constants} ${optimality}
}

function dynasty() {
    local parallelity=""
    if [ ${parallel} = "true" ]; then
        parallelity="&"
    fi
    local verbosity='tee >(cat >>${log_file}) >(grep "^> " | cat >>${log_grep_file})'
    if [ ${verbose} = "false" ]; then
        verbosity=${verbosity}' | grep "^> "'
    fi
    command="python-dynasty $1 | ${verbosity} ${parallelity}"
    # echo ${command}
    eval ${command}
}

function try_thresholds() {

    for threshold in `seq ${t_min} ${t_step} ${t_max}`; do
        dynasty $1
    done
    wait
}

function reset_log() {
    > ${log_file}
    > ${log_grep_file}
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
    echo "----- $1"
    for model in "${models[@]}"; do
        choose_model `eval echo '${'${model}'[@]}'`
        echo "--- $model"
        $1
    done
}
# --- sandbox ------------------------------------------------------------------

function test_release() {
    reset_log
    timeout=1m
    parallel=true
    # verbose=true
    model=("herman/orig" 2 0.60 0.75 0.15)
    choose_model "${model[@]}"
    cegar
    echo "^ should be at 15 and 18 sec"
}

function try_herman() {
    reset_log

    timeout=5h
    parallel=true
    # verbose=true
    
    # model=("herman/orig" 2 1.86 1.86 0.6)
    # model=("herman/5" 0 18.1 18.1 0.1)
    # model=("herman/10" 0 1 1 0.1)
    
    choose_model "${model[@]}"

    hybrid
    # cegar
    # cegis
    # onebyone
}

function run() {
    reset_log

    timeout=1h
    # parallel=true
    verbose=true
    # optimal=true
    
    model=("msp/dice-4" 0 2 2 0.1)

    # model=("msp/dpm-main" 10 5700 5700 100.0)
    # model=("grid/big" 1 0.004 0.004 0.003)
    
    choose_model "${model[@]}"

    # hybrid
    # cegar
    # cegis
    onebyone
}

# --- execution ----------------------------------------------------------------

# test_release
# try_herman
run

exit

# --- halted -------------------------------------------------------------------

