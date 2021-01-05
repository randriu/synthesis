#!/bin/bash

## settings ####################################################################

TIMEOUT_BASIC=${EXPERIMENT_TIMEOUT_BASIC}
TIMEOUT_LARGE=${EXPERIMENT_TIMEOUT_LARGE}
CORES=${EXPERIMENT_CORES}

## helper functions ############################################################

# sample command:
# python3 dynasty.py --project workspace/tacas21/grid/ --properties easy.properties hybrid --regime 3

# experiment counters
experiment_current=0
experiment_total=59

# wait until the number of child processes is at most the number of available cores
function experiments_wait() {
    local cores=$1
    children=$(pgrep -c -P$$)

    while [ ${cores} -le ${children} ]; do
        wait -n 1
        children=$(pgrep -c -P$$)
    done
}

# convert selected synthesis method to regime index
function method_to_regime() {
    local method=$1
    if [ $method == "onebyone" ]; then
        echo 0
    elif [ $method == "cegis" ]; then
        echo 1
    elif [ $method == "cegar" ]; then
        echo 2
    elif [ $method == "hybrid" ]; then
        echo 3
    else
        echo "unknown synthesis method"
        exit 1
    fi
}

# ryn dynasty on a given model/property via a selected method (onebyone, cegis, cegar, hybrid)
function dynasty() {
    experiments_wait ${CORES}

    local timeout=$1
    local experiment_name=$2
    local model=$3
    local property=$4
    local method=$5
    local regime="$(method_to_regime ${method})"
    local logfile="../experiments/${experiment_name}/${model}_${property}_${method}.txt"
    local extra_option_1=$6
    local extra_option_2=$7
    
    ((experiment_current+=1))
    echo "experiment ${experiment_current}/${experiment_total}: ${model} (${property}), method: ${method} (${extra_option_1} ${extra_option_2})"
    timeout ${timeout} python dynasty.py --project workspace/tacas21/${model} --properties ${property}.properties hybrid --regime ${regime} --check-prerequisites ${extra_option_1} ${extra_option_2} > ${logfile} || echo "TO" >> ${logfile} &
}

# evaluate five models from the basic benchmark using a selected method
function evaluate_basic_benchmark() {
    local experiment_name=$1
    local method=$2
    local options=$3
    local models=( grid maze dpm pole herman )
    for model in "${models[@]}"; do
        dynasty ${TIMEOUT_BASIC} ${experiment_name} ${model} easy ${method} ${options}
        dynasty ${TIMEOUT_BASIC} ${experiment_name} ${model} hard ${method} ${options}
    done
}

## experiment section ##########################################################

# create folders for log files
mkdir -p basic
mkdir -p ce ce/quality ce/maxsat
mkdir -p large_model large_model/feasibility large_model/multiple large_model/optimality_0 large_model/optimality_5

# activate python environment and navigate to dynasty
source ../env/bin/activate
cd ../dynasty

# evaluate cegis/cegar/hybrid on a basic benchmark
echo "-- evaluating basic benchmark (cegis)"
evaluate_basic_benchmark basic cegis
echo "-- evaluating basic benchmark (cegar)"
evaluate_basic_benchmark basic cegar
echo "-- evaluating basic benchmark (hybrid)"
evaluate_basic_benchmark basic hybrid

# evaluate CE quality on the same benchmark
echo "-- evaluating CE quality (hybrid)"
evaluate_basic_benchmark ce/quality hybrid "--ce-quality"
echo "-- evaluating CE quality (maxsat)"
evaluate_basic_benchmark ce/maxsat hybrid "--ce-quality --ce-maxsat"

# large model experiments

# estimate 1-by-1 enumeration on optimality (0%)
echo "-- evaluating large model"
dynasty ${TIMEOUT_LARGE} large_model/optimality_0 herman_large none onebyone "--optimality 0.optimal"
children=$(pgrep -c -P$$)

# evaluate cegar and hybrid
methods=( cegar hybrid )
for method in "${methods[@]}"; do
    regime="$(method_to_regime ${method})"
    dynasty ${TIMEOUT_LARGE} large_model/feasibility herman_large feasibility ${method}
    dynasty ${TIMEOUT_LARGE} large_model/multiple herman_large multiple ${method}
    dynasty ${TIMEOUT_LARGE} large_model/optimality_0 herman_large none ${method} "--optimality 0.optimal"
    dynasty ${TIMEOUT_LARGE} large_model/optimality_5 herman_large none ${method} "--optimality 5.optimal"
done

# wait for remaining experiments to finish
wait

# deactivate python environment and navigate to root folder
deactivate
cd $OLDPWD

# done
