#!/home/may/phd/storm/venv/bin/python

import os
import subprocess
import resource
import shutil
import sys
import re
import click
import math
import concurrent.futures

date="02-06"
experiment_group_name = f"{date}-dtpaynt-error-01-1h"
paynt_one = "one" in experiment_group_name

new_models = True

##### benchmarks evaluation ######

def contains_sketch(directory):
    if not os.path.isdir(directory):
        return False
    # files = [ os.path.basename(f.path) for f in os.scandir(directory) if f.is_file() ]
    # return b'sketch.templ' in files and b'sketch.props' in files
    subdirectories = [ f.path for f in os.scandir(directory) if f.is_dir() ]
    for x in subdirectories:
        if "decision_trees" in x.__str__():
            subdirectories = []
        if ".benchmark_suite" in x.__str__():
            subdirectories = []
    return len(subdirectories) == 0

def collect_sketches(directory):
    if ".benchmark_suite" in directory.__str__() or "decision_trees" in directory.__str__():
        return []
    if not isinstance(directory, bytes):
        directory = os.fsencode(directory)
    sketches = []
    if contains_sketch(directory):
        sketches.append(directory.decode("utf-8"))
    subdirectories = [ f.path for f in os.scandir(directory) if f.is_dir() ]
    for subdirectory in subdirectories:
        sketches += collect_sketches(subdirectory)
    return sketches

def log_dump(what, where):
    os.makedirs(os.path.dirname(where), exist_ok=True)
    if isinstance(what, bytes):
        what = what.decode("utf-8")
    with open(where, "w") as f:
        f.write(what)

def set_memory_limit(maxmem_mb):
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (maxmem_mb*1024*1024, hard))

def run_paynt(paynt_dir, sketch, options, timeout_seconds, maxmem_mb, task_name, output_dir, restart:bool):
    if os.path.isdir(output_dir) and not restart:
        print(f"{task_name} skipped, {output_dir} already exists")
        return
    os.makedirs(os.path.dirname(output_dir), exist_ok=True)

    options += f" --export-synthesis {output_dir}/tree"

    model = sketch
    other_flags = ""
    if new_models:
        if "undiscounted" in model:
            other_flags += " --sketch model.prism"
            other_flags += " --props model.props"
        else:
            other_flags += " --sketch model-random.drn"
            other_flags += " --props discounted.props"
        other_flags += " --add-dont-care-action"
    else:
        if "omdt" in model:
            other_flags += " --sketch model-random.drn"
            other_flags += " --props discounted.props"
        if "maze" in model:
            other_flags += " --sketch model-random.drn"
            other_flags += " --props discounted.props"
        if "qcomp" in model:
            # other_flags += " --sketch model-random-enabled.drn"
            other_flags += " --sketch model.prism"
            # other_flags += " --props discounted.props"
            other_flags += " --props model.props"
            other_flags += " --add-dont-care-action"
            # if paynt_one:
            #     other_flags += " --sketch model-random-enabled.drn"
            #     other_flags += " --props discounted.props"
            # else:
            #     other_flags += " --sketch model.prism"
            #     other_flags += " --props model.props"

        # if not paynt_one and "qcomp" not in model:
        #     other_flags += " --add-dont-care-action"

    if paynt_one:
        if "maze" in model or "omdt" in model:
            other_flags += f" --tree-map-scheduler {model}/scheduler.storm.json"
        if "qcomp" in model:
            # other_flags += f" --tree-map-scheduler {model}/scheduler.storm.json"
            other_flags += f" --tree-map-scheduler {model}/scheduler-random.storm.json"
    options += other_flags

    command = f"python3 {paynt_dir}/paynt.py {sketch} {options}"
    timeout_seconds += 10 # experiment reserve
    # use explicit option instead of preexec_fn for all-in-one
    preexec_fn = lambda: set_memory_limit(maxmem_mb)
    
    timed_out = False
    stdout = None
    stderr = None
    print(task_name, "started")
    try:
        result = subprocess.run(command.split(), preexec_fn=preexec_fn, timeout=timeout_seconds, capture_output=True, text=True)
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout
        stderr = e.stderr
    except subprocess.CalledProcessError as e:
        print(f'Error occured: {e}')
    except Exception as e:
        print(f'Exception occurred: {e}')

    output = ""
    if stdout is not None and len(stdout) > 0:
        if isinstance(stdout,str):
            output += stdout
        if isinstance(stdout,bytes):
            output += stdout.decode("utf-8")
    if stderr is not None and len(stderr) > 0:
        if isinstance(stderr,str):
            output += stderr
        if isinstance(stderr,bytes):
            output += stderr.decode("utf-8")
    log_dump(output, f"{output_dir}/stdout.txt")



def collect_tasks(models_dir, experiment_name, output_dir, restart:bool):
    sketches = collect_sketches(models_dir)
    experiment_dir = f"{output_dir}/{experiment_name}"
    if os.path.isdir(experiment_dir) and restart:
        print(f"removing existing directory {experiment_dir}")
        shutil.rmtree(experiment_dir)

    skip = []
    # skip += ["maze"]
    # skip += ["omdt"]
    # skip += ["qcomp"]

    current_experiment = 0

    sketches = sorted(sketches)
    sketches = [sketch for sketch in sketches if not any([k in str(sketch) for k in skip])]

    tasks = []
    for sketch in sketches:
        model_name = os.path.basename(sketch)
        model_group_name = os.path.basename(os.path.dirname(sketch))
        model_name = f"{model_group_name}-{model_name}"
        current_experiment += 1
        task_name = f"model {current_experiment}/{len(sketches)}".ljust(16) + model_name.ljust(32)
        task_output_dir = f"{experiment_dir}/{model_name}"
        tasks.append((sketch,task_name,task_output_dir))
    return tasks


def evaluate_benchmarks(experiment_name, num_workers, paynt_dir, timeout_seconds, maxmem_mb, options, restart, output_dir):
    models_dir = "/home/fpmk/synthesis-playground/models/dts-uai-subset"
    tasks = collect_tasks(models_dir, experiment_name, output_dir, restart)
    print(tasks)
    # exit()
    if num_workers == 1:
        for sketch,task_name,task_output_dir in tasks:
            run_paynt(paynt_dir, sketch, options, timeout_seconds, maxmem_mb, task_name, task_output_dir, restart)
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            for (sketch,task_name,task_output_dir) in tasks:
                executor.submit(run_paynt, paynt_dir, sketch, options, timeout_seconds, maxmem_mb, task_name, task_output_dir, restart)


##### log parsing #####

def search_entry(lines, regex, conversion=str, number=-1):
    num_groups = re.compile(regex).groups
    assert num_groups == 1
    entries = []
    for line in lines:
        match = re.search(regex, line)
        if match is not None:
            entry = conversion(match.group(1))
            entries.append(entry)
    
    if (len(entries) == 0 and number == -1) or number >= len(entries):
        return None
    return entries[number]

def search_int(lines, regex, number=-1):
    return search_entry(lines, regex, int, number)

def search_float(lines, regex, number=-1):
    return search_entry(lines, regex, float, number)

def shorten_model_name(model):
    ''' Get a shortened model name used in the paper. '''
    model_dict = {
        "avoid-8-2" : "av-8-2",
        "avoid-8-2-easy" : "av-8-2-e",
        "dodge-8-mod2-pull-30" : "dodge-2",
        "dodge-8-mod3-pull-30" : "dodge-3",
        "dpm-switch-q10" : "dpm-10",
        "dpm-switch-q10-big" : "dpm-10-b",
        "obstacles-8-6-skip" : "obs-8-6",
        "obstacles-10-6-skip-easy" : "obs-10-6",
        "obstacles-10-9-pull" : "obs-10-9",
        "rover-100-big" : "rov-100",
        "rover-1000" : "rov-1000",
        "uav-operator-roz-workload" : "uav-work",
    }
    if model in model_dict:
        model = model_dict[model]
    return model

class TableRow:

    def to_string(self, spreadsheet=False, latex=False):
        s = ""
        if not spreadsheet:
            is_na = lambda what,just : "N/A".ljust(just) if what is None else str(what).ljust(just)
        else:
            is_na = lambda what,just : "N/A;" if what is None else f"{str(what)};"
        latex_sep = "&  " if latex else ""
        form = lambda what,just : is_na(what,just)+latex_sep
        s += form(self.model, 26)
        s += form(self.variables, 6)
        s += form(self.states, 8)
        s += form(self.relevant_states, 2)
        s += form(self.actions, 8)
        s += form(self.choices, 8)
        s += form(self.true_opt, 12)
        s += form(self.random, 12)
        s += form("", 2)

        # s += form(self.max_depth, 12)
        s += form(self.best, 12)
        s += form(self.best_relative, 12)
        # s += form(self.time_best, 12)
        s += form(self.time, 12)
        s += form(self.tree_nodes, 12)
        s += form(self.tree_depth, 12)

        s += form(self.dtcontrol_calls, 12)
        s += form(self.dtcontrol_smaller, 12)
        s += form(self.dtcontrol_recomputed_calls, 12)
        s += form(self.dtcontrol_recomputed_smaller, 12)
        s += form(self.paynt_calls, 12)
        s += form(self.paynt_smaller, 12)
        s += form(self.paynt_tree_found, 12)
        s += form(self.all_larger, 12)
        s += form("", 2)

        s += form(self.dtcontrol_nodes, 12)
        s += form(self.dtcontrol_depth, 12)

        if paynt_one:
            return s

        # s += form(self.members, 12)
        # s += form(self.num_families_considered,8)
        # s += form(self.num_schedulers_preserved,8)
        # s += form(self.num_families_model_checked,8)
        # s += form(self.num_harmonizations,8)
        # s += form(self.num_harmonization_succeeded,8)

        return s

        s += form(self.fraction_init, 8)
        s += form(self.fraction_build, 8)
        s += form(self.fraction_mc, 8)
        s += form(self.fraction_consistent, 8)

    def __str__(self):
        return self.to_string(latex=False)

    @classmethod
    def header(cls):
        r = cls()
        r.model = "model"
        r.variables = "vars"
        r.states = "S"
        r.relevant_states = "rel(S)"
        r.actions = "Act"
        r.choices = "choices"
        r.true_opt = "*-opt"
        r.random = "random"

        r.best = "best"
        r.best_relative = "best relative"
        r.time = "time"
        r.tree_nodes = "tree nodes"
        r.tree_depth = "tree depth"

        r.dtcontrol_calls = "DTControl calls"
        r.dtcontrol_smaller = "DTControl smaller"
        r.dtcontrol_recomputed_calls = "DTControl recomputed calls"	
        r.dtcontrol_recomputed_smaller = "DTControl recomputed smaller"
        r.paynt_calls = "DTPAYNT calls"
        r.paynt_smaller = "DTPAYNT smaller"
        r.paynt_tree_found = "DTPAYNT tree found"
        r.all_larger = "both larger"

        r.dtcontrol_nodes = "DTControl nodes"
        r.dtcontrol_depth = "DTControl depth"

        # r.members = "|M|"
        # r.num_families_considered = "F"
        # r.num_schedulers_preserved = "Fs="
        # r.num_families_model_checked = "F?"
        # r.num_harmonizations = "H?"
        # r.num_harmonization_succeeded = "H+"

        # r.fraction_init = "init%"
        # r.fraction_build = "build%"
        # r.fraction_mc = "MC%"
        # r.fraction_consistent = "cons%"

        return r


def create_table_row(model, path, latex=False):
    
    log = f"{path}/{model}/stdout.txt"
    def float_pretty(x,digits=4):
        if x is None:
            return x
        else:
            return round(x,digits)

    def percent_pretty(x):
        if x is None or x < 0.01:
            return "0"
        else:
            return float_pretty(x,1)

    assert os.path.isfile(log)

    with open(log, "r") as f:
        lines = f.readlines()
    r = TableRow()


    r.model = shorten_model_name(model).replace("run-1-","")
    r.variables = search_int(lines, r"found the following (.*?) variables")
    r.states = search_int(lines, r"explicit quotient having (.*?) states and .*? choices")
    r.actions = search_int(lines, r"MDP has (\d+) actions")
    r.choices = search_int(lines, r"explicit quotient having .*? states and (.*?) choices")

    r.relevant_states = float_pretty(search_int(lines, r"MDP has (\d+)/.*? relevant states") / r.states * 100)
    r.true_opt = float_pretty(search_float(lines, r"optimal scheduler has value: (.*?)$"))
    r.random = float_pretty(search_float(lines, r"the random scheduler has value: (.*?)$"))

    # r.max_depth = search_int(lines, r"building tree of depth (\d+)")
    # r.members = search_entry(lines, r"synthesis initiated, design space: (.*?)$")

    # r.timeout = "TO" if search_entry(lines, r"(time limit reached)") is not None else "-"
    # r.best = float_pretty(search_float(lines, r"value (.*?) achieved after .*? seconds"))
    r.best = float_pretty(search_float(lines, r"the synthesized tree has value (.*?)\n"))
    r.best_relative = float_pretty(search_float(lines, r"the synthesized tree has relative value: (.*?)\n"))
    r.time = float_pretty(search_float(lines, r"synthesis finished after (.*?) seconds$"))
    r.tree_nodes = search_int(lines, r"synthesized tree of depth \d+ with (\d+) decision nodes")
    r.tree_depth = search_int(lines, r"synthesized tree of depth (\d+) with \d+ decision nodes")

    r.dtcontrol_calls = search_int(lines, r"dtcontrol calls: (\d+)$")
    r.dtcontrol_smaller = search_int(lines, r"dtcontrol successes: (\d+)$")
    r.dtcontrol_recomputed_calls = search_int(lines, r"dtcontrol recomputed calls: (\d+)$")
    r.dtcontrol_recomputed_smaller = search_int(lines, r"dtcontrol recomputed successes: (\d+)$")
    r.paynt_calls = search_int(lines, r"paynt calls: (\d+)$")
    r.paynt_smaller = search_int(lines, r"paynt successes smaller: (\d+)$")
    r.paynt_tree_found = search_int(lines, r"paynt tree found: (\d+)$")
    r.all_larger = search_int(lines, r"all larger: (\d+)$")

    r.dtcontrol_nodes = search_int(lines, r"initial external tree has depth .*? and (.*?) nodes")
    r.dtcontrol_depth = search_int(lines, r"initial external tree has depth (.*?) and .*? nodes")

    # r.num_families_considered = search_int(lines, r"families considered: (\d+)")
    # r.num_schedulers_preserved = search_int(lines, r"families with schedulers preserved: (\d+)")
    # r.num_families_model_checked = search_int(lines, r"families model checked: (\d+)")
    # r.num_harmonizations = search_int(lines, r"harmonizations attempted: (\d+)")
    # r.num_harmonization_succeeded = search_int(lines, r"harmonizations succeeded: (\d+)")

    # r.fraction_init = percent_pretty(search_float(lines, r"^(.*?) \%.*?set_depth\)$"))
    # r.fraction_build = percent_pretty(search_float(lines, r"^(.*?) \%.*?build\)$"))
    # r.fraction_mc = percent_pretty(search_float(lines, r"^(.*?) \%.*?_model_checking_sparse_engine.$"))
    # r.fraction_consistent = percent_pretty(search_float(lines, r"^(.*?) \%.*?are_choices_consistent\)$"))
    
    return r


def show_experiment(name, output_dir, spreadsheet=False):
    path = f"{output_dir}/{name}"
    
    models = [f for f in os.scandir(path) if f.is_dir()]
    models = [os.path.basename(m.path) for m in models]
    models = sorted(models)

    i1 = [i for i,model in enumerate(models) if "4x4" in model][0]
    i2 = [i for i,model in enumerate(models) if "8x8" in model][0]
    model = models[i1]; models[i1] = models[i2]; models[i2] = model

    rows = []
    for model in models:
        rows.append(create_table_row(model, path))

    print(TableRow.header().to_string(spreadsheet=spreadsheet))
    for row in rows:
        for depth,_ in enumerate(row.depth_info):
            if depth == 0: continue
            print(row.to_string_depth(spreadsheet=spreadsheet,depth=depth))


def show_experiment_group(group, output_dir, spreadsheet=False):


    group_path = f"{output_dir}/{group}"
    experiments = [os.path.basename(f.path) for f in os.scandir(group_path) if f.is_dir()]
    experiments = sorted(experiments)
    assert len(experiments) > 0
    for experiment in experiments:
        models = [os.path.basename(f.path) for f in os.scandir(f"{group_path}/{experiment}") if f.is_dir()]
        break
    models = sorted(models)

    # i1 = [i for i,model in enumerate(models) if "12x12" in model][0]
    # i2 = [i for i,model in enumerate(models) if "4x4" in model][0]
    # model = models[i1]; models[i1] = models[i2]; models[i2] = model

    # i1 = [i for i,model in enumerate(models) if "12x12" in model][0]
    # i2 = [i for i,model in enumerate(models) if "8x8" in model][0]
    # model = models[i1]; models[i1] = models[i2]; models[i2] = model

    rows = []
    for model in models:
        for experiment in experiments:
            rows.append(create_table_row(model, f"{group_path}/{experiment}"))

    print(TableRow.header().to_string(spreadsheet=spreadsheet))
    for row in rows:
        print(row.to_string(spreadsheet=spreadsheet))

def show_experiment_one(name, output_dir, spreadsheet=False):    
    path = f"{output_dir}/{name}"
    
    models = [f for f in os.scandir(path) if f.is_dir()]
    models = [os.path.basename(m.path) for m in models]
    models = sorted(models)

    if any(["8x8" in model for model in models]):
        i1 = [i for i,model in enumerate(models) if "8x8" in model][0]
        i2 = [i for i,model in enumerate(models) if "12x12" in model][0]
        model = models[i1]; models[i1] = models[i2]; models[i2] = model

    rows = []
    for model in models:
        rows.append(create_table_row(model, path))

    print(TableRow.header().to_string(spreadsheet=spreadsheet))
    for row in rows:
        print(row.to_string(spreadsheet=spreadsheet))



@click.command()
@click.option('--paynt-dir', type=str, default="/home/may/synthesis", show_default=True, help='Path to the Paynt root folder.')
# @click.option('--paynt-dir', type=str, default="/opt/paynt", show_default=True, help='Path to the Paynt root folder.')
@click.option('--workers', type=int, default=8, show_default=True, help='Number of parallel tests.')
@click.option('--timeout', type=int, default=1200, show_default=True, help='Time limit for abstraction refinement (per model), seconds.')
@click.option('--maxmem', type=int, default=16, show_default=True, help='Memory limit, GB.')
@click.option('--output', type=str, default="logs", show_default=True, help='Name for the output logs folder.')
@click.option('--restart', is_flag=True, help='Re-run all benchmarks.')
def main(paynt_dir, workers, timeout, maxmem, output, restart):


    profiling = ""
    # profiling = " --profiling"
    tree_enumeration = ""
    # tree_enumeration = " --tree-enumeration"
    
    depth_min = 1
    depth_max = 2
    # experiments = [
    #     (f"{experiment_group_name}/{depth}", f"{profiling} --tree-depth={depth} {tree_enumeration}", timeout) for depth in range(depth_min,depth_max+1)
    # ]
    experiments = [
        (f"{experiment_group_name}/integration", f"--add-dont-care-action --tree-enumeration --tree-depth 10", timeout)
    ]

    if paynt_one:
        depth_max = 20
        experiments = [(f"{experiment_group_name}", f"{profiling} --tree-depth={depth_max}", timeout)]

    for index,experiment in enumerate(experiments):
        name,options,timeout_sec = experiment
        maxmem_mb = maxmem*1024
        print(f"----- experiment {index+1}/{len(experiments)}: {name} -----")
        evaluate_benchmarks(name, workers, paynt_dir, timeout_sec, maxmem_mb, options, restart, output)

    # exit()
    if not paynt_one:
        show_experiment_group(experiment_group_name, output, spreadsheet=True)
    else:
        for experiment_name,_,_ in experiments:
            show_experiment_one(experiment_name, output, spreadsheet=True)


if __name__ == '__main__':
    main()
