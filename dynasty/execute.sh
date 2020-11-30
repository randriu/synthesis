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

# preset candidates
mazexxl=("maze/xxl" 50 0.1 0.1 0.1)

# exploring herman
CMAX=6
herbig=("herman/2m-go1" ${CMAX} 0.95 0.95 0.3)
herbigfix=("herman/2m-go1-fixed" ${CMAX} 0.95 0.95 0.3)

# workspace settings
examples_dir="workspace/examples"
log_dir="workspace/log"
parameters_file="${log_dir}/parameters.txt"
log_file="${log_dir}/log_${core}.txt"
log_grep_file="${log_dir}/log_grep_${core}.txt"

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
    dynasty="python dynasty.py ${dynasty_opts} ${primary_method}"
    timeout ${timeout} ${dynasty} --constants "CMAX=${cmax},THRESHOLD=${threshold}"
    # timeout ${timeout} ${dynasty} --constants "CMAX=${cmax},THRESHOLD=${threshold}" --restrictions sketch.restrictions ${OPTIMALITY}
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

function tacas_performance() {
    reset_log

    timeout=5m
    # parallel=true
    # verbose=true

    grid=("grid/orig" 40 0.004 0.019 0.015)
    gridbig=("grid/big" 40 0.928 0.931 0.003)
    maze=("maze/orig" 50 0.1612764 0.1612766 0.0000002)
    dpm=("dpm/orig" 12 0.078 0.080 0.002)
    pole=("pole/orig" 5 0.732 0.735 0.003)
    herman=("herman/orig" 2 0.60 0.75 0.15)

    # models=("grid" "gridbig" "maze" "dpm" "pole" "herman")
    models=("grid" "maze" "dpm" "pole" "herman")

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
    
    hybrid
    # cegar
}

function profiling() {
    reset_log

    timeout=10h
    # parallel=true
    # verbose=true

    # model=("grid/orig" 40 0.019 0.019 0.15)
    # model=("grid/big" 40 0.928 0.931 0.003)
    # model=("maze/orig" 50 0.1612764 0.1612764 0.0000002)
    # model=("herman/orig" 2 0.60 0.60 0.15)
    # model=("pole/orig" 5 0.735 0.735 0.001)
    # model=("dpm/orig" 12 0.080 0.080 0.002)
    # model=("herman/2m-go1-fixed" 6 0.98 0.98 0.3)

    model=("pole/orig" 5 0.735 0.735 0.001)

    choose_model "${model[@]}"

    hybrid
    # cegis
    # cegar
    # onebyone
}

function test_release() {
    parallel=true
    reset_log
    timeout=5m
    model=("herman/orig" 2 0.60 0.75 0.15)
    choose_model "${model[@]}"
    cegar
    echo "^ should be at 15 and 19 sec"
}



# rewards_grid
# tacas_performance

profiling

# exploring_grid

# test_release

exit

# --- halted -------------------------------------------------------------------

function run() {

    reset_log
    timeout=40s
    # parallel=true
    
    choose_model "${herman[@]}"
    # choose_model "${gridbig[@]}"
    # choose_model "${maze[@]}"
    # choose_model "${mazexxl[@]}"
    # choose_model "${pole[@]}"
    # choose_model "${dpm[@]}"
    # choose_model "${herman[@]}"

    model=("herman/orig" 2 0.60 0.75 0.15)

    choose_model "${model[@]}"

    # cegis
    # cegar
    hybrid
}

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

function cegis_grid_big() {
    reset_log

    timeout=1h
    # parallel=true
    # verbose=true

    CMAX=4000
    T_MIN=1000
    T_MAX=1000
    T_STEP=200.0

    model=("cegis-copy/grid-big" ${CMAX} ${T_MIN} ${T_MAX} ${T_STEP})
    choose_model "${model[@]}"

    # cegis
    # cegar
    onebyone
    # wait
}

function cegis_grid() {
    reset_log

    timeout=1m
    parallel=true
    # verbose=true

    CMAX=100
    T_MIN=0.99
    T_MAX=1.0
    T_STEP=0.01

    model=("cegis-copy/grid" ${CMAX} ${T_MIN} ${T_MAX} ${T_STEP})
    choose_model "${model[@]}"

    cegis
    # cegar
    # onebyone
    # wait
}

function cegis_dpm() {
    reset_log

    # primary_method=cegis
    # OPTIMALITY="--optimality sketch.optimal"
    timeout=1m

    # parallel=true
    # verbose=true
    
    CMAX=10
    # THRESHOLD=1.0
    model=("cegis-copy/dpm" ${CMAX} 0.008 0.008 0.001)
    choose_model "${model[@]}"
    
    # cegis
    # cegar
    # try_thresholds

    onebyone
}

function test_parallel_run() {
    processes=$1
    for job in `seq $processes`; do
        cegar
    done;
    wait
}

function test_parallel() {
    reset_log

    timeout=10m
    parallel=true
    
    model=("herman/orig" 2 0.60 0.60 0.15)
    choose_model "${model[@]}"

    for processes in `seq 1 1 16`; do
        echo "> $processes"
        time test_parallel_run $processes
    done

    # hybrid
}



# beep bop
# paplay /usr/share/sounds/freedesktop/stereo/complete.oga
