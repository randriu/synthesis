#!/bin/bash

## helper functions ############################################################

function print_benchmark_info() {
    benchmark_name=$1
    logfile=$2

    number_of_holes="$(python3 parse_log.py ${logfile} number_of_holes)"
    family_size="$(python3 parse_log.py ${logfile} family_size)"
    mdp_size="$(python3 parse_log.py ${logfile} mdp_size)"
    dtmc_size="$(python3 parse_log.py ${logfile} dtmc_size)"
    
    printf "%12s \t %-10s \t %-10s \t %-10s \t %-10s\n" ${benchmark_name} ${number_of_holes} ${family_size} ${mdp_size} ${dtmc_size}
}

function print_ce_info() {
    benchmark_name=$1
    
    logfile=ce/maxsat/${benchmark_name}_hybrid.txt
    ce_quality_maxsat="$(python3 parse_log.py ${logfile} ce_quality_maxsat)"
    ce_time_maxsat="$(python3 parse_log.py ${logfile} ce_time_maxsat)"
    
    logfile=ce/quality/${benchmark_name}_hybrid.txt
    ce_quality_trivial="$(python3 parse_log.py ${logfile} ce_quality_trivial)"
    ce_time_trivial="$(python3 parse_log.py ${logfile} ce_time_trivial)"
    ce_quality_nontrivial="$(python3 parse_log.py ${logfile} ce_quality_nontrivial)"
    ce_time_nontrivial="$(python3 parse_log.py ${logfile} ce_time_nontrivial)"

    printf "%12s \t %-16s \t %-6s (%-6s) \t %-6s \t\n" ${benchmark_name} "${ce_quality_maxsat} (${ce_time_maxsat})" ${ce_quality_trivial} ${ce_time_trivial} ${ce_quality_nontrivial}
}

function print_performance_info() {
    benchmark_name=$1

    logfile=basic/${benchmark_name}_cegis.txt
    cegis_iters="$(python3 parse_log.py ${logfile} cegis_iters)"
    cegis_time="$(python3 parse_log.py ${logfile} synthesis_time)"

    logfile=basic/${benchmark_name}_cegar.txt
    cegar_iters="$(python3 parse_log.py ${logfile} cegar_iters)"
    cegar_time="$(python3 parse_log.py ${logfile} synthesis_time)"

    logfile=basic/${benchmark_name}_hybrid.txt
    hybrid_iters="$(python3 parse_log.py ${logfile} hybrid_iters)"
    hybrid_time="$(python3 parse_log.py ${logfile} synthesis_time)"

    printf "%12s \t %-10s \t %-10s \t %-10s \t %-10s \t %-10s \t %-10s \n" ${benchmark_name} ${cegis_iters} ${cegis_time} ${cegar_iters} ${cegar_time} ${hybrid_iters} ${hybrid_time}
}

function print_large_model_stats() {
    problem=$1

    printf "\n-- ${problem}\n"

    cegar_time="$(python3 parse_log.py large_model/${problem}/*cegar.txt synthesis_time)"
    cegar_iters="$(python3 parse_log.py large_model/${problem}/*cegar.txt cegar_iters)"

    hybrid_time="$(python3 parse_log.py large_model/${problem}/*hybrid.txt synthesis_time)"
    hybrid_iters="$(python3 parse_log.py large_model/${problem}/*hybrid.txt hybrid_iters)"

    printf "cegar: ${cegar_iters} iters, ${cegar_time} sec\n"
    printf "hybrid: ${hybrid_iters} iters, ${hybrid_time} sec\n"
}

## parse all logs ##############################################################

basic_bechmarks=( grid maze dpm pole herman )

# Table 1
printf "\nTable 1 (benchmark info)\n\n"
printf "%-10s \t %-10s \t %-10s \t %-10s \t %-10s\n" benchmark holes family MDP DTMC
for benchmark in "${basic_bechmarks[@]}"; do
    print_benchmark_info ${benchmark} basic/${benchmark}_easy_hybrid.txt
done
print_benchmark_info herman-large large_model/herman2_larger/optimality_5/*hybrid.txt

# Table 2 (counterexamples)
printf "\nTable 2 (counterexamples)\n\n"
printf "%-10s \t %-16s \t %-16s \t %-10s\n" benchmark maxsat trivial family
for benchmark in "${basic_bechmarks[@]}"; do
    print_ce_info ${benchmark}_easy
    print_ce_info ${benchmark}_hard
done

# Table 2 (performance)
printf "\nTable 2 (performance)\n\n"
printf "%-10s \t %-12s \t %-12s \t %-12s \t %-12s \t %-12s \t %-12s \n" benchmark cegis_iters cegis_time cegar_iters cegar_time hybrid_iters hybrid_time
for benchmark in "${basic_bechmarks[@]}"; do
    print_performance_info ${benchmark}_easy
    print_performance_info ${benchmark}_hard
done

# Table 3 (large model)
printf "\nTable 3 (large model)\n\n"
print_large_model_stats herman2_smaller/feasibility
print_large_model_stats herman2_smaller/multiple
print_large_model_stats herman2_smaller/optimality_0
print_large_model_stats herman2_larger/feasibility
print_large_model_stats herman2_larger/optimality_0
print_large_model_stats herman2_larger/optimality_5
onebyone_time="$(python3 parse_log.py large_model/herman2_larger/optimality_0/*onebyone.txt synthesis_time)"
printf "\n1-by-1 on herman2_larger: %s sec\n" ${onebyone_time}
