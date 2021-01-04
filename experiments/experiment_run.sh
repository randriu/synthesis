# verbose mode
# set -x

# checklist

# timeout values for each experiment
timeout_basic_benchmark=30s  # grid/maze/dpm/pole/herman
timeout_large_model=1m      # large herman

# number of experiments
experiment_current=0
experiment_total=59

# sample command:
# timeout ${timeout} python dynasty.py --project workspace/tacas21/grid/ --constants CMAX=40,THRESHOLD=0.931 hybrid --regime 3 > ../experiments/grid_easy_hybrid.txt || > ../experiments/grid_easy_hybrid.txt

## helper functions ############################################################

# convert selected synthesis method to regime index
function method_to_regime() {
    local method=$1
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
    local timeout=$1
    local experiment_set=$2
    local model=$3
    local property=$4
    local method=$5
    local regime="$(method_to_regime ${method})"
    local logfile="../experiments/${experiment_set}/${model}_${property}_${method}.txt"
    local extra_option_1=$6
    local extra_option_2=$7
    
    ((experiment_current+=1))
    echo "experiment ${experiment_current}/${experiment_total}: ${model} (${property}), method: ${method} (${extra_option_1} ${extra_option_2})"
    timeout ${timeout} python dynasty.py --project workspace/tacas21/${model} --properties ${property}.properties hybrid --regime ${regime} --check-prerequisites ${extra_option_1} ${extra_option_2} > ${logfile} || echo "TO" >> ${logfile}
}

# evaluate five models from the basic benchmark using a selected method
function evaluate_basic_benchmark() {
    local experiment_set=$1
    local method=$2
    local options=$3
    local models=( grid maze dpm pole herman )
    for model in "${models[@]}"; do
        dynasty ${timeout_basic_benchmark} ${experiment_set} ${model} easy ${method} ${options} 
        dynasty ${timeout_basic_benchmark} ${experiment_set} ${model} hard ${method} ${options}
    done
}

## experiment section ##########################################################

# create folders for log files
mkdir -p basic ce_quality ce_maxsat large_model large_model/feasibility large_model/multiple large_model/optimality_0 large_model/optimality_5

# activate python environment and navigate to dynasty
source ../env/bin/activate
cd ../dynasty

# # evaluate cegis/cegar/hybrid on a basic benchmark
# echo "-- evaluating basic benchmark (cegis)"
# evaluate_basic_benchmark basic cegis
# echo "-- evaluating basic benchmark (cegar)"
# evaluate_basic_benchmark basic cegar
# echo "-- evaluating basic benchmark (hybrid)"
# evaluate_basic_benchmark basic hybrid

# # evaluate CE quality on the same benchmark
# echo "-- evaluating CE quality (hybrid)"
# evaluate_basic_benchmark ce_quality hybrid "--ce-quality"
# echo "-- evaluating CE quality (maxsat)"
# evaluate_basic_benchmark ce_maxsat hybrid "--ce-quality --ce-maxsat"

## large model experiments

# estimate 1-by-1 on optimality
dynasty ${timeout_large_model} large_model/optimality_0 herman_large none onebyone "--optimality 0.optimal"

# evaluate CEGAR and hybrid
methods=( cegar hybrid )
for method in "${methods[@]}"; do
    regime="$(method_to_regime ${method})"
    
    dynasty ${timeout_large_model} large_model/feasibility herman_large feasibility ${method}
    dynasty ${timeout_large_model} large_model/multiple herman_large multiple ${method}
    dynasty ${timeout_large_model} large_model/optimality_0 herman_large none ${method} "--optimality 0.optimal"
    dynasty ${timeout_large_model} large_model/optimality_5 herman_large none ${method} "--optimality 5.optimal"
done

# deactivate python environment and navigate to root folder
deactivate
cd $OLDPWD

echo "all experiments complete"
