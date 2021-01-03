# verbose mode
# set -x

# timeout values for each experiment
timeout_basic_benchmark=2h  # grid/maze/dpm/pole/herman
timeout_large_model=2h      # large herman

# number of experiments
experiment_current=0
experiment_total=56

# sample command:
# timeout ${timeout} python dynasty.py --project workspace/tacas21/grid/ --constants CMAX=40,THRESHOLD=0.931 hybrid --regime 3 > ../experiments/grid_easy_hybrid.txt || > ../experiments/grid_easy_hybrid.txt

## helper functions ############################################################

# convert selected synthesis method to regime index
function method_to_regime() {
    method=$1
    if [ $method == "onebyone" ]; then
        echo 0
    elif [ $method == "cegis" ]; then
        echo 1
    elif [ $method == "cegar" ]; then
        echo 2
    elif [ $method == "hybrid" ]; then
        echo 3
    else
        echo "unknown synthesis method"
        exit 1
    fi

}

# ryn dynasty on a given model/property via a selected method (onebyone, cegis, cegar, hybrid)
function dynasty() {
    timeout=$1
    experiment_set=$2
    model=$3
    property=$4
    method=$5
    regime="$(method_to_regime ${method})"
    logfile="../experiments/${experiment_set}/${model}_${property}_${method}.txt"
    extra_option_1=$6
    extra_option_2=$7
    
    ((experiment_current+=1))
    echo "experiment ${experiment_current}/${experiment_total}: ${model} (${property}), method: ${method} (${extra_option_1} ${extra_option_2})"
    timeout ${timeout} python dynasty.py --project workspace/tacas21/${model} --properties ${property}.properties hybrid --regime ${regime} ${extra_option_1} ${extra_option_2} > ${logfile} || echo "TO" >> ${logfile}
}

# evaluate five models from the basic benchmark using a selected method
function evaluate_models() {
    experiment_set=$1
    method=$2
    options=$3
    models=( grid maze dpm pole herman )
    for model in "${models[@]}"; do
        dynasty ${timeout_basic_benchmark} ${experiment_set} ${model} easy ${method} ${options} 
        dynasty ${timeout_basic_benchmark} ${experiment_set} ${model} hard ${method} ${options}
    done
}

## experiment section ##########################################################

# create folders for log files
mkdir -p basic ce_quality ce_maxsat multiple_properties large_model

# activate python environment and navigate to dynasty
source ../env/bin/activate
cd ../dynasty

# evaluate cegis/cegar/hybrid on a basic benchmark
echo "-- evaluating basic benchmark (cegis)"
evaluate_models basic cegis
echo "-- evaluating basic benchmark (cegar)"
evaluate_models basic cegar
echo "-- evaluating basic benchmark (hybrid)"
evaluate_models basic hybrid

# evaluate CE quality on the same benchmark
echo "-- evaluating CE quality (hybrid)"
evaluate_models ce_quality hybrid "--ce-quality"
echo "-- evaluating CE quality (maxsat)"
evaluate_models ce_maxsat hybrid "--ce-quality --ce-maxsat"

## TODO multiple properties
echo "TODO multiple properties"

## large model experiments
methods=( onebyone cegar hybrid )
for method in "${methods[@]}"; do
    regime="$(method_to_regime ${method})"
    
    ((experiment_current+=1))
    echo "experiment ${experiment_current}/${experiment_total}: herman_large (feasibility), method: ${method}"
    logfile="../experiments/large_model/feasibility_${method}.txt"
    timeout ${timeout_large_model} python dynasty.py --project workspace/tacas21/herman_large/feasibility --properties sketch.properties hybrid --regime ${regime} > ${logfile} || echo "TO" >> ${logfile}
    
    ((experiment_current+=1))
    echo "experiment ${experiment_current}/${experiment_total}: herman_large (optimality), method: ${method}"
    logfile="../experiments/large_model/optimality_${method}.txt"
    timeout ${timeout_large_model} python dynasty.py --project workspace/tacas21/herman_large/optimality --properties sketch.properties hybrid --optimality sketch.optimal --regime ${regime} > ${logfile} || echo "TO" >> ${logfile}
done

# deactivate python environment and navigate to root folder
deactivate
cd $OLDPWD

## parsing log files ###########################################################

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
    
    logfile=ce_maxsat/${benchmark_name}_hybrid.txt
    ce_quality_maxsat="$(python3 parse_log.py ${logfile} ce_quality_maxsat)"
    ce_time_maxsat="$(python3 parse_log.py ${logfile} ce_time_maxsat)"
    
    logfile=ce_quality/${benchmark_name}_hybrid.txt
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

    # 1-by-1 estimate: divide family size by the number of iterations performed before timeout
    multiplier=$(cat large_model/${problem}_onebyone.txt | grep "Iteration:" | tail -n 1 | awk '{print $12 / $10}')
    printf "1-by-1: approximately %s * %s\n" ${multiplier} ${timeout_large_model}

    cegar_time="$(python3 parse_log.py large_model/${problem}_cegar.txt synthesis_time)"
    cegar_iters="$(python3 parse_log.py large_model/${problem}_cegar.txt cegar_iters)"

    hybrid_time="$(python3 parse_log.py large_model/${problem}_hybrid.txt synthesis_time)"
    hybrid_iters="$(python3 parse_log.py large_model/${problem}_hybrid.txt hybrid_iters)"

    printf "cegar: ${cegar_iters} iters, ${cegar_time} sec\n"
    printf "hybrid: ${hybrid_iters} iters, ${hybrid_time} sec\n"
}

basic_bechmarks=( grid maze dpm pole herman )

# Table 1
printf "\nTable 1 (benchmark info)\n\n"
printf "%-10s \t %-10s \t %-10s \t %-10s \t %-10s\n" benchmark holes family MDP DTMC
for benchmark in "${basic_bechmarks[@]}"; do
    print_benchmark_info ${benchmark} basic/${benchmark}_easy_hybrid.txt
done
print_benchmark_info herman-large large_model/feasibility_hybrid.txt
echo ""

# Table 2 (counterexamples)
printf "\nTable 2 (counterexamples)\n\n"
printf "%-10s \t %-16s \t %-16s \t %-10s\n" benchmark maxsat trivial family
for benchmark in "${basic_bechmarks[@]}"; do
    print_ce_info ${benchmark}_easy
    print_ce_info ${benchmark}_hard
done

# Table 2 (performance)
printf "\nTable 2 (performance)\n\n"
printf "%-10s \t %-12s \t %-12s \t %-12s \t %-12s \t %-12s \t %-12s \n" "benchmark" "cegis_iters" "cegis_time" "cegar_iters" "cegar_time" "hybrid_iters" "hybrid_time"
for benchmark in "${basic_bechmarks[@]}"; do
    print_performance_info ${benchmark}_easy
    print_performance_info ${benchmark}_hard
done

# Table 3 (multiple properties)
printf "\nTable 3 (multiple properties)\n\n"
echo "TODO"

# Table 4 (large model)
printf "\nTable 3 (large model)\n"
print_large_model_stats feasibility
print_large_model_stats optimality

