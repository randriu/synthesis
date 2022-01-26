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
pomdp=false

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

function python_paynt() {
    local project=$1
    local method=$2
    local pomdp_flag=""
    if [ ${pomdp} = "true" ]; then
        pomdp_flag="--pomdp"
    fi
    local paynt_call="python3 ${paynt_exe} --project ${projects_dir}/${project}/ $method $pomdp_flag"
    echo \$ ${paynt_call}
    timeout ${timeout} ${paynt_call} ${constants}
}

function paynt() {
    local project=$1
    local method=$2
    local parallelity=""
    if [ ${parallel} = "true" ]; then
        parallelity="&"
    fi
    local verbosity='tee >(cat >>${log_file}) >(grep "^> " | cat >>${log_grep_file})'
    if [ ${verbose} = "false" ]; then
        verbosity=${verbosity}' | grep "^> "'
    fi
    command="python_paynt $project $method | ${verbosity} ${parallelity}"
    eval ${command}
}

function onebyone() {
    paynt $1 onebyone
}
function cegis() {
    paynt $1 cegis
}
function ar() {
    paynt $1 ar
}
function hybrid() {
    paynt $1 hybrid
}

# --- sandbox ------------------------------------------------------------------

function run() {
    timeout=120s
    parallel=false
    verbose=true

    # pomdp=true

    # running ##########

    # model="coin"
    # model="coin/more"
    # model="dice/5"

    model="pomdp/maze/concise"
    # model="pomdp/maze/2"
    
    # model="pomdp/drone"
    # model="pomdp/crypt/4"
    # model="pomdp/network/simple-2"
    # model="pomdp/network/priorities-2"
    # model="pomdp/nrp"
    # model="pomdp/samplerocks"

    # model="pomdp/grid/avoid"
    # model="pomdp/grid/simple"
    # model="pomdp/grid/simple-mo"

    # model="pomdp/grid/refuel"
    # model="pomdp/grid/obstacle"
    # model="pomdp/grid/intercept"
    # model="pomdp/grid/evade"

    ### leonore ###

    # model="pomdp/leonore/refuel"
    # model="pomdp/leonore/avoid"
    # model="pomdp/leonore/sketch"
    # model="pomdp/leonore/cheese"

    ## cav ##
    # model="cav/grid"
    # model="cav/dpm"
    # model="cav/pole"
    # model="herman/5"

    # model="mdp"

    # ar $model
    hybrid $model
}

# --- execution ----------------------------------------------------------------

reset_log
run
# exit

# --- archive ------------------------------------------------------------------

