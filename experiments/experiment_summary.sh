#!/bin/bash

## helper functions ############################################################

function print_benchmark_info() {
    benchmark=$1
    logfile=$2

    number_of_holes="$(python3 parse_log.py ${logfile} number_of_holes)"
    family_size="$(python3 parse_log.py ${logfile} family_size)"
    mdp_size="$(python3 parse_log.py ${logfile} mdp_size)"
    dtmc_size="$(python3 parse_log.py ${logfile} dtmc_size)"
    
    printf "    %-20s%-20s%-20s%-20s%-20s\n" "${benchmark}" ${number_of_holes} ${family_size} ${mdp_size} ${dtmc_size}
}

function print_ce_stats() {
    benchmark=$1
    property=$2
    
    logfile=ce/${benchmark}_${property}_ce_maxsat_hybrid.txt
    ce_quality_maxsat="$(python3 parse_log.py ${logfile} ce_quality_maxsat)"
    ce_time_maxsat="$(python3 parse_log.py ${logfile} ce_time_maxsat)"
    
    logfile=ce/${benchmark}_${property}_ce_hybrid_hybrid.txt
    ce_quality_trivial="$(python3 parse_log.py ${logfile} ce_quality_trivial)"
    ce_time_trivial="$(python3 parse_log.py ${logfile} ce_time_trivial)"
    ce_quality_nontrivial="$(python3 parse_log.py ${logfile} ce_quality_nontrivial)"
    ce_time_nontrivial="$(python3 parse_log.py ${logfile} ce_time_nontrivial)"

    printf "    %-16s%-20s%-20s%-20s\n" "${benchmark} (${property})" "${ce_quality_maxsat} (${ce_time_maxsat})" "${ce_quality_trivial} (${ce_time_trivial})" ${ce_quality_nontrivial}
}


function print_performance_stats() {
    benchmark=$1
    printf "    %-16s" ${benchmark}
    for method in cegis cegar hybrid; do
        logfile=performance/${benchmark}_${property}_${method}.txt
        iters="$(python3 parse_log.py ${logfile} iters)"
        time="$(python3 parse_log.py ${logfile} time)"
        printf "%-20s%-20s" ${iters} ${time}
    done
    printf "\n"
}

function print_herman2_stats() {
    variant=$1
    for problem in $2 $3 $4; do
        printf "    %-16s" ${problem}
        for method in cegar hybrid; do
            logfile=herman2/herman2_${variant}_${problem}_${method}.txt
            iters="$(python3 parse_log.py ${logfile} iters)"
            time="$(python3 parse_log.py ${logfile} time)"
            printf "%-20s%-20s" ${iters} ${time}    
        done
        printf "\n"
    done
}

## parse all logs ##############################################################

small_models=( grid maze dpm pole herman )

# Table 1
printf "\nTable 1 (benchmark info)\n\n"
printf "%-24s%-20s%-20s%-20s%-20s\n" benchmark parameters "family size" "MDP size" "DTMC size"
for benchmark in "${small_models[@]}"; do
    print_benchmark_info ${benchmark} performance/${benchmark}_easy_hybrid.txt
done
print_benchmark_info "herman-2 (larger)" herman2/herman2_larger_5_hybrid.txt
printf "\n"

# Table 2 (counterexamples)
printf "Table 2 (counterexamples)\n\n"
printf "%-20s%-20s%-20s%-20s\n" benchmark maxsat trivial family
for benchmark in "${small_models[@]}"; do
    for property in easy hard; do
        print_ce_stats ${benchmark} ${property}
    done
done
printf "\n"

# Table 2 (performance)
printf "Table 2 (performance)\n\n"
printf "%-20s%-20s%-20s%-20s%-20s%-20s%-20s%-20s\n" benchmark cegis_iters cegis_time cegar_iters cegar_time hybrid_iters hybrid_time
for benchmark in "${small_models[@]}"; do
    for property in easy hard; do
        print_performance_stats ${benchmark} ${property}
    done
done
printf "\n"

# Table 3 (Herman-2)

printf "Table 3 (herman-2, smaller)\n\n"
printf "%-20s%-20s%-20s%-20s%-20s\n" problem cegar_iters cegar_time hybrid_iters hybrid_time
print_herman2_stats smaller feasibility multiple 0
printf "\n"

printf "Table 3 (herman-2, larger)\n\n"
printf "%-20s%-20s%-20s%-20s%-20s\n" problem cegar_iters cegar_time hybrid_iters hybrid_time
print_herman2_stats larger feasibility 0 5
printf "\n"

onebyone_time="$(python3 parse_log.py herman2/*onebyone.txt time)"
printf "1-by-1 on herman-2 (larger): %s sec\n" ${onebyone_time}
printf "\n"

