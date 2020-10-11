#!/bin/bash

# todo
# cegis for superfamily
# lazy mapping
# rewarding cegis

# presets
def=("pole-safety" 3 0.32 0.32 0.02)
small=("small" 50 0.3 0.3 0.02)

# gs=("grid-safety" 40 0.01 0.11 0.02)
# gl=("grid-liveness" 40 0.89 0.99 0.02)
# ms=("maze-safety" 50 0.16 0.26 0.02)
# ml=("maze-liveness" 50 0.74 0.84 0.02)
# ps=("pole-safety" 5 0.73 0.83 0.02)
# pl=("pole-liveness" 5 0.25 0.35 0.02)
# dpm=("dpm" 12 0.003 0.013 0.002)
# her=("herman/herman-old" 2 0.52 0.62 0.02)

# unfeasible
gsu=("grid-safety" 40 0.001 0.022 0.003)
msu=("maze-safety" 50 0.16127635 0.16127665 0.00000005)
psu=("pole-safety" 5 0.731 0.737 0.001)
heru=("herman/herman-old" 2 0.55 0.80 0.05)
heru=("herman/herman-old" 2 0.7 0.7 0.05)
dpmu=("dpm-new" 12 0.1 0.9 0.2)
dpmnu=("dpm-new" 12 0.99442 0.99442 0.00001)
    
# unfeasible - singular
# gsu1=("grid-safety" 40 0.007 0.007 0.003)
# msu1=("maze-safety" 50 0.16127650 0.16127650 0.00000005)
# psu1=("pole-safety" 5 0.736 0.736 0.001)
# heru1=("herman" 2 0.58 0.58 0.05)

# exploring herman
CMAX=6
her=("herman/herman-old" ${CMAX} 0.9 0.9 0.1) # mdp: 54k, 0.5 T - 0.6 F
herseb=("herman/herman-seb" ${CMAX} 0.9 0.90 0.05)
hersebgo=("herman/herman-seb-go1" ${CMAX} 0.99 0.99 0.3)

# basic settings
regime=2
# primary_method=cschedenum
primary_method=research

# main parameters
preset=("${psu[@]}")
timeout=120
score_limit=5

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
    timeout ${timeout}s ${dynasty} --constants "CMAX=${cmax},THRESHOLD=${threshold}"
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
    timeout=7200
    reset_log
    choose_model "${heru[@]}"
    # cegis
    # cegar
    hybrid

    exit
}

function unfeasible() {
    timeout=600
    reset_log

    echo ""; echo "> gsu"
    choose_model "${gsu[@]}"
    # cegis
    # cegar
    # hybrid

    echo ""; echo "> msu"
    choose_model "${msu[@]}"
    # cegis
    # cegar
    # hybrid

    echo ""; echo "> psu"
    choose_model "${psu[@]}"
    # cegis
    # cegar
    # hybrid

    echo ""; echo "> heru"
    choose_model "${heru[@]}"
    # cegis
    # cegar
    # hybrid

    exit
}

run
# unfeasible
exit

# beep bop
# paplay /usr/share/sounds/freedesktop/stereo/complete.oga

# if [ $regime -eq 0 ] # simple execution
# then
#     dynasty
#     exit
# elif [ $regime -eq 1 ] # explore threshold: cegis
# then
#     cegis
# elif [ $regime -eq 2 ] # explore threshold: cegar
# then
#     cegar
# elif [ $regime -eq 3 ] # explore threshold (cegis, cegar)
# then
#     hybrid
# elif [ $regime -eq 3 ] # explore cegar iterations limit
# then
#     for cegar_iters_limit in `seq ${l_min} ${l_step} ${l_max}`; do
#         echo "> L = ${cegar_iters_limit}"  | log_output
#         write_params
#         dynasty | log_output
#     done
# elif [ $regime -eq 3 ] # explore expanded per iter
# then
#     for cegis_expanded_per_iter in `seq ${e_min} ${e_step} ${e_max}`; do
#         echo "> E = ${cegis_expanded_per_iter}"  | log_output
#         write_params
#         dynasty | log_output
#     done
# else
#     echo "what"
# fi

# subl ${log_file}
# subl ${log_grep_file}
