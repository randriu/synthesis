#!/bin/bash

# sample command:
# python3 dynasty.py --project workspace/tacas21/grid/ --properties easy.properties hybrid --regime 3

# timeout values for each experiment
export EXPERIMENT_TIMEOUT_BASIC=2s  # grid/maze/dpm/pole/herman
export EXPERIMENT_TIMEOUT_LARGE=10s  # herman L

# setting this value to >1 will enable concurrent running of experiments
export EXPERIMENT_CORES=8

# run experiments and process logs
echo "> starting experimental evaluation ..."
cd experiments
. experiment_run.sh
echo "> all experiments finished, collecting stats ..."
. experiment_summary.sh > summary.txt
cd ..
echo "> stats stored to experiments/summary.txt"
# cat experiments/summary.txt
