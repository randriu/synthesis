#!/bin/bash

# grid/center maze maze_avoid maze_hexa grid/avoid grid/avoid_2 grid/avoid_3 grid/avoid_4 grid/hexa grid/simple
# for example in grid/simple grid/avoid grid/avoid_4 grid/center maze maze_long
for example in maze_long
do
    props=$(find "workspace/examples/pomdp/$example" -type f -printf "%f\n" | grep prop)
    example="workspace/examples/pomdp/$example"


    # timeout 30m python3 paynt/paynt.py \
    #     --properties $props \
    #     --project $example ar \
    #     --pomdp-memory-size 2 \
    #     --strategy iterative \
    #     --fsc-synthesis \

    # timeout 30m python3 paynt/paynt.py \
    #     --properties $props \
    #     --project $example ar \
    #     --pomdp-memory-size 2 \
    #     --strategy injection \
    #     --fsc-synthesis \
    
    python3 paynt/paynt.py \
        --properties $props \
        --project $example ar \
        --fsc-synthesis \
        --pomdp-memory-size 1 \
        --incremental 1 4
done 
    