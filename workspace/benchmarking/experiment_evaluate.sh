#!/bin/bash

timeout=5s
if [ -n "$1" ]; then
    timeout=$1
fi

threads=$(nproc)
if [ -n "$2" ]; then
    threads=$2
fi

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

    # create folder for this experiment
    local experiment_set=$1
    mkdir -p logs/${experiment_set}
    
    local benchmark=$2
    local logfile="logs/${experiment_set}/${benchmark}.txt"

    # collect other arguments
    local project="--project ${benchmarks_dir}/${benchmark}"
    local method=$3
    local pomdp="--pomdp-memory-size=${pomdp_mem_size}"
    local timeout=$4
    
    ((experiment_current+=1))
    echo "experiment ${experiment_current}/${experiments_total}: ${benchmark}, method: ${method}"
    # timeout ${timeout} python3 $PAYNT_DIR/paynt.py ${project} ${property} ${method} ${pomdp} > ${logfile} || echo "TO" >> ${logfile} &
    timeout ${timeout} python3 $PAYNT_DIR/paynt.py ${project} ${property} ${method} ${pomdp} > ${logfile} &
}

## experiment section ##########################################################


# benchmark setup

# benchmarks=( dpm maze herman pole grid )
# experiments_total=5

benchmarks_dir="$SYNTHESIS/workspace/examples/pomdp/voihp"
experiments_total=`ls $benchmarks_dir/ | wc -l`

# create folder for log files
mkdir -p logs

# activate environment
source $SYNTHESIS_ENV/bin/activate

## experiments

method=ar
pomdp_mem_size=1

echo "-- evaluating "
# for benchmark in "${benchmarks[@]}"; do
for k in {1..4}; do
    experiment_current=0
    echo "-- k=$k"
    pomdp_mem_size=$k
    experiment_name="ar-k=${k}-cold"
    for benchmark in `ls $benchmarks_dir`; do
        paynt "${experiment_name}" "${benchmark}" ${method} ${timeout}
    done
done
# wait for the remaining experiments to finish
wait
echo "-- all experiments finished"

# deactivate environment
deactivate

# done
