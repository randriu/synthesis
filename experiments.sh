#!/bin/sh

python3 saynt_new_beliefs.py refuel-08 > experiments/belief-5s/refuel-08.log

python3 saynt_new_beliefs.py 4x3-95 > experiments/belief-5s/4x3-95.log

python3 saynt_new_beliefs.py lanes > experiments/belief-5s/lanes.log

python3 saynt_new_beliefs.py query-s3 > experiments/belief-5s/query-s3.log

python3 saynt_new_beliefs.py network > experiments/belief-5s/network.log

python3 saynt_new_beliefs.py drone-4-1 > experiments/belief-5s/drone-4-1.log