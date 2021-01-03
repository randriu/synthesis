import sys
import re

# process command line arguments
assert len(sys.argv) == 3
filename = sys.argv[1]
selection = sys.argv[2]

# read file
file = open(filename, 'r')
lines = file.readlines()
file.close()

# we need at most last 20 lines
lines = lines[-20:]

# timeout check
if lines[-1] == "TO\n":
    print("-")
    exit()

def match(regex, lines):
    for line in lines:
        res = re.match(regex, line)
        if res is not None:
            return res.groups()
    return None

method = synthesis_time = number_of_holes = family_size = None
mdp_size = cegar_iters = None
dtmc_size = cegis_iters = None
ce_quality_maxsat = ce_quality_trivial = ce_quality_nontrivial = None
ce_time_maxsat = ce_time_trivial = ce_time_nontrivial = None

res = match(r"^method: (.*?), synthesis time: (.*?) s$", lines)
assert res is not None
method = res[0]
synthesis_time = res[1]


res = match(r"^number of holes: (.*?), family size: (.*?)$", lines)
assert res is not None
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

hybrid_iters = f"({cegar_iters},{cegis_iters})"

# print selection
selected_value = globals()[selection]
print(selected_value)

