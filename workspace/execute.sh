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
    timeout=1000s
    parallel=false
    verbose=true

    pomdp=true

    coin="coin"
    # coin="coin/more"
    dice="dice/5"

    m="pomdp/obstacle"

    drone="pomdp/drone"
    crypt="pomdp/crypt"
    network="pomdp/network"
    nrp="pomdp/nrp"
    samplerocks="pomdp/samplerocks"

    maze="pomdp/maze/concise"
    # maze="pomdp/maze/2"

    avoid="pomdp/grid/avoid"
    avoids="pomdp/grid/avoid-slippery"
    refuel="pomdp/grid/refuel"
    obstacle="pomdp/grid/obstacle"
    intercept="pomdp/grid/intercept"
    evade="pomdp/grid/evade"

    leo_refuel="pomdp/leonore/refuel"
    leo_avoid="pomdp/leonore/avoid"
    leo_sketch="pomdp/leonore/sketch"

    cav_dpm="cav/dpm"
    cav_pole="cav/pole"
    herman="herman/5"

    # running ##########

    # model=$coin
    # model=$dice

    # model=$drone
    model=$crypt
    # model=$maze
    # model=$network
    # model=$nrp
    # model=$samplerocks

    # model=$avoid
    # model=$avoids
    model=$refuel
    # model=$obstacle
    # model=$intercept
    # model=$evade
    # todo rocks

    ### leonore ###

    # model=$leo_refuel
    # model=$leo_avoid
    # model=$leo_sketch

    ## cav ##
    # model=$cav_dpm
    # model=$cav_pole # error
    # model=$herman

    # model=$m

    # onebyone $model
    ar $model
    # cegis $model
    # hybrid $model
}

# --- execution ----------------------------------------------------------------

reset_log
run
# exit

# --- archive ------------------------------------------------------------------

