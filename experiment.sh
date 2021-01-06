#!/bin/bash

# sample command:
# python3 dynasty.py --project workspace/tacas21/grid/ --properties easy.properties hybrid

# timeout values for each experiment (recommended values: 30m and 6h)
export TIMEOUT_SMALL_MODELS=30s     # grid, maze, dpm, pole, herman, herman-2 (smaller)
export TIMEOUT_LARGE_MODELS=30s     # herman-2 (larger)

# run experiments and process logs
printf "> starting experimental evaluation ...\n"
cd experiments
./experiment_run.sh
printf "> processing experiment logs ...\n"
./experiment_summary.sh > summary.txt
cd ..
printf "> stats stored to file experiments/summary.txt, printing it below:\n\n"
cat experiments/summary.txt
