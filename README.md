# PAYNT

PAYNT (Probabilistic progrAm sYNThesizer) is a tool for the automated synthesis of probabilistic programs. PAYNT takes a program with holes (a so-called sketch) and a specification (see below for more information), and outputs a concrete hole assignment that yields a program that satisfies the specification, if such an assignment exists. Internally, PAYNT interprets the incomplete probabilistic program as a family of Markov chains and uses state-of-the-art synthesis methods on top of the model checker [Storm](https://github.com/moves-rwth/storm) to identify satisfying realization. PAYNT is implemented in python and uses [stormpy](https://github.com/moves-rwth/stormpy) -- python bindings for Storm. This repository contains the source code of PAYNT along with adaptations for [storm](https://github.com/moves-rwth/storm) and [stormpy](https://github.com/moves-rwth/stormpy), prerequisites for PAYNT.

PAYNT is described in 
- [1] PAYNT: A Tool for Inductive Synthesis of Probabilistic Programs by Roman Andriushchenko, Milan Ceska, Sebastian Junges, Joost-Pieter Katoen and Simon Stupinsky

Most of the algorithms are described in 
- [2] Inductive Synthesis for Probabilistic Programs Reaches New Horizons by Roman Andriushchenko, Milan Ceska, Sebastian Junges, Joost-Pieter Katoen, TACAS 2021
- [3] Counterexample-Driven Synthesis for Probabilistic Program Sketches by Milan Ceska, Christian Hensel, Sebastian Junges, Joost-Pieter Katoen, FM 2019.
- [4] Shepherding Hordes of Markov Chains by Milan Ceska, Nils Jansen, Sebastian Junges, Joost-Pieter Katoen, TACAS 2019

PAYNT is hosted on [github](https://github.com/gargantophob/synthesis).


## Image with the pre-installed tool

An image with the pre-installed tool is available in [this Ubuntu 20.04 LTS virtual machine](). Compilation and installation of the tool from scratch on your system or VM will be discussed in the end of this README.

** How to boot the VM ** 
- Virtualbox, no password.
- Where to navigate.

## Getting started with PAYNT 

Having the tool installed, you can quickly test it by activating the python environment and asking PAYNT to evaluate a simple synthesis problem:

```sh
source env/bin/activate
python3 paynt/paynt.py --project cav21-benchmark/grid --properties easy.properties hybrid
```

The syntax of the command is explained in the last chapter of this README. For now, we can see that we investigate the __Grid__ benchmark discussed in the CAV'21 paper and synthesize it wrt. the easy property using the advanced hybrid approach. The tool will print a series of log messages and, in the end, a short summary of the synthesis process, similar to the one below:

```
formula 1: P>=931/1000 [F ("goal" & (c < 40))]

method: Hybrid, synthesis time: 3.03 s
number of holes: 8, family size: 65536
super MDP size: 11535, average MDP size: 11490, MPD checks: 5, iterations: 5
average DTMC size: 1232, DTMC checks: 215, iterations: 215

feasible: no
```
Importantly, the tool reports that it could not find a feasible solution.


The python environment can be deactivated by runnning

```sh
deactivate
```

## Running PAYNT

### Syntax of the PAYNT's command
PAYNT is started using the command in the following form:

```shell
python3 paynt/paynt.py [OPTIONS] [hybrid|cegar|cegis|onebyone]
```
where the most important options are can be: 
- ``--project PATH``: specifies the path to the benchmark folder [required]
- ``--sketch FILE_IN_PATH``: specifies the file containing the template description in the PRISM guarded command language [default: ``PATH/sketch.templ``]
- ``--properties FILE_IN_PATH``: specifies the file containing specifications to synthesise against [default: ``PATH/sketch.properties``]
- ``--constants TEXT``: specifies the values of constants that are undefined in the sketch and are not holes, in the form: ``c1=0,c2=1`` as standard for Prism programs.
- 
For instance, PAYNT can be run most simply as follows: 

```shell
python3 paynt/paynt.py --project cav21-benchmark/dpm-demo --constants CMAX=2 hybrid
```

The `--project` option specifies the path to the benchmark folder.
PAYNT inspects the content of this folder to find the required files for the synthesis process: `sketch.templ` and `sketch.properties`.
The first file contains the template description, and the second one the specifications.
The `--constants` option specifies the value for an undefined variable in the sketch, which is not considered as a synthesised hole.
Finally, the last argument specifies the selected synthesis method: `hybrid`.

PAYNT has some advanced options for developers.
- ``--short-summary``: prints also short summary of the synthesis results consisting of primary information
- ``--ce-quality``: evaluates the counter-example quality when usage the hybrid approach. For recreating experiments in [2].
- ``--ce-maxsat``: enables the construction of counter-examples using MaxSat approach and also their evaluation. For recreating experiments in [2].
- ``--help``: shows the help message of the PAYNT and exit the program


## Understanding the synthesis process in PAYNT

The PAYNT's command produces the following summary printed at the end of the synthesis process:

```shell
formula 1: R[exp]{"rewardmodel_lost"}<=1 [F "finished"]
optimal setting: formula: R[exp]{"power"}min=? [F "finished"]; direction: min; eps: 0.0
method: Hybrid, synthesis time: 23.26 s
number of holes: 7, family size: 12150
super MDP size: 1502, average MDP size: 1365, MPD checks: 6, iterations: 3
average DTMC size: 172, DTMC checks: 2708, iterations: 1354

optimal: 9100.064246
hole assignment: P1=1,P2=0,P3=0,P4=2,T1=0.0,T3=0.8,QMAX=5
```

This summary consists of some information about the result of the performed synthesis process: benchmark statistics, synthesis time, number of iterations, MDP-related info, DTMC-related info, whether the synthesis problem is feasible etc.
The first lines contain the synthesised specifications, as well as the optimal property with its settings if it was entered.
We can see that this particular DPM benchmark contains 7 holes (parameters) and 12.1K family members.
On average, each member has on average 1.3K states when constructed via the (quotient) MDP in the AR method and 172 states when analysing the underlying DTMC (in CEGIS). 
We can also see that the problem found the optimal solution satisfying also given formula and that on our machine took 3 AR, 1354 CEGIS iterations and 23 seconds to prove this.
The last lines show the synthesised solution with concrete instantiations of holes and the found optimal value.
Notice that only the hybrid method contains both MDP- and DTMC-related information since CEGIS never deals with MDPs, and AR only works via the MDP.

### Sketching language

PAYNT takes as an input a sketch -- program description in `PRISM` (or `JANI`) language containing some undefined parameters (holes) with associated options from domains -- and a specification given as a list of temporal logic constraints (interpreted as a conjunction of theses constrains) possibly including an optimal objective. Before explaining the sketching language, let us briefly present the key ideas of the `PRISM` language -- the full documentation of the language is available [here](https://www.prismmodelchecker.org/manual/ThePRISMLanguage/Introduction).

A `PRISM` program consists of one or more reactive modules that may interact with each other using synchronisation. A module has a set of (bounded) variables that span its state space. Possible transitions between states of a module are described by a set of guarded commands of the form:

```math
[action] guard -> prob_1 : update_1 + ... + prob_n : update_n; 
```

If the `guard` evaluates to true, an update of the variables is chosen according to the probability distribution given by expressions `p_1` through `p_n`. The `actions` are used to force two or more modules to make the command simultaneously (i.e. to synchronise).

Recall that the sketch is a `PRISM` program with holes and allows us to compactly describe a set of candidates program.
The holes can appear in guards and updates. Replacing each hole with one of its options yields a complete program with the semantics given by a finite-state Markov chain. 

We exemplify the usage of PAYNT by the following synthesis problem.

<img src="./doc/figures/dpm.jpg" alt="The server for request processing">

Consider a server for request processing depicted in Figure above.
Requests are generated (externally) in random intervals and upon arrival stored in a request queue of capacity Q<sub>max</sub>. 
When the queue is full, the request is lost.
The server has three profiles -- *sleeping*, *idle* and *active* -- that differ in their power consumption.
The requests are processed by the server only when it is in the active state.
Switching from a low-energy state into the active state requires additional energy as well as an additional random latency before the request can be processed. We further assume that the power consumption of request processing depends on the current queue size. The operation time of the server finite but given by a random process.

The goal of the synthesis process is to design power manager (PM) that controls the server. 
The PM observes the current queue size and then sets the desired power profile. 
We assume that the PM distinguishes between four queue occupancy levels determined by the threshold levels T<sub>1</sub>,T<sub>2</sub>, and T<sub>3</sub>. 
In other words, the PM observes the queue occupancy of the intervals: [0, T<sub>1</sub>], [T<sub>1</sub>, T<sub>2</sub>] etc. 
The values of these levels are unknown and thus are defined using four holes.
For each occupancy level, the PM changes to the associated power profile P<sub>1</sub>, ..., P<sub>4</sub> in {0,1,2}, where numbers 0 through 2 encode the profiles *sleeping*, *idle* and *active}*, respectively. 
The strategy which profile to used for the particular occupy is also unknown and thus defined using another four holes. 
Finally, the queue capacity Q<sub>max</sub> is also unknown and thus the sketch includes in total 9 holes. The following sketch describes the PM (the modules implementing the other components of the server are omitted here for brevity -- the entire sketch is available in benchmark [template](cav21-benchmark/dpm-demo/sketch.templ)).


```math
module PM
    [ToDo] Add domains of the holes
    pm  :  [0..2] init 0; // 0 - sleep, 1 - idle, 2 - active
    [sync0] q <= T1*QMAX -> (pm'=P1);
    [sync0] q > T1*QMAX & q <= T2*QMAX -> (pm'=P2);
    [sync0] q > T2*QMAX & q <= T3*QMAX -> (pm'=P3);
    [sync0] q > T3*QMAX -> (pm'=P4);
endmodule
```

The sketch also includes the domains for each hole. Note that these domains ensures that T<sub>1</sub> < T<sub>2</sub> < T<sub>3</sub>, however PAYNT further supports restrictions --- additional constraints on parameter combinations. 
The resulting sketch describes a *design space* of 10 x 5 x 4 x 3<sup>4</sup> = 16,200 different power managers where the average size of the underlying MC (of the complete system) is around 900 states. 


### Specification of the required behaviour

The goal is to find the concrete power manager, i.e., the instantiation of the holes, that minimizes power consumption while the expected number of lost requests during the operation time of the server is below 1. 
Such specification is formalized as a list of temporal logic formulae in the `PRISM` syntax (the specification is also available within the benchmark directory [here](cav21-benchmark/dpm-demo/sketch.properties):

```shell
R{"lost"}<= 1 [ F "finished" ]  R{"power"}min=? [ F "finished" ]
```

For the given the sketch and specification, PAYNT effectively explores the design space and finds a hole assignment inducing a program that satisfies the specification, provided such assignment exists. 
Otherwise, it reports that such design does not exist.
Executing the following command:

```shell
python3 paynt/paynt.py --project cav21-benchmark/dpm-demo --constants CMAX=10 hybrid
```

### Interpretation of the synthesis results

PAYNT produces the following output containing the hole assignment and the quality wrt. the specification of the corresponding program:

```math
hole assignment: QMAX=5,T1=0,T3=0.7,P1=1,P2=2,P3=2,P4=2
R[exp]{"lost"}=0.6822759696 [F "finished"]
R[exp]{"power"}min=9100.064246 [F "finished"]
```

The obtained optimal power manager has queue capacity 5 with thresholds (after rounding) at 0, 2 and 3.
In addition, the power manager always maintains an active profile unless the request queue is empty, in which case the device is put into an idle state.
This solution leads to the expected number of lost requests of around 0.68 < 1 and the power consumption of 9,100 units. 
PAYNT computes this optimal solution in one minute. Despite of the relatively small family size, PAYNT is about three times faster than a naive enumeration of all solutions. 

We further consider a more complex variant of the synthesis problem inspired by the well-studied model of a dynamical power manager ([DPM](https://ieeexplore.ieee.org/document/7372021)) for complex electronic systems. 
The corresponding sketch describes around 43M available solutions with an the average MC size of 3.6k states (the [sketch](./cav21-benchmark/dpm/sketch.templ) and [specification](./cav21-benchmark/dpm/hard.properties) are available in benchmark [directory](./cav21-benchmark/dpm)). 
While enumeration needs more than ~1 month to find the optimal power manager, PAYNT solves it within 10 hours.


## Evaluating PAYNT 
The [evaluate.md](./cav21-benchmark/evaluate.md) describes the way of recreating the experiments in [1].
Further, it contains the exploring synthesis problems beyond the presented experiment suite.
For more information about these parts, please examine the specified file.


## Testing PAYNT
As we report in the paper, PAYNT is tested with unit tests and regression tests.
These tests currently cover more than 90% of the source code lines.
The unit tests which cover the specific logic components to maintain their correct functionality.
You can run the regression and unit tests (~5 minutes) with the following sequence of commands:

```shell
cd paynt/paynt_tests
python3 -m pytest --cov=./../paynt/ --cov-report term-missing test_synthesis.py test_model_checking.py
```

This command prints the coverage report, displaying the resulting coverage for individual source files.
Our tests currently cover more than `90%` of the source code lines, even though the result shows `82%` because `~10%` of the source code is only temporary functions for debugging purposes that have no functionality.

## Installation

The script will automatically install dependencies and compile prerequisites necessary to run PAYNT. Compilation of the tool and of all of its prerequisites might take a couple of hours. Be aware that upgrading the OS of the VM may cause problems with installation. To accelerate compilation, we recommend enabling multiple CPU cores on your VM. Such multi-core compilation is quite memory-intensive, therefore, we recommend allocating a significant amount of RAM on your VM as well. As a rule of thumb, we recommend allocating at least 2 GB RAM per core. For instance, for a VM with 4 CPU cores and at least 8 GB of RAM, the compilation should take around 30 minutes. Any errors you encounter during the compilation are most likely caused by the lack of memory: try to allocate more RAM for your VM or disable multi-core compilation (see variable `threads` in the script `install.sh`).