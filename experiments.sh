# verbose mode
# set -x

# timeout value for each experiment
timeout_basic=2s
timeout_large_model=2s

# number of experiments
experiment_current=0
experiment_total=58

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
    options=$6
    
    ((experiment_current+=1))
    echo "experiment ${experiment_current}/${experiment_total}: ${model} (${property}), method: ${method} (${options})"
    timeout ${timeout} python dynasty.py --project workspace/tacas21/${model} --properties ${property}.properties hybrid --regime ${regime} ${options} > ${logfile} || echo "TO" >> ${logfile}
}

# evaluate five models from the basic benchmark using a selected method
function evaluate_models() {
    experiment_set=$1
    method=$2
    options=$3
    models=( grid maze dpm pole herman )
    for model in "${models[@]}"; do
        dynasty ${timeout_basic} ${experiment_set} ${model} easy ${method} ${options} 
        dynasty ${timeout_basic} ${experiment_set} ${model} hard ${method} ${options}
    done
}

## experiment section ##########################################################

# create folders for log files
mkdir -p experiments
mkdir -p experiments/basic_hybrid
mkdir -p experiments/basic_cegar
mkdir -p experiments/basic_cegis
mkdir -p experiments/ce_quality
mkdir -p experiments/ce_maxsat

mkdir -p experiments/multiple_properties
mkdir -p experiments/large_model

# activate python environment and navigate to dynasty
source env/bin/activate
cd dynasty

# evaluate cegis/cegar/hybrid on a basic benchmark
echo "-- evaluating basic benchmark (cegis)"
evaluate_models basic_cegis cegis
echo "-- evaluating basic benchmark (cegar)"
evaluate_models basic_cegar cegar
echo "-- evaluating basic benchmark (hybrid)"
evaluate_models basic_hybrid hybrid

# evaluate CE quality on the same benchmark
echo "-- evaluating CE quality (hybrid)"
evaluate_models ce_quality hybrid --ce-quality
echo "-- evaluating CE quality (maxsat)"
evaluate_models ce_maxsat hybrid --ce-maxsat

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

echo "TODO file parsing"