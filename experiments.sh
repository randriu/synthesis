#!/bin/sh

python3 saynt_new_beliefs.py refuel-08 > experiments/belief-1s-s/refuel-08.log

python3 saynt_new_beliefs.py 4x3-95 > experiments/belief-1s-s/4x3-95.log

# python3 saynt_new_beliefs.py lanes > experiments/belief-5s/lanes.log

python3 saynt_new_beliefs.py query-s3 > experiments/belief-1s-s/query-s3.log

python3 saynt_new_beliefs.py network > experiments/belief-1s-s/network.log

python3 saynt_new_beliefs.py drone-4-1 > experiments/belief-1s-s/drone-4-1.log


# for dir in models/archive/cav23-saynt/*; do
#     # echo "$dir"
#     dirname="$(basename "${dir}")"
#     echo "$dirname"
#     timeout 30 python3 saynt_new_beliefs.py "$dirname" > experiments/beliefs-info/"$dirname".log
# done