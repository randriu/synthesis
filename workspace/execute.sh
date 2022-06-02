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
    # local sketch="--sketch sketch.pomdp"
    local method="--method $2"

    local incomplete_search_flag=""
    if [ ${incomplete_search} = "true" ]; then
        incomplete_search_flag="--incomplete-search"
    fi

    local fsc_flag=""
    if [ ${fsc_synthesis} = "true" ]; then
        fsc_flag="--fsc-synthesis"
    fi
    local pomdp_memory_set="--pomdp-memory-size=$pomdp_mem_size"

    local paynt_call="python3 ${paynt_exe} ${project} ${sketch} ${method} ${incomplete_search_flag} ${fsc_flag} ${pomdp_memory_set} ${other_flags}"
    echo \$ ${paynt_call}

    eval timeout ${timeout} ${paynt_call}
}


# --- sandbox ------------------------------------------------------------------

function run() {

    timeout=300s

    # pomdp_mem_size=1
    fsc_synthesis=true
    # incomplete_search=true

    ### running ###

    # model="coin"
    # model="coin/more"
    # model="dice/5"
    # model="dtmc/maze/concise"

    ### uai
    # model="pomdp/uai/crypt-4"
    # model="pomdp/uai/drone-4-1"
    # model="pomdp/uai/drone-4-2"
    # model="pomdp/uai/grid-avoid-4-0"
    # model="pomdp/uai/grid-avoid-4-0.1"
    # model="pomdp/uai/grid-large-30-5"
    model="pomdp/uai/hallway"
    other_flags="--filetype drn"
    # model="pomdp/uai/maze-alex"
    # model="pomdp/uai/network-prio-2-8-20"
    # model="pomdp/uai/nrp-8"
    # model="pomdp/uai/refuel-06"
    # model="pomdp/uai/rocks-12"


    ### test

    # model="ctmc/simple"
    # model="mdp/simple"
    # model="mdp/maze"
    # model="pomdp/maze"
    # model="pomdp/maze/mba"

    # model="pomdp/sarsop/hallway"
    # model="pomdp/sarsop/hallway-single"
    # model="pomdp/sarsop/4x4.95"
    # model="pomdp/sarsop/4x5x2.95"
    # model="pomdp/sarsop/1d"
    # model="pomdp/sarsop/simple"

    # model="pomdp/sarsop/prism-grid-4-0.1"
    # model="pomdp/sarsop/prism-maze-alex"

    # model="pomdp/sarsop/current"

    # other_flags="--help"
    # other_flags="--sketch sketch.pomdp --filetype pomdp --export drn"
    # other_flags="--sketch sketch.pomdp --filetype pomdp"
    # other_flags="--sketch sketch.drn --filetype drn --export pomdp"
    # other_flags="--sketch sketch.drn --filetype drn"

    # other_flags="--sketch sketch.pomdp --properties props.pomdp"
    # other_flags="--sketch sketch.pomdp"
    # other_flags="--props sketch.props"

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