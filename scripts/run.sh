#!/bin/bash

for example in grid/avoid grid/center maze maze_long
do
    props=$(find "workspace/examples/pomdp/$example" -type f -printf "%f\n" | grep prop)
    example="workspace/examples/pomdp/$example"


    timeout 30m python3 paynt/paynt.py \
        --properties $props \
        --project $example ar \
        --pomdp-memory-size 2 \
        --strategy iterative \
        --fsc-synthesis \

    timeout 30m python3 paynt/paynt.py \
        --properties $props \
        --project $example ar \
        --pomdp-memory-size 2 \
        --strategy injection \
        --fsc-synthesis \
    
    timeout 30m python3 paynt/paynt.py \
        --properties $props \
        --project $example ar \
        --fsc-synthesis \
        --pomdp-memory-size 1 \
        --incremental 1 4
done 
    