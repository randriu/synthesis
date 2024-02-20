#!/bin/bash

source ../env/bin/activate
# timeout values for each experiment (recommended values: 20m and 5h)
export TIMEOUT_SMALL_MODELS=20m     # grid, maze, dpm, pole, herman, herman-2 (smaller)
export TIMEOUT_LARGE_MODELS=5h      # herman-2 (larger)

quick=""
if [ "$1" = "--quick" ]; then
    export TIMEOUT_SMALL_MODELS=5m
    quick="_quick"
fi

script_evaluate=experiment_evaluate${quick}.sh
script_summary=experiment_summary${quick}.sh
summary=summary${quick}.txt

# run experiments and process logs
printf "> starting experimental evaluation ...\n"
./${script_evaluate}
printf "> processing experiment logs ...\n"
./${script_summary} > ${summary}
cd ..
printf "> stats stored to file experiments/${summary}, printing it below:\n\n"
cat experiments/${summary}
