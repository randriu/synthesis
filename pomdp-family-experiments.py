import os
import subprocess
from datetime import datetime
import sys

onebyone = "--onebyone" in sys.argv

# List of models
# pomdp_family_model = ["obstacles-maze-4", "obstacles-maze-4-2", "obstacles-maze-4-3", "refuel-04", "refuel-04-slip", "rover-100", "dpm-switch-q10"]
pomdp_family_model = [
    "_coridor-big",
    "_coridor-medium",
    "_coridor-medium-different-holes",
    "_coridor-small",
    "_coridor-small-different-holes",
    "coridor-3x5-1t",
    "coridor-3x5-2t",
    "coridor-3x5-2t-1o",
    "coridor-3x5-2t-2o",
    "coridor-3x5-2x2t-2o-fixed",
    "coridor-3x5-4t-2o",
    "coridor-3x5-4t-2o-fixed",
    "coridor-3x5-4t-2o-fixed-up",
    "coridor-3x6-4t-2o",
    "coridor-3x6-4t-2o-slip",
    "coridor-3x6-6t-2o",
    "coridor-3x6-6t-2o-bigger-holes",
    "coridor-3x6-6t-2o-up",
    "coridor-3x6-sym6t-2o",
    "coridor-3x6-sym6t-2o-up",
    "coridor-3x7-6t-3o-fixed-up",
    "coridor-3x7-6t-3o-up",
]

# Create experiments folder if it doesn't exist
experiments_dir = "experiments"
if not os.path.exists(experiments_dir):
    os.makedirs(experiments_dir)

# Get current date timestamp
timestamp = datetime.now().strftime("%Y-%m-%d")

# Create timestamped folder inside experiments
timestamped_dir = os.path.join(experiments_dir, f"{timestamp}-pomdp-family_threshold")
if onebyone:
    timestamped_dir += "-onebyone"
if not os.path.exists(timestamped_dir):
    os.makedirs(timestamped_dir)

# Iterate over the list and run the command
for model in pomdp_family_model:
    for memory in range(1, 5):
        log_file = os.path.join(timestamped_dir, f"{model}_mem{memory}.log")

        # Skip the model if log_file already exists and --override is not used
        if os.path.exists(log_file) and "--override" not in sys.argv:
            print(f"Skipping {model}, log file already exists.")
            continue

        command = f"gtimeout 1500 python3 paynt.py models/pomdp/sketches/coridor/{model} --fsc-memory-size {memory}"
        if onebyone:
            command += " --method onebyone"

        with open(log_file, "w") as log:
            process = subprocess.Popen(command, shell=True, stdout=log, stderr=log)
            process.communicate()

        print(f"Finished analysis for {model}")