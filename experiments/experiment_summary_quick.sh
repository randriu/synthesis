#!/bin/bash

## parse all logs ##############################################################

small_models=( grid maze dpm pole herman )

# Table 2
printf "Table 2: counterexamples (hybrid), performance of cegar/hybrid on a basic benchmark\n\n"
printf "%-20s%-20s%-20s%-20s%-20s%-20s%-20s\n" benchmark ce_trivial ce_family cegar_iters cegar_time hybrid_iters hybrid_time
for benchmark in "${small_models[@]}"; do
    for property in easy hard; do
        logfile=logs/ce/${benchmark}_${property}_ce_hybrid_hybrid.txt
        ce_quality_trivial="$(python3 parse_log.py ${logfile} ce_quality_trivial)"
        ce_time_trivial="$(python3 parse_log.py ${logfile} ce_time_trivial)"
        ce_quality_nontrivial="$(python3 parse_log.py ${logfile} ce_quality_nontrivial)"
        ce_time_nontrivial="$(python3 parse_log.py ${logfile} ce_time_nontrivial)"
        printf "    %-16s%-20s%-20s" "${benchmark} (${property})" "${ce_quality_trivial} (${ce_time_trivial})" ${ce_quality_nontrivial}

        for method in cegar hybrid; do
            logfile=logs/performance/${benchmark}_${property}_${method}.txt
            iters="$(python3 parse_log.py ${logfile} iters)"
            time="$(python3 parse_log.py ${logfile} time)"
            printf "%-20s%-20s" ${iters} ${time}
        done
        printf "\n"
    done
done
printf "\n"
