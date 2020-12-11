#!/bin/bash

# command-line argument: core index
# if [ -n "$1" ]; then
#     core=$1
# else
#     core="0"
# fi
core=$1

# default parameters
regime=0
timeout=720h
score_limit=999999
verbose=false
parallel=false

# synthesis method
# primary_method=cschedenum
# primary_method=cegis
primary_method=research

# presets: TACAS
grid=("grid/orig" 40 0.004 0.019 0.003)
gridbig=("grid/big" 40 0.927 0.931 0.001)
maze=("maze/orig" 50 0.16127640 0.16127660 0.00000005)
pole=("pole/orig" 5 0.732 0.736 0.001)
dpm=("dpm/orig" 12 0.078 0.081 0.001)
herman=("herman/orig" 2 0.60 0.75 0.05)

CMAX=6
herbig=("herman/big" ${CMAX} 0.95 0.95 0.3)

# preset candidates
mazexxl=("maze/xxl" 50 0.1 0.1 0.1)
virus=("virus/orig" 0 0.1 0.9 0.1)

# workspace settings
examples_dir="workspace/examples"
log_dir="workspace/log"
parameters_file="${log_dir}/parameters.txt"
log_file="${log_dir}/log_${core}.txt"
log_grep_file="${log_dir}/log_grep_${core}.txt"

# ------------------------------------------------------------------------------
# functions

function log_output() {
    while read input; do
        if [ ${verbose} = "false" ]; then
            echo ${input} | tee --append ${log_file} | grep "^> " | tee --append ${log_grep_file}
        else
            echo ${input} | tee --append ${log_file}
        fi
    done
}

function choose_model() {
    preset=("$@")
    model=${preset[0]}
    cmax=${preset[1]}
    t_min=${preset[2]}
    t_max=${preset[3]}
    t_step=${preset[4]}
}

function write_params() {
    echo $regime > $parameters_file
    echo $score_limit >> $parameters_file
}

function dynasty() {
    dynasty_opts="--project ${examples_dir}/${model}/ --sketch sketch.templ --allowed sketch.allowed --properties sketch.properties"
    # dynasty_opts="--project ${examples_dir}/${model}/ --sketch sketch.templ --allowed sketch.allowed --properties sketch.properties --restrictions sketch.restrictions"
    dynasty="python dynasty.py ${dynasty_opts} ${primary_method}"
    constants="--constants CMAX=${cmax},THRESHOLD=${threshold}"
    timeout ${timeout} ${dynasty} ${constants} ${OPTIMALITY}
}

function try_thresholds() {
    for threshold in `seq ${t_min} ${t_step} ${t_max}`; do
        if [ ${parallel} = "false" ]; then
            dynasty | log_output
        else
            dynasty | log_output &
        fi
    done
    wait
}

reset_log() {
    echo "" > ${log_file}
    echo "" > ${log_grep_file}
    write_params
}

function onebyone() {
    regime=1
    write_params
    try_thresholds
}

function cegis() {
    regime=2
    write_params
    try_thresholds
}

function cegar() {
    regime=3
    write_params
    try_thresholds
}

function hybrid() {
    regime=4
    write_params
    try_thresholds
}

# --- sandbox ------------------------------------------------------------------

function test_release() {
    parallel=true
    reset_log
    timeout=5m
    model=("herman/orig" 2 0.60 0.75 0.15)
    choose_model "${model[@]}"
    cegar
    echo "^ should be at 15 and 19 sec"
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

function profiling() {
    reset_log

    timeout=10h
    # parallel=true
    # verbose=true

    model=("grid/orig" 40 0.019 0.019 0.15)

    # model=("grid/big" 40 0.928 0.931 0.003)
    # model=("maze/orig" 50 0.1612764 0.1612764 0.0000002)
    # model=("pole/orig" 5 0.735 0.735 0.001)
    # model=("dpm/orig" 12 0.080 0.080 0.002)
    # model=("herman/orig" 2 0.60 0.60 0.15)
    # model=("virus/orig" 0 0.1 0.9 0.1)

    # model=("herman/big" 6 0.98 0.98 0.3)

    choose_model "${model[@]}"

    # hybrid
    cegis
    # cegar
    # onebyone
}

function exploring_grid() {
    reset_log

    timeout=1h
    parallel=true
    # verbose=true
    
    model=("grid/big-exploring" 10 0.0714 0.0714 0.0001)
    # model=("grid/big-exploring" 10 7.6 7.7 0.1)
    
    # model=("grid/big-exploring-nobad" 10 0.1 0.9 0.1)
    # model=("grid/big-exploring-nobad" 10 9.4 /9.5 0.1)
    
    choose_model "${model[@]}"
    

    # hybrid
    # cegar
    cegis
}

function run() {
    reset_log

    timeout=1h
    parallel=true
    # verbose=true
    
    model=("grid/orig" 40 0.019 0.019 0.15)
    # model=("grid/big" 40 0.928 0.931 0.003)
    # model=("maze/orig" 50 0.1612764 0.1612764 0.0000002)
    # model=("pole/orig" 5 0.735 0.735 0.001)
    # model=("dpm/orig" 12 0.080 0.080 0.002)
    # model=("herman/orig" 2 0.60 0.60 0.15)

    # model=("herman/orig" 6 0.9254 0.9254 0.15)
    # model=("herman/orig-rew" 2 1.80 1.88 0.02)
    
    # model=("herman/553x_1_0" 0 1.8 2.2 0.2)
    # model=("herman/553x_1_0_m" 0 1 1 0.1)

    # model=("herman/553x_1_3_m_r" 3 0.57 0.57 0.1)
    # model=("herman/553x_1_3_m_p" 3 0.57 0.57 0.1)
    # model=("herman/553x_1_3_m_rp" 3 0.57 0.57 0.1)

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
    
    choose_model "${model[@]}"

    # hybrid
    cegar
    # cegis
    # onebyone
}

# ----------

# test_release
# tacas_performance

# profiling
# exploring_grid

run

exit

# --- halted -------------------------------------------------------------------

# --- CEGIS revisited ---

function cegis_virus_opt() {
    reset_log

    # primary_method=cegis
    OPTIMALITY="--optimality sketch.optimal"
    timeout=360h
    
    # parallel=true
    # verbose=true

    model=("cegis-copy/virus-opt" 0 1 1 1.0)
    choose_model "${model[@]}"
    
    cegis
    # cegar
    # onebyone
}

function cegis_virus() {
    # primary_method=cegis
    timeout=1m
    reset_log
    # parallel=true
    # verbose=true

    model=("cegis-copy/virus" 0 23 23 1.0)
    choose_model "${model[@]}"
    # onebyone
    cegis
    # cegar
}

function exploring_virus() {
    reset_log

    timeout=1h
    parallel=true
    # verbose=true
    
    # model=("virus/orig" 20 0.01 0.20 0.01)
    model=("virus/orig" 20 0.13 0.13 0.06)
    
    choose_model "${model[@]}"
    
    # hybrid
    cegar
    # cegis
}

function cegis_grid_big_opt() {
    reset_log

    # primary_method=cegis
    OPTIMALITY="--optimality sketch.optimal"
    timeout=1m

    # parallel=true
    verbose=true

    CMAX=4000
    
    model=("cegis-copy/grid-big-opt" ${CMAX} 1 1 1.0)
    choose_model "${model[@]}"

    cegis
    # cegar
    # onebyone
}

function cegis_grid() {
    timeout=120h
    reset_log
    parallel=true

    CMAX=10
    echo CMAX=${CMAX}
    model=("cegis-copy/grid" ${CMAX} 1 9 2.0)
    choose_model "${model[@]}"
    # cegis
    # onebyone
    wait

    CMAX=100
    echo CMAX=${CMAX}
    model=("cegis-copy/grid" ${CMAX} 10 90 20.0)
    choose_model "${model[@]}"
    # cegis
    # onebyone
    wait

    CMAX=1000
    echo CMAX=${CMAX}
    model=("cegis-copy/grid" ${CMAX} 100 900 200.0)
    choose_model "${model[@]}"
    # cegis
    # onebyone
    wait
    
    CMAX=4000
    echo CMAX=${CMAX}
    model=("cegis-copy/grid" ${CMAX} 400 3600 800.0)
    choose_model "${model[@]}"
    # cegis
    # onebyone
    wait

    CMAX=10000
    echo CMAX=${CMAX}
    model=("cegis-copy/grid" ${CMAX} 1000 9000 2000.0)
    choose_model "${model[@]}"
    # cegis
    # onebyone
    wait
    
    # cegis
    # onebyone
}

# beep bop
# paplay /usr/share/sounds/freedesktop/stereo/complete.oga
