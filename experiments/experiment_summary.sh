#!/bin/bash

## parse all logs ##############################################################

benchmarks=( dpm maze herman pole grid )

# Table 1
printf "\nTable 1 \n\n"
printf "%-22s%-16s%-16s%-16s%-16s%-16s%-16s\n" model "parameters" "family size" "avg. MC size" "1-by-1" "hybrid (hard)" "hybrid (easy)"
for benchmark in "${benchmarks[@]}"; do

    log_onebyone=logs/onebyone/${benchmark}*.txt
    log_hybrid_hard=logs/hybrid_hard/${benchmark}*.txt
    log_hybrid_easy=logs/hybrid_easy/${benchmark}*.txt

    number_of_holes="$(python3 parse_log.py ${log_hybrid_easy} number_of_holes)"
    family_size="$(python3 parse_log.py ${log_hybrid_easy} family_size)"
    dtmc_size="$(python3 parse_log.py ${log_hybrid_easy} dtmc_size)"

    onebyone_time="$(python3 parse_log.py ${log_onebyone} time)"
    hybrid_hard_time="$(python3 parse_log.py ${log_hybrid_hard} time)"
    hybrid_easy_time="$(python3 parse_log.py ${log_hybrid_easy} time)"

    printf "    %-18s%-16s%-16s%-16s%-16s%-16s%-16s\n" "${benchmark}" ${number_of_holes} ${family_size} ${dtmc_size} ${onebyone_time} ${hybrid_hard_time} ${hybrid_easy_time}
done
printf "\n"


