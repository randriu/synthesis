import os
import subprocess
from datetime import datetime
import sys

onebyone = "--onebyone" in sys.argv

# List of models
# pomdp_family_model = ["obstacles-maze-4", "obstacles-maze-4-2", "obstacles-maze-4-3", "refuel-04", "refuel-04-slip", "rover-100", "dpm-switch-q10"]
# pomdp_family_model = [
#     "avoid-3x5-1o-noslip-down",
#     "avoid-3x5-1o-noslip-down --fsc-memory-size 2",
#     "avoid-3x5-1o-slip-down",
#     "avoid-3x5-1o-slip-nodown",
#     "avoid-3x5-1o-slip-nodown --fsc-memory-size 2",
#     "avoid-4x4-3o-slip-1detect-nodown-lr",
#     "avoid-4x5-2o-noslip-1crash-nodown-lr",
#     "avoid-4x5-2o-noslip-1detect-nodown-lr",
#     "avoid-4x5-2o-slip-1detect-down",
#     "avoid-4x5-2o-slip-1detect-down-lr",
#     "avoid-4x5-2o-slip-1detect-nodown-lr",
#     "avoid-5x4-3o-slip-1detect-nodown-lr",

#     "avoid-5x4-2o-slip-1detect-nodown-lr"
# ]
pomdp_family_model = ["debugging-2"]

# Create experiments folder if it doesn't exist
experiments_dir = "experiments"
if not os.path.exists(experiments_dir):
    os.makedirs(experiments_dir)

# Get current date timestamp
timestamp = datetime.now().strftime("%Y-%m-%d")

# Create timestamped folder inside experiments
timestamped_dir = os.path.join(experiments_dir, f"{timestamp}-pomdp-family")
if onebyone:
    timestamped_dir += "-onebyone"
if not os.path.exists(timestamped_dir):
    os.makedirs(timestamped_dir)

# Iterate over the list and run the command
for model in pomdp_family_model:
    log_file = os.path.join(timestamped_dir, f"{model}.log")

    # Skip the model if log_file already exists and --override is not used
    if os.path.exists(log_file) and "--override" not in sys.argv:
        print(f"Skipping {model}, log file already exists.")
        continue

    command = f"gtimeout 1500 python3 paynt.py models/pomdp/sketches/{model}"
    if onebyone:
        command += " --method onebyone"

    with open(log_file, "w") as log:
        process = subprocess.Popen(command, shell=True, stdout=log, stderr=log)
        process.communicate()

    print(f"Finished analysis for {model}")