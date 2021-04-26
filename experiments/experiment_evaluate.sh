#!/bin/bash

timeout=1s
if [ -n "$1" ]; then
    timeout=$1
fi

threads=1
if [ -n "$2" ]; then
    threads=$2
fi

# experiment counters
experiment_current=0
experiment_total=15

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

# ryn paynt on a given model/property via a selected method (onebyone, cegis, cegar, hybrid)
function paynt() {
    experiments_wait ${threads}

    local experiment_set=$1

    local benchmark=$2
    local project="--project ../cav21-benchmark/${benchmark}"

    local property=$3
    property="--properties ${property}.properties"
    
    local method=$4
    
    local timeout=$5
    local logfile="../experiments/logs/${experiment_set}/${benchmark}_${method}.txt"
    
    ((experiment_current+=1))
    echo "experiment ${experiment_current}/${experiment_total}: ${benchmark}, method: ${method}"
    timeout ${timeout} python paynt.py ${project} ${property} ${method} > ${logfile} || echo "TO" >> ${logfile} &
}

## experiment section ##########################################################

benchmarks=( dpm maze herman pole grid )

# create folders for log files
mkdir -p logs logs/onebyone logs/hybrid_hard logs/hybrid_easy

# activate environment
source ../env/bin/activate

# navigate to paynt
cd ../paynt

## 1-by-1 enumeration

echo "-- evaluating 1-by-1 enumeration"
for benchmark in "${benchmarks[@]}"; do
    paynt onebyone "${benchmark}" "hard" "onebyone" "${timeout}"
done

echo "-- evaluating hybrid method (hard)"
for benchmark in "${benchmarks[@]}"; do
    paynt hybrid_hard "${benchmark}" "hard" "hybrid" "${timeout}"
done

echo "-- evaluating hybrid method (easy)"
for benchmark in "${benchmarks[@]}"; do
    paynt hybrid_easy "${benchmark}" "easy" "hybrid" "${timeout}"
done

# wait for the remaining experiments to finish
wait
echo "-- all experiments finished"

# navigate back to root folder
cd -

# deactivate environment
deactivate

# done
