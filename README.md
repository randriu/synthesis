# PAYNT

PAYNT (Probabilistic progrAm sYNThesizer) is a tool for the automated synthesis of probabilistic programs. PAYNT takes a program with holes (a so-called sketch) and a PCTL specification (see below for more information), and outputs a concrete hole assignment that yields a satisfying program, if such an assignment exists. Internally, PAYNT interprets the incomplete probabilistic program as a family of Markov chains and uses state-of-the-art synthesis methods on top of the model checker [Storm](https://github.com/moves-rwth/storm) to identify satisfying realization. PAYNT is implemented in python and uses [Stormpy](https://github.com/moves-rwth/stormpy) -- python bindings for Storm. This repository contains the source code of PAYNT along with adaptations for [Storm](https://github.com/moves-rwth/storm) and [Stormpy](https://github.com/moves-rwth/stormpy), prerequisites for PAYNT. PAYNT is hosted on [github](https://github.com/gargantophob/synthesis).

PAYNT is described in 
- [1] PAYNT: A Tool for Inductive Synthesis of Probabilistic Programs by Roman Andriushchenko, Milan Ceska, Sebastian Junges, Joost-Pieter Katoen and Simon Stupinsky

Most of the algorithms are described in 
- [2] Inductive Synthesis for Probabilistic Programs Reaches New Horizons by Roman Andriushchenko, Milan Ceska, Sebastian Junges, Joost-Pieter Katoen, TACAS 2021
- [3] Counterexample-Driven Synthesis for Probabilistic Program Sketches by Milan Ceska, Christian Hensel, Sebastian Junges, Joost-Pieter Katoen, FM 2019.
- [4] Shepherding Hordes of Markov Chains by Milan Ceska, Nils Jansen, Sebastian Junges, Joost-Pieter Katoen, TACAS 2019

## Image with the pre-installed tool

An image of an Ubuntu 20.04 LTS virtual machine with the pre-installed tool is available on [zenodo](https://doi.org/10.5281/zenodo.4726056). Compilation and installation of the tool from scratch on your system or VM will be discussed in the end of this README. To boot the VM, you will need [VirtualBox](https://www.virtualbox.org/).

username: cav21
password: cav21

Home folder `/home/cav21` contains the paper, this README and folder `synthesis` containing the artifact.

## Getting started with PAYNT 

Having the tool installed, you can quickly test it by navigating to the tool folder, activating the python environment and asking PAYNT to evaluate a simple synthesis problem:

```sh
cd /home/cav21/synthesis
source env/bin/activate
python3 paynt/paynt.py --project cav21-benchmark/dpm-demo  --properties sketch.properites hybrid
```

The syntax of the command is described in more detail in the following chapters of this README.
For now, we can see that we ask PAYNT to look at the sketch (located in directory ``cav21-benchmark/dpm-demo``) for the dynamic power manager discussed in Section 2 in [1] and synthesize it wrt. specification in file ``cav21-benchmark/dpm-demo/sketch.properties`` using the advanced hybrid approach.
The tool will print a series of log messages and, in the end, a short summary of the synthesis process, similar to the one below:

```
formula 1: R[exp]{"requests_lost"}<=1 [F "finished"]
optimal setting: formula: R[exp]{"power"}min=? [F "finished"]; direction: min; eps: 0.0

method: Hybrid, synthesis time: 12.39 s
number of holes: 7, family size: 12150
super MDP size: 1502, average MDP size: 1502, MPD checks: 2, iterations: 1
average DTMC size: 172, DTMC checks: 2708, iterations: 1354

optimal: 9100.064246
hole assignment: P1=1,P2=0,P3=0,P4=2,T1=0.0,T3=0.8,QMAX=5
```
The contents of such summary will be again discussed later.
Nonetheless, we can see that the tool reports a hole assignment that yields the optimal program.

The python environment can be deactivated by runnning

```sh
deactivate
```

### Contents of this README

The remainder of this README fully describes how to synthesize probabilistic programs using PAYNT.
In particular, we will discuss
- how to run PAYNT
- how to read the output of PAYNT
- how to create your own sketches and specifications

In the end, we will discuss how to install and test PAYNT on your system.
Finally, file [experiments/README_evaluation.md](./experiments/README_evaluation.md) contains instructions on **how to reconstruct experiments discussed in [1]**.
The file also contains exploration of synthesis problems beyond the presented experiment suite.

## Synthesizing probabilistic programs with PAYNT

### Running PAYNT
PAYNT is executed using the command in the following form:

```shell
python3 paynt/paynt.py [OPTIONS] [hybrid|cegar|cegis|onebyone]
```
where the most important options are: 
- ``--project PROJECT``: specifies the path to the benchmark folder [required]
- ``--sketch FILE_IN_PROJECT``: specifies the file containing the template description in the PRISM guarded command language [default: ``sketch.templ``]
- ``--properties FILE_IN_PROJECT``: specifies the file containing specifications to synthesise against [default: ``sketch.properties``]
- ``--constants STRING``: specifies the values of constants that are undefined in the sketch and are not holes, in the form: ``c1=0,c2=1`` as standard for PRISM programs.
- 
For instance, here is a simple PAYNT call:

```shell
python3 paynt/paynt.py --project cav21-benchmark/grid --sketch sketch.templ --properties easy.properties hybrid
```

The `--project` option specifies the path to the benchmark folder: now we will investigate the __Grid__ model discussed in [1].
PAYNT inspects the content of this folder and locates the required files for the synthesis process: the sketch and the specification list.
In the example above, the sketch file is `cav21-benchmark/grid/sketch.templ` (in this case, `--sketch` option could have been omitted), the specification file is `cav21-benchmark/grid/easy.properties` and the sketch does not have undefined constants, only holes.
Finally, the last argument specifies the selected synthesis method: `hybrid`.

PAYNT has some advanced options for developers.
- ``--help``: shows the help message of the PAYNT and exit the program
- ``--short-summary``: also prints a one-line short summary of the synthesis
- ``--ce-maxsat``: enables the construction of counter-examples using MaxSat approach and also their evaluation. For recreating experiments in [2].
- ``--ce-quality``: evaluates the counter-example quality when using the hybrid approach. Used to recreate experiments in [2].


### Reading the output of PAYNT

Running PAYNT produces a sequence of log and a summary printed at the end of the synthesis process.
For instance, if we run

```sh
python3 paynt/paynt.py --project cav21-benchmark/dpm-demo hybrid
```
we obtain the following summary:

```shell
formula 1: R[exp]{"requests_lost"}<=1 [F "finished"]
optimal setting: formula: R[exp]{"power"}min=? [F "finished"]; direction: min; eps: 0.0

method: Hybrid, synthesis time: 67.62 s
number of holes: 7, family size: 12150
super MDP size: 1502, average MDP size: 956, MPD checks: 116, iterations: 59
average DTMC size: 234, DTMC checks: 14206, iterations: 7103

optimal: 9100.064246
hole assignment: P1=1,P2=2,P3=2,P4=2,T1=0.0,T3=0.8,QMAX=5
```

This summary contains information about the synthesized sketch as well as the results of the synthesis process.
The first lines repeat the synthesised specifications and, if included, the optimizing property.
Next, the synthesis was carried out using the hybrid method and it on our machine it took 68 seconds.
We can see that this particular DPM benchmark contains 7 holes (parameters) and 12K family members.
The following lines are statistics about deductive (MDP-based) or inductive (counterexample-based) analysis, including sizes of analyzed MDPs/DTMCs, number of particular model checking calls, overall iterations count etc.
Notice that only the hybrid method contains both MDP- and DTMC-related information since CEGIS never deals with MDPs, and AR works exclusively with MDPs.

Finally, the last lines show the synthesis result.
In our case, PAYNT printed a hole assignment yielding optimal solution as well as the induced optimal value.

### Sketching language

PAYNT takes as an input a sketch -- program description in `PRISM` (or `JANI`) language containing some undefined parameters (holes) with associated options from domains -- and a specification given as a list of temporal logic constraints (interpreted as a conjunction of theses constrains) possibly including an optimal objective. Before explaining the sketching language, let us briefly present the key ideas of the `PRISM` language -- the full documentation of the language is available [in the PRISM manual](https://www.prismmodelchecker.org/manual/ThePRISMLanguage/Introduction).

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
Finally, the queue capacity Q<sub>max</sub> is also unknown and thus the sketch includes in total 9 holes.
In the sketch, the definition of the hole takes place outside of any module (typically in the beginning of the program) and must include its data type (int or double) as well as the domain:

```math
// profiles desired at observation levels
// 0 - sleep, 1 - idle, 2 - active
hole int P1 in {0,1,2};
hole int P2 in {0,1,2};
hole int P3 in {0,1,2};
hole int P4 in {0,1,2};

// observation level thresholds
hole double T1 in {0.0,0.1,0.2,0.3,0.4};
hole double T2 in {0.5};
hole double T3 in {0.6,0.7,0.8};

// queue size
hole int QMAX in {1,2,3,4,5,6,7,8,9,10};
```

The following sketch fragment describes the module for the described power manager. The modules implementing other components of the server are omitted here for brevity -- the entire sketch is available in [this file](cav21-benchmark/dpm-demo/sketch.templ).

```math
module PM
    pm  :  [0..2] init 0; // 0 - sleep, 1 - idle, 2 - active
    [tick0] q <= T1*QMAX -> (pm'=P1);
    [tick0] q > T1*QMAX & q <= T2*QMAX -> (pm'=P2);
    [tick0] q > T2*QMAX & q <= T3*QMAX -> (pm'=P3);
    [tick0] q > T3*QMAX -> (pm'=P4);
endmodule
```

Note that the domains of the holes defined above ensure that T<sub>1</sub> < T<sub>2</sub> < T<sub>3</sub>, however PAYNT further supports restrictions --- additional constraints on parameter combinations. 
The resulting sketch describes a *design space* of 10 x 5 x 4 x 3<sup>4</sup> = 16,200 different power managers where the average size of the underlying MC (of the complete system) is around 900 states. 

### Specification of the required behaviour

The goal is to find the concrete power manager, i.e., the instantiation of the holes, that minimizes power consumption while the expected number of lost requests during the operation time of the server is at most 1. 
In general, a specification is formalized as a list of temporal logic formulae in the [`PRISM` syntax](https://www.prismmodelchecker.org/manual/PropertySpecification/Introduction).
Here is a specification available within the benchmark directory [here](cav21-benchmark/dpm-demo/sketch.properties):

```math
R{"requests_lost"}<= 1 [ F "finished" ]
R{"power"}min=? [ F "finished" ]
```

We can see that the speicification file can additionally contain at most one optimizing property.
Furthermore, one can specify relative precision for satisfying such criterion (epsilon-optimality), e.g.

```math
R{"power"}min{0.05}=? [ F "finished" ]
```

For the given sketch and specification, PAYNT effectively explores the design space and finds a hole assignment inducing a program that satisfies the specification, provided that such assignment exists.
Otherwise, it reports that such design does not exist.
If the specification also includes an optimizing criterion, PAYNT will find hole assignments that satisfies constraints in the specification __and__ has an optimal behaviour.

### Interpretation of the synthesis results

PAYNT produces the following output containing the hole assignment and the quality wrt. the specification of the corresponding program:

```math
optimal: 9100.064246
hole assignment: P1=1,P2=2,P3=2,P4=2,T1=0.0,T3=0.8,QMAX=5
```

The obtained optimal power manager has queue capacity 5 with thresholds (after rounding) at 0, 2 and 4.
In addition, the power manager always maintains an active profile unless the request queue is empty, in which case the device is put into an idle state.
This solution guarantees expected number of lost requests to be at most one and has the power consumption of 9,100 units. 
To double-check that there are no controllers having expected power consumption less than 9100, we can modify the specification file `cav21-benchmark/dpm-demo/sketch.properties` as follows:

```math
R{"requests_lost"} <= 1 [ F "finished" ]
R{"power"}<=9100 [ F "finished" ]
```

Running PAYNT again (with hybrid synthesis approach) will produce the following result

```shell
formula 1: R[exp]{"requests_lost"}<=1 [F "finished"]
formula 2: R[exp]{"power"}<=9100 [F "finished"]

method: Hybrid, synthesis time: 67.52 s
number of holes: 7, family size: 12150
super MDP size: 1502, average MDP size: 962, MPD checks: 116, iterations: 59
average DTMC size: 237, DTMC checks: 14126, iterations: 7063

feasible: no
```
from which we can see that PAYNT indeed proved non-existence of a better solution.

We might further consider a more complex program sketch __Grid__ (discussed in [1]), where we synthesize controller for a robot in an unpredictable environment.

```shell
python3 paynt/paynt.py --project cav21-benchmark/grid --properties easy.properties hybrid
```

This sketch describes a family of 65K members, where each member has, on average 1225 states.
Even though this is a much larger family with much larger chains than in the sketch considered before, the pruning ability of the advanced hybrid approach allows PAYNT to handle this specification in a matter of seconds.
Meanwhile, one-by-one enumeration

```shell
python3 paynt/paynt.py --project cav21-benchmark/grid --properties easy.properties onebyone
```
might take up to 20 minutes.

## Testing PAYNT
As reported in the paper, PAYNT is tested with unit tests and regression tests.
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

To install the tool on your system, download the repository, navigate to the root folder of the tool and simply run

```shell
./install.sh
```

The script will automatically install dependencies and compile prerequisites necessary to run PAYNT. Compilation of the tool and of all of its prerequisites might take a couple of hours. Be aware that upgrading the OS of the VM may cause problems with installation. To accelerate compilation, we recommend enabling multiple CPU cores on your VM. Such multi-core compilation is quite memory-intensive, therefore, we recommend allocating a significant amount of RAM on your VM as well. As a rule of thumb, we recommend allocating at least 2 GB RAM per core. For instance, for a VM with 4 CPU cores and at least 8 GB of RAM, the compilation should take around 30 minutes. Any errors you encounter during the compilation are most likely caused by the lack of memory: try to allocate more RAM for your VM or disable multi-core compilation (see variable `threads` in the script `install.sh`). The corresponding VM containing pre-compiled tool was created by installing the tool using the script above.

## Repository Structure
The directory [cav21-benchmark](./cav21-benchmark) includes the benchmarks evaluated in the paper.
The directory [experiments](./experiments) includes the scripts to recreate the experiments in our paper and [manual](./experiments/README_evaluation.md) for their reproduction.
The main project [directory](./paynt) includes all PAYNT source [files](./paynt/paynt), test [files](./paynt/paynt_tests) and also configuration files.
The fixed installation dependencies for installing PAYNT are in the [prereuisites](./prerequisites), as well as in the [storm](./storm) and [stormpy](./stormpy) directories.
The [workspace](./workspace) directory includes the various versions of benchmarks used, e.g. in the previous publications, and some of them we present in the last section of evaluation [README](./experiments/README_evaluation.md).
Last but not least, at the top of the repository is located our [paper](./cav21-paper.pdf), [README.md](./README.md) file and the [script](./install.sh) to install the tool on your system.
