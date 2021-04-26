#!/bin/bash

# implicit synthesis timeout
timeout=0
if [ -n "$1"]; then
    timeout=$1
fi

# setting this value to >1 will enable concurrent evaluation of experiments
threads=4

# run experiments
printf "> starting experimental evaluation ...\n"
./experiment_evaluate.sh ${timeout} ${threads}

# process logs into a summary
printf "> processing experiment logs ...\n"
./experiment_summary.sh > logs/summary.txt

# print summary
printf "> stats stored to file logs/summary.txt, printing it below:\n\n"
cat logs/summary.txt
