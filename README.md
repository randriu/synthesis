# PAYNT

PAYNT is tool that can automatically synthesize finite-state controllers for POMDPs. This fork modifies PAYNT to be able to restrict design spaces and only synthesize controllers of certain types.

## Installation
To install the program, run the installation script:
```
./install.sh
```

## Running the program

To run the program you use the script`./scripts/run.sh` which runs all three of the approaches on the four interesting benchmarks.

Before you run the program, make sure the folder `/workspace/log` exists and that you have the Python environment loaded (`source env/bin/activate`).


## Options:

```
Options:
  --project TEXT                  root  [required]
  --sketch TEXT                   name of the sketch file
  --properties TEXT               name of the properties file
  --fsc-synthesis                 enable incremental synthesis of FSCs for a
                                  POMDP
  --pomdp-memory-size INTEGER     implicit memory size for POMDP FSCs
  --incremental INTEGER...        enable incremental synthesis of FSC for a
                                  POMDP within a memory size with applied
                                  restrictions
  --strategy [full|iterative|injection]
                                  define strategy
  --reset-optimum                 reset the optimality property after each
                                  synthesis loop
  --help                          Show this message and exit.
  ```
