#!/bin/bash

# presets
def=("pole-safety" 3 0.32 0.32 0.02)

gs=("grid-safety" 40 0.01 0.11 0.02)
gl=("grid-liveness" 40 0.89 0.99 0.02)
ms=("maze-safety" 50 0.16 0.26 0.02)
ml=("maze-liveness" 50 0.74 0.84 0.02)
ps=("pole-safety" 5 0.73 0.83 0.02)
pl=("pole-liveness" 5 0.25 0.35 0.02)
dpm=("dpm" 12 0.003 0.013 0.002)
her=("herman" 2 0.52 0.62 0.02)

# singular & small
gs1=("grid-safety" 40 0.03 0.03 0.02)
ms1=("maze-safety" 50 0.1612766 0.1612766 0.0000001)
ps1=("pole-safety" 5 0.735 0.735 0.005)
her1=("herman" 2 0.58 0.58 0.02)

small=("small" 50 0.3 0.3 0.02)
mss=("maze-safety" 5 0.1 0.9 0.1)
gss=("grid-safety" 10 0.01 0.01 0.02)
ms2=("maze-safety" 50 0.20 0.20 0.02)
# msl=("maze-liveness" 20 0.1 0.9 0.4)

# unfeasible
gsu=("grid-safety" 40 0.001 0.022 0.003)
msu=("maze-safety" 50 0.16127635 0.16127665 0.00000005)
heru=("herman" 2 0.52 0.62 0.02)
psu=("pole-safety" 5 0.731 0.737 0.001)
dpmu=("dpm" 12 0.001 0.009 0.001)

# unfeasible - singular
msu1=("maze-safety" 50 0.16127665 0.16127665 0.00000005)
psu1=("pole-safety" 5 0.732 0.732 0.001)
gsu1=("grid-safety" 40 0.007 0.007 0.003)
heru1=("herman" 2 0.58 0.58 0.05)

# debuggin hole exploration
msd=("maze-safety" 2 0.2 0.2 0.1) # 2 0.2
gsd=("grid-safety" 40 0.03 0.03 0.02)
dpmd=("dpm" 12 0.009 0.009 0.002)

# basic settings
regime=2
primary_method=research
preset=("${heru[@]}")
time_limit=1200

# hybrid method parameters
score_limit=20

# explore parameters
# l_min=1
# l_max=40
# l_step=2

# e_min=1
# e_max=65
# e_step=2

# workspace settings
workspace="workspace"
examples_dir="${workspace}/examples"
experiments_dir="${workspace}/experiments"
parameters_file="${experiments_dir}/parameters.txt"
log_file="${experiments_dir}/log.txt"
log_grep_file="${experiments_dir}/log_grep.txt"

# functions

function log_output() {
    while read input; do
        echo ${input} | tee --append ${log_file} | grep "> " | tee --append ${log_grep_file}
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
    timeout ${time_limit}s ${dynasty} --constants "CMAX=${cmax},THRESHOLD=${threshold}"
    # ${dynasty} --constants "CMAX=${cmax},THRESHOLD=${threshold}"
}

function try_thresholds() {
    for threshold in `seq ${t_min} ${t_step} ${t_max}`; do
        echo "> T = ${threshold}" | log_output
        dynasty | log_output
    done
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

# reset files
choose_model "${preset[@]}"
echo "" > ${log_file}
echo "" > ${log_grep_file}
write_params


# experiments section
# cegis
# cegar
hybrid
exit

# iterate over all models
echo "> gs"
choose_model "${gs[@]}"
# cegis; cegar
hybrid

echo "> gl"
choose_model "${gl[@]}"
# cegis; cegar
hybrid

echo "> ms"
choose_model "${ms[@]}"
# cegis; cegar
hybrid

echo "> ml"
choose_model "${ml[@]}"
# cegis; cegar
hybrid

echo "> ps"
choose_model "${ps[@]}"
# cegis; cegar
hybrid

echo "> pl"
choose_model "${pl[@]}"
# cegis; cegar
hybrid

echo "> dpm"
choose_model "${dpm[@]}"
# cegis; cegar
hybrid

echo "> her"
choose_model "${her[@]}"
# cegis; cegar
hybrid

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
