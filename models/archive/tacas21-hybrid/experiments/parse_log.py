import sys
import re

def match(regex, lines):
    for line in lines:
        res = re.match(regex, line)
        if res is not None:
            return res.groups()
    return None

# default values
iters_estimate = time_estimate = None
method = synthesis_time = number_of_holes = family_size = None
mdp_size = cegar_iters = None
dtmc_size = cegis_iters = None
ce_quality_maxsat = ce_quality_trivial = ce_quality_nontrivial = None
ce_time_maxsat = ce_time_trivial = ce_time_nontrivial = None
iters = time = None

# process command-line arguments
assert len(sys.argv) == 3
filename = sys.argv[1]
selection = sys.argv[2]

# read file
file = open(filename, 'r')
lines = file.readlines()
file.close()

# we will only need last few lines
lines = lines[-20:]

# timeout check
if lines[-1] == "TO\n":
    res = match(r"^.*?Performance estimation \(unfeasible\): (.*?) iterations in (.*?) sec.*?$", lines)
    if res is not None:
        iters = round(float(res[0]),0)
        time = round(float(res[1]),0)
        iters_estimate = str(iters) + "*"
        time_estimate = str(time) + "*"

res = match(r"^method: (.*?), synthesis time: (.*?) s$", lines)
if res is not None:
    method = res[0]
    synthesis_time = res[1]

res = match(r"^number of holes: (.*?), family size: (.*?)$", lines)
if res is not None:
    number_of_holes = res[0]
    family_size = res[1]

res = match(r"^super MDP size: (.*?), average MDP size: (.*?), MPD checks: (.*?), iterations: (.*?)$", lines)
if res is not None:
    mdp_size = res[1]
    cegar_iters = res[3]

res = match(r"^average DTMC size: (.*?), DTMC checks: (.*?), iterations: (.*?)$", lines)
if res is not None:
    dtmc_size = res[0]
    cegis_iters = res[2]

res = match(r"^ce quality: maxsat: (.*?), trivial: (.*?), non-trivial: (.*?)$", lines)
if res is not None:
    ce_quality_maxsat = res[0]
    ce_quality_trivial = res[1]
    ce_quality_nontrivial = res[2]

res = match(r"^ce time: maxsat: (.*?), trivial: (.*?), non-trivial: (.*?)$", lines)
if res is not None:
    ce_time_maxsat = res[0]
    ce_time_trivial = res[1]
    ce_time_nontrivial = res[2]

hybrid_iters = None if cegar_iters is None or cegis_iters is None else f"({cegar_iters},{cegis_iters})"

# identify iters and time
if method is None:
    # timeout
    iters = iters_estimate
    time = time_estimate
else:
    iters = next(value for value in [hybrid_iters, cegis_iters, cegar_iters] if value is not None)
    time = synthesis_time

# print selected value
value_selected = globals()[selection]
value_str = value_selected if value_selected is not None else "-"
print(value_str)
