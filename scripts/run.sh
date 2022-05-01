#!/bin/bash

# grid/center maze maze_avoid maze_hexa grid/avoid grid/avoid_2 grid/avoid_3 grid/avoid_4 grid/hexa grid/simple
for example in maze_hexa # grid/center maze maze_avoid maze_hexa grid/avoid grid/avoid_2 grid/avoid_3 grid/avoid_4 grid/hexa grid/simple
do
    props=$(find "workspace/examples/pomdp/$example" -type f -printf "%f\n" | grep prop)
    example="workspace/examples/pomdp/$example"


    timeout 5m python3 paynt/paynt.py \
        --properties $props \
        --project $example ar \
        --pomdp-memory-size 2 \
        --strategy iterative \
        --fsc-synthesis \

    timeout 5m python3 paynt/paynt.py \
        --properties $props \
        --project $example ar \
        --pomdp-memory-size 2 \
        --strategy injection \
        --fsc-synthesis \
    
    timeout 5m python3 paynt/paynt.py \
        --properties $props \
        --project $example ar \
        --fsc-synthesis \
        --pomdp-memory-size 1 \
        --incremental 1 0
done 
    