#!/bin/bash

# presets
grid=("grid/orig" 40 0.004 0.019 0.003)
gridbig=("grid/big" 40 0.927 0.931 0.001)
maze=("maze/orig" 50 0.16127640 0.16127660 0.00000005)
pole=("pole/orig" 5 0.732 0.736 0.001)
dpm=("dpm/orig" 12 0.078 0.081 0.001)
herman=("herman/orig" 2 0.60 0.75 0.05)

# candidates
mazexxl=("maze/xxl" 50 0.1 0.1 0.1)

# exploring herman
CMAX=6
herbig=("herman/2m-go1" ${CMAX} 0.98433 0.98433 0.3)
herbigfix=("herman/2m-go1-foxed" ${CMAX} 0.905 0.905 0.3)

# cegis - extended


# basic settings
regime=2
# primary_method=cschedenum
primary_method=research

# main parameters
preset=("${psu[@]}")
timeout=24h
score_limit=999999

# workspace settings
workspace="workspace"
examples_dir="${workspace}/examples"
experiments_dir="${workspace}/experiments"
parameters_file="${experiments_dir}/parameters.txt"
log_file="${experiments_dir}/log.txt"
log_grep_file="${experiments_dir}/log_grep.txt"

# explore parameters
# l_min=1
# l_max=40
# l_step=2

# e_min=1
# e_max=65
# e_step=2

# functions

function log_output() {
    while read input; do
        echo ${input} | tee --append ${log_file} | grep "^> " | tee --append ${log_grep_file}
        # echo ${input}
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
    # echo $subchains_checked_limit >> $parameters_file
}

function dynasty() {
    dynasty_opts="--project ${examples_dir}/${model}/ --sketch sketch.templ --allowed sketch.allowed --properties sketch.properties"
    dynasty="python dynasty.py ${dynasty_opts} ${primary_method}"
    timeout ${timeout} ${dynasty} --constants "CMAX=${cmax},THRESHOLD=${threshold}"
    # ${dynasty} --constants "CMAX=${cmax},THRESHOLD=${threshold}"
}

function try_thresholds() {
    for threshold in `seq ${t_min} ${t_step} ${t_max}`; do
        echo "> T = ${threshold}" | log_output
        dynasty | log_output
    done
}

reset_log() {
    echo "" > ${log_file}
    echo "" > ${log_grep_file}
    write_params
    
}

function cegis() {
    regime=1
    write_params
    try_thresholds
}

function cegar() {
    regime=2
    write_params
    try_thresholds
}

function hybrid() {
    regime=3
    write_params
    try_thresholds
}

function run(){
    timeout=12h
    score_limit=999999
    # CMAX=6
    reset_log
    
    # choose_model "${grid[@]}"
    # choose_model "${gridbig[@]}"
    # choose_model "${maze[@]}"
    # choose_model "${mazexxl[@]}"
    # choose_model "${pole[@]}"
    # choose_model "${dpm[@]}"
    # choose_model "${herman[@]}"

    # model=("maze/xxl" 50 0.5 0.5 0.1)

    CMAX=6
    model=("herman/2m-go1-fixed" ${CMAX} 0.905 0.905 0.3)

    choose_model "${model[@]}"
    # cegis
    # cegar
    hybrid
}


function counterexamples(){
    timeout=1h
    reset_log

    echo ""; echo "> grid"
    choose_model "${grid[@]}"
    # hybrid

    echo ""; echo "> maze"
    choose_model "${maze[@]}"
    # hybrid

    echo ""; echo "> pole"
    choose_model "${pole[@]}"
    # hybrid
    
    echo ""; echo "> herman"
    choose_model "${herman[@]}"
    # hybrid
}

function performance() {
    timeout=1h
    score_limit=999999
    reset_log

    echo ""; echo "> ----- grid"
    choose_model "${grid[@]}"
    # cegis
    # cegar
    hybrid

    echo ""; echo "> ----- grid-big"
    choose_model "${gridbig[@]}"
    # cegis
    # cegar
    hybrid

    echo ""; echo "> ----- maze"
    choose_model "${maze[@]}"
    # cegis
    # cegar
    hybrid

    echo ""; echo "> ----- pole"
    choose_model "${pole[@]}"
    # cegis
    # cegar
    hybrid

    echo ""; echo "> ----- dpm"
    choose_model "${dpm[@]}"
    # cegis
    # cegar
    hybrid

    echo ""; echo "> ----- herman"
    choose_model "${herman[@]}"
    # cegis
    # cegar
    hybrid
}

run
# counterexamples
# performance

exit

# beep bop
# paplay /usr/share/sounds/freedesktop/stereo/complete.oga
