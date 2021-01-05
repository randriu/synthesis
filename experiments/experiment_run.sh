#!/bin/bash

# experiment counters
experiment_current=0
experiment_total=63

## helper functions ############################################################

# wait until the number of child processes is at most the number of available cores
function experiments_wait() {
    local cores=$1
    children=$(pgrep -c -P$$)

    while [ ${cores} -le ${children} ]; do
        wait -n 1
        children=$(pgrep -c -P$$)
    done
}

# ryn dynasty on a given model/property via a selected method (onebyone, cegis, cegar, hybrid)
function dynasty() {
    experiments_wait ${THREADS}

    local timeout=$1
    local experiment_name=$2
    local model=$3
    local property=$4
    local method=$5
    local logfile="../experiments/${experiment_name}/${model}_${property}_${method}.txt"
    local extra_option_1=$6
    local extra_option_2=$7
    
    ((experiment_current+=1))
    echo "experiment ${experiment_current}/${experiment_total}: ${model} (${property}), method: ${method} (${extra_option_1} ${extra_option_2})"
    timeout ${timeout} python3 dynasty.py --project ../tacas21-benchmark/${model} --properties ${property}.properties ${method} ${extra_option_1} ${extra_option_2} > ${logfile} || echo "TO" >> ${logfile} &
}

# evaluate five models from the basic benchmark using a selected method
function evaluate_basic_benchmark() {
    local experiment_name=$1
    local method=$2
    local options=$3
    local models=( grid maze dpm pole herman )
    for model in "${models[@]}"; do
        dynasty ${TIMEOUT_SMALL_MODELS} ${experiment_name} ${model} easy ${method} ${options}
        dynasty ${TIMEOUT_SMALL_MODELS} ${experiment_name} ${model} hard ${method} ${options}
    done
}

## experiment section ##########################################################

# create folders for log files
mkdir -p basic ce large_model
mkdir -p ce/quality ce/maxsat
mkdir -p large_model/herman2_smaller large_model/herman2_larger
mkdir -p large_model/herman2_smaller/feasibility large_model/herman2_smaller/multiple large_model/herman2_smaller/optimality_0
mkdir -p large_model/herman2_larger/feasibility large_model/herman2_larger/optimality_0 large_model/herman2_larger/optimality_5 large_model/herman2_larger/onebyone

# activate python environment and navigate to dynasty
source ../env/bin/activate
cd ../dynasty

## experiments on a basic benchmark (Table 2)

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

## experiments with a large model (Table 3)

# evaluate smaller and larger variant of Herman using cegar and hybrid
methods=( cegar hybrid )
echo "-- evaluating herman2-smaller (cegar, hybrid)"
for method in "${methods[@]}"; do
    dynasty ${TIMEOUT_LARGE_MODELS} large_model/herman2_smaller/feasibility herman2_smaller feasibility ${method}
    dynasty ${TIMEOUT_LARGE_MODELS} large_model/herman2_smaller/multiple herman2_smaller multiple ${method}
    dynasty ${TIMEOUT_LARGE_MODELS} large_model/herman2_smaller/optimality_0 herman2_smaller none ${method} "--optimality 0.optimal"
done
echo "-- evaluating herman2-larger (cegar, hybrid, 1-by-1)"
for method in "${methods[@]}"; do
    dynasty ${TIMEOUT_LARGE_MODELS} large_model/herman2_larger/feasibility herman2_larger feasibility ${method}
    dynasty ${TIMEOUT_LARGE_MODELS} large_model/herman2_larger/optimality_0 herman2_larger none ${method} "--optimality 0.optimal"
    dynasty ${TIMEOUT_LARGE_MODELS} large_model/herman2_larger/optimality_5 herman2_larger none ${method} "--optimality 5.optimal"
done
# estimate 1-by-1 enumeration on optimality (0%)
dynasty ${TIMEOUT_LARGE_MODELS} large_model/herman2_larger/optimality_0 herman2_larger none onebyone "--optimality 0.optimal"
children=$(pgrep -c -P$$)

# wait for the remaining experiments to finish
wait
echo "-- all experiments finished"

# deactivate python environment and navigate to root folder
deactivate
cd $OLDPWD

# done
