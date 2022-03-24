#!/bin/bash

# command-line argument: core index
core=0
if [ -n "$1" ]; then
    core=$1
fi

# default parameters
timeout=100d
pomdp_mem_size=1
fsc_synthesis=false
incomplete_search=false

# workspace settings
paynt_exe="$SYNTHESIS/paynt/paynt.py"
projects_dir="$SYNTHESIS/workspace/examples"
log_dir="$SYNTHESIS/workspace/log"
log_file="${log_dir}/log_${core}.txt"

# ------------------------------------------------------------------------------
# functions

function reset_log() {
    > ${log_file}
}

function paynt() {
    # argument settings
    local project="--project ${projects_dir}/$1/"
    local method=$2

    local incomplete_search_flag=""
    if [ ${incomplete_search} = "true" ]; then
        incomplete_search_flag="--incomplete-search"
    fi

    local fsc_flag=""
    if [ ${fsc_synthesis} = "true" ]; then
        fsc_flag="--fsc-synthesis"
    fi
    local pomdp_memory_set="--pomdp-memory-size=$pomdp_mem_size"

    local paynt_call="python3 ${paynt_exe} ${project} ${method} ${incomplete_search_flag} ${fsc_flag} ${pomdp_memory_set}"
    echo \$ ${paynt_call}

    eval timeout ${timeout} ${paynt_call}
}


# --- sandbox ------------------------------------------------------------------

function run() {

    # timeout=3s

    pomdp_mem_size=1
    fsc_synthesis=true
    # incomplete_search=true

    ### running ###

    # model="coin"
    # model="coin/more"
    # model="dice/5"

    # model="pomdp/maze/concise"

    # model="pomdp/grid/obstacle"
    # model="pomdp/grid/intercept"
    # model="pomdp/grid/evade"
    # model="pomdp/voihp-all/grid-large-10-5"

    ### verification of indefinite-horizon POMDPs ###
    # model="pomdp/voihp-all/grid-4-0.1"
    # model="pomdp/voihp-all/grid-4-0.3"
    model="pomdp/voihp-all/grid-avoid-4-0.1"
    # model="pomdp/voihp-all/grid-avoid-4-0"
    # model="pomdp/voihp-all/maze2-0.1"
    # model="pomdp/voihp/maze2-0"
    # model="pomdp/voihp-other/maze-alex"

    
    # model="pomdp/voihp-hard/drone-4-1"
    # model="pomdp/voihp-all/refuel-06"
    # model="pomdp/voihp-hard/rocks-12"

    # model="pomdp/voihp-all/crypt-4"
    # model="pomdp/voihp-hard/network-prio-2-8-20"
    # model="pomdp/voihp/network-2-8-20"
    # model="pomdp/voihp/nrp-8"


    # model="pomdp/leonore/cheese"
    # model="pomdp/leonore/hallway"
    # model="pomdp/voihp-all/hallway"
    # model="pomdp/voihp-other/grid-avoid-0-mo"
    # model="pomdp/voihp-other/maze-mo"
    # model="pomdp/voihp-other/maze-paper"

    ### CTMC

    # model="ctmc/simple"

    paynt $model ar
    # paynt $model hybrid
    # paynt $model cegis
}

# --- execution ----------------------------------------------------------------

reset_log
run

# --- archive ------------------------------------------------------------------

    ### cav ###
    # model="cav/grid"
    # model="cav/dpm"
    # model="cav/pole"
    # model="herman/5"