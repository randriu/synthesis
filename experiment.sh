#!/bin/bash

# timeout values for each experiment (recommended values: 20m and 5h)
export TIMEOUT_SMALL_MODELS=20m     # grid, maze, dpm, pole, herman, herman-2 (smaller)
export TIMEOUT_LARGE_MODELS=5h      # herman-2 (larger)

# run experiments and process logs
printf "> starting experimental evaluation ...\n"
cd experiments
./experiment_run.sh
printf "> processing experiment logs ...\n"
./experiment_summary.sh > summary.txt
cd ..
printf "> stats stored to file experiments/summary.txt, printing it below:\n\n"
cat experiments/summary.txt
