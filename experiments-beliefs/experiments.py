import os
import subprocess
import signal
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))

# If you feel like your PC is struggling to achieve correct values in the given timeout
# because of performance issues try incresing this multiplier
# default = 1, if you set it to 2 all timeout settings will be multiplied by 2
timeout_multiplier = 1

# If true overwrite existing logs, if false only run experiments for missing log files
overwrite_logs = False

# If true FSCs will be exported alongside the log files
export_fsc = False

# SETTINGS FOR EXPERIMENTS
# use_storm = False                   # False if you want just PAYNT result
# iterative_storm = False   # False if you dont want iterative loop, otherwise (timeout, paynt_timeout, storm_timeout)
# get_storm_result = 0            # Put integer to represent number of seconds to just get storm result, False to turn off
# storm_options = "2mil"               # False to use default, otherwise one of [cutoff,clip2,clip4...]
# prune_storm = True                 # Family pruning based on storm, default False
# unfold_strategy = "cutoff"            # False to use default, otherwise one of [paynt,storm,cutoff]
# use_storm_cutoff = True            # Use Storm cutoff schedulers to prioritize family exploration, default False
# aposteriori_unfolding = False       # Enables new unfolding

# Parsing options to options string
# example options string: "--storm-pomdp --iterative-storm 600 12 12"
# if use_storm:
#     options_string = "--storm-pomdp"
#     if iterative_storm:
#         options_string += " --iterative-storm {} {} {}".format(iterative_storm[0], iterative_storm[1], iterative_storm[2])
#     if get_storm_result:
#         options_string += " --get-storm-result {}".format(get_storm_result)
#     if storm_options:
#         options_string += " --storm-options {}".format(storm_options)
#     if prune_storm:
#         options_string += " --prune-storm"
#     if unfold_strategy:
#         options_string += " --unfold-strategy-storm {}".format(unfold_strategy)
#     if use_storm_cutoff:
#         options_string += " --use-storm-cutoffs"
#     if aposteriori_unfolding:
#         options_string += " --posterior-aware"
# else:
#     options_string = ""

# CHANGE THIS TO CHANGE WHAT MODELS SHOULD BE USED
directory = os.fsencode(dir_path + '/../models/archive/cav23-saynt')
models = [ f.path for f in os.scandir(directory) if f.is_dir() ]

def run_experiment(options, logs_string, experiment_models, timeout, special={}):
    
    logs_dir = os.fsencode(dir_path + "/{}/".format(logs_string))

    print(f'\nRunning experiment {logs_string}. The logs will be saved in folder {logs_dir.decode("utf-8")}')
    print(f'The options used: "{options}"\n')

    real_timeout = int(timeout*timeout_multiplier)

    for model in models:
        model_name = os.path.basename(model).decode("utf-8")
        project_name = model.decode("utf-8")

        if model_name in special.keys():
            model_options = special[model_name]
        else:
            model_options = options

        # THE REST OF THE MODELS
        command = "python3 paynt.py --project {} --fsc-synthesis {}".format(project_name, model_options)

        if model_name not in experiment_models:
            continue

        if not overwrite_logs:
            if os.path.isfile(logs_dir.decode("utf-8") + model_name + "/" + "logs.txt"):
                print(model_name, "LOG EXISTS")
                continue

        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            # TIMEOUT HERE TO TERMINATE EXPERIMENT
            # timeout should be higher than the expected running time of a given experiment
            output, error = process.communicate(timeout=real_timeout)
            output, error = process.communicate()
            process.wait()
        except subprocess.TimeoutExpired:
            process.send_signal(signal.SIGKILL)
            output, error = process.communicate()
            process.wait()

        if os.path.isfile(logs_dir.decode("utf-8") + model_name + "/" + "logs.txt"):
            print(model_name, "OVERWRITEN LOG")
            os.remove(logs_dir.decode("utf-8") + model_name + "/" + "logs.txt")
        else:
            print(model_name)

        if os.path.isfile(logs_dir.decode("utf-8") + model_name + "/" + "stderr.txt"):    
            os.remove(logs_dir.decode("utf-8") + model_name + "/" + "stderr.txt")

        os.makedirs(os.path.dirname(logs_dir.decode("utf-8") + model_name + "/" + "logs.txt"), exist_ok=True)
        with open(logs_dir.decode("utf-8") + model_name + "/" + "logs.txt", "w") as text_file:
            text_file.write(output.decode("utf-8"))

        # TODO remove after
        if error:
            with open(logs_dir.decode("utf-8") + model_name + "/" + "stderr.txt", "w") as text_file:
                text_file.write(error.decode("utf-8"))

    print(f'\nExperiment {logs_string} completed. The logs are saved in folder {logs_dir.decode("utf-8")}')


def run_sarsop(options, logs_string, experiment_models, timeout):
    logs_dir = os.fsencode(dir_path + "/{}/".format(logs_string))

    print(f'\nRunning experiment {logs_string}. The logs will be saved in folder {logs_dir.decode("utf-8")}')
    print(f'The options used: "{options}"\n')

    real_timeout = int(timeout*timeout_multiplier)

    for model in experiment_models:

        model_name = model[:-6]
        model_name = model_name.replace(".", "-")

        # THE REST OF THE MODELS
        command = "./pomdpsol ../models/08/{} -p 1e-4 -o ../../../../synthesis-playground/experiments-beliefs/sarsop/output/{}.out".format(model, model_name)

        if not overwrite_logs:
            if os.path.isfile(logs_dir.decode("utf-8") + model_name + "/" + "logs.txt"):
                print(model_name, "LOG EXISTS")
                continue

        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            # TIMEOUT HERE TO TERMINATE EXPERIMENT
            # timeout should be higher than the expected running time of a given experiment
            output, error = process.communicate(timeout=real_timeout)
            process.wait()
        except subprocess.TimeoutExpired:
            process.send_signal(signal.SIGINT)
            output, error = process.communicate()
            process.wait()

        if os.path.isfile(logs_dir.decode("utf-8") + model_name + "/" + "logs.txt"):
            print(model_name, "OVERWRITEN LOG")
            os.remove(logs_dir.decode("utf-8") + model_name + "/" + "logs.txt")
        else:
            print(model_name)

        if os.path.isfile(logs_dir.decode("utf-8") + model_name + "/" + "stderr.txt"):    
            os.remove(logs_dir.decode("utf-8") + model_name + "/" + "stderr.txt")

        os.makedirs(os.path.dirname(logs_dir.decode("utf-8") + model_name + "/" + "logs.txt"), exist_ok=True)
        with open(logs_dir.decode("utf-8") + model_name + "/" + "logs.txt", "w") as text_file:
            text_file.write(output.decode("utf-8"))

        # TODO remove after
        if error:
            with open(logs_dir.decode("utf-8") + model_name + "/" + "stderr.txt", "w") as text_file:
                text_file.write(error.decode("utf-8"))

    print(f'\nExperiment {logs_string} completed. The logs are saved in folder {logs_dir.decode("utf-8")}')


if __name__ == '__main__':
    experiment = sys.argv[1]
    overwrite = sys.argv[2]
    overwrite_logs = overwrite == "True"
    export_fsc = len(sys.argv) > 3

    if experiment == 'default':
        experiment_models = ["drone-4-2", "network", "4x3-95", "query-s3", "milos-aaai97", "network-2-8-20", "refuel-08", "refuel-20"]

        options = "--storm-pomdp --iterative-storm 900 90 2 --enhanced-saynt 0 --saynt-overapprox"
        logs_string = "uniform-overapp-default-90-2"
        timeout = 1200
        run_experiment(options, logs_string, experiment_models, timeout)

        print("\n EXPERIMENT COMPLETE\n")

    elif experiment == 'saynt':
        experiment_models = ["problem-saynt"]

        options = "--storm-pomdp --iterative-storm 900 60 10 --enhanced-saynt 6"
        logs_string = "saynt-enhanced"
        timeout = 1200
        run_experiment(options, logs_string, experiment_models, timeout)

        print("\n EXPERIMENT COMPLETE\n")

    elif experiment == 'posterior':
        experiment_models = ["drone-4-2", "network", "4x3-95"]

        options = "--storm-pomdp --iterative-storm 900 90 2 --enhanced-saynt 0 --saynt-overapprox --posterior-aware"
        logs_string = "uniform-overapp-default-90-2-posterior"
        timeout = 1200
        run_experiment(options, logs_string, experiment_models, timeout)

        print("\n EXPERIMENT COMPLETE\n")

    elif experiment == 'saynt-variants':
        experiment_models = ["drone-4-1", "drone-8-2", "network", "4x3-95", "query-s3", "milos-aaai97", "network-3-8-20", "refuel-20", "lanes"]
        posterior_experiment_models = ["drone-4-2", "network", "4x3-95"]
        longer_experiment_models = ["milos-aaai97", "query-s3"]

        options = "--storm-pomdp --iterative-storm 900 60 10 --storm-exploration-heuristic gap"
        logs_string = "saynt-gap"
        timeout = 1200
        run_experiment(options, logs_string, experiment_models, timeout)

        options = "--storm-pomdp --iterative-storm 900 60 10 --storm-exploration-heuristic gap --posterior-aware"
        logs_string = "saynt-gap-posterior"
        timeout = 1200
        run_experiment(options, logs_string, posterior_experiment_models, timeout)

        options = "--storm-pomdp --iterative-storm 900 90 10 --storm-exploration-heuristic gap"
        logs_string = "saynt-gap-paynt90"
        timeout = 1200
        run_experiment(options, logs_string, longer_experiment_models, timeout)

        options = "--storm-pomdp --iterative-storm 900 60 10 --storm-exploration-heuristic reachability"
        logs_string = "saynt-reachability"
        timeout = 1200
        run_experiment(options, logs_string, experiment_models, timeout)

        options = "--storm-pomdp --iterative-storm 900 60 10 --storm-exploration-heuristic reachability --posterior-aware"
        logs_string = "saynt-reachability-posterior"
        timeout = 1200
        run_experiment(options, logs_string, posterior_experiment_models, timeout)

        options = "--storm-pomdp --iterative-storm 900 90 10 --storm-exploration-heuristic reachability"
        logs_string = "saynt-reachability-paynt90"
        timeout = 1200
        run_experiment(options, logs_string, longer_experiment_models, timeout)

        print("\n EXPERIMENT COMPLETE\n")

    elif "sarsop":
        # experiment_models = ["drone-4-1-80.pomdp", "drone-4-1-95.pomdp", "drone-4-2-80.pomdp", "drone-4-2-95.pomdp", "drone-8-2-80.pomdp", "drone-8-2-95.pomdp", "grid-av-4-01-80.pomdp", "grid-av-4-01-95.pomdp", "refuel-06-80.pomdp", "refuel-06-95.pomdp", "refuel-08-80.pomdp", "refuel-08-95.pomdp", "refuel-20-80.pomdp", "refuel-20-95.pomdp"]
        experiment_models = ["milos-aaai97.pomdp", "network.pomdp", "query.s3.pomdp", "learning.c3.pomdp", "4x5x2.95.pomdp", "hanks.95.pomdp"]
        # experiment_models = ["network-3-8-20-80.pomdp", "network-3-8-20-95.pomdp"]

        options = ""
        logs_string = "sarsop-08"
        timeout = 900
        run_sarsop(options, logs_string, experiment_models, timeout)

        print("\n EXPERIMENT COMPLETE\n")

    else:
        print("Unknown experiment")