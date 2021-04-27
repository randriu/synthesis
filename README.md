# PAYNT

PAYNT (Probabilistic progrAm sYNThesizer) is a tool for automated synthesis of probabilistic programs. PAYNT inputs a program with holes (so-called sketch) and a specification (see below for more information), and outputs concrete hole assignment allowing to satisfy the specification, if such assignment exists. Internally, PAYNT interprets incomplete probabilistic program as a family of Markov chains and uses state-of-the-art synthesis methods on top of the model checker [Storm](https://github.com/moves-rwth/storm) to identify satisfying realization. PAYNT is implemented in python and uses [stormpy](https://github.com/moves-rwth/stormpy) -- python bindings for Storm. This repository contains the source code of PAYNT along with adaptations for [storm](https://github.com/moves-rwth/storm) and [stormpy](https://github.com/moves-rwth/stormpy), prerequisites for PAYNT.

## Image with the pre-installed tool

Pre-installed tool is available in [this Ubuntu 20.04 LTS virtual machine](). Compilation and installation of the tool from scratch on your system or VM will be discussed in the end of this README.

## Initial testing of the artifact

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

Python environment can be deactivated by runnning

```sh
deactivate
```


## Reproducing presented experiments

### Reproducing Table 1

Table 1 reported in our CAV'21 submission presents results of 15 different experiments: 5 benchmarks evaluated using one-by-one enumeration and using advanced synthesis method, where the latter approach is investigated wrt. a hard and an easy property. To run these 15 evaluations, simply navigate to `experiments` folder and run the script:

```sh
cd experiments
./experiment.sh timeout
```

Here, `timeout` is a timeout value for each individual experiment, e.g. '5m' or '2h'. The script will evaluate the benchmarks and, for each experiment, produce a logfile available in `experiments/logs` folder. As soon as all experiments are finished, the script will parse these logfiles and output a table similar to Table 1. This table will be also stored to `experiment/logs/summary.txt`.

### How to select the timeout value

Based on the runtimes reported in the table, you can select a timeout value that will allow you to complete as many experiments as possible within your allocated time. Since 1-by-1 enumeration typically requires more than a day to complete, you might be interested in at least completing synthesis via advanced methods (10 of the 15 presented experiments). Here are some suggested values:

`timeout=5m` will complete 4/10 experiments within 1 hour
`timeout=20m` will complete 6/10 experiments within 3.5 hours
`timeout=1h` will complete 7/10 experiments within 8.5 hours
`timeout=2h` will complete 9/10 experiments within 14 hours (recommended value)
`timeout=12h` will complete 10/10 experiments within 2.5 days

If the experiment associated with one-by-one enumeration hits a timeout, the runtime will be estimated based on the number of rejected assignments. However, in order to obtain reliable estimates, enumeration must run of a significant period of time, i.e. for a couple of hours. If advanced synthesis method will hit a timeout, then, since its performance cannot be estimated in a meaningful way, the corresponding table entry will contain '-'.
Finally, statistics about average MC size are taken from logs associated with advanced synthesis (easy property) and, if the corresponding computation was interrupted, the table entry will again display '-'.

Finally, note that the evaluation of experiments is executed concurrently based on the number `nproc` of (logical) CPUs available on your system/VM. As a result, for a VM having 4 CPU cores, choosing recommended timeout value `timeout=2h` will allow to complete 9/10 experiments associated with advanced synthesis approaches as well as produce reliable estimates for 1-by-1 enumeration within 3-4 hours. It might be a good idea to let the script run overnight. The log files for [TBA]

**Please note** that all of the discussed synthesis methods, specifically advanced methods (CEGIS, CEGAR, hybrid) are subject to some nondeterminism during their execution, and therefore during your particular evaluation you might obtain slightly different execution times. Furthermore, the switching nature of the integrated method heavily depends on the timing, which can again result in fluctutations in the observed measurements. However, the qualitative conclusions -- e.g. overall performance of hybrid vs 1-by-1 enumeration or comparative runtimes of synthesizing wrt. easy vs hard property -- should be preserved. Also remember that the provided runtimes for different timeout settings were estimated based on the experience with our CPU (Intel i5-8300H, 4 cores at 2.3 GHz) and that the evaluation might last longer/shorter on your machine.

### Reproducing Figure 5

Figure 5 was created manually based on the output of PAYNT when synthesizing an optimal controller (hard property) for __Maze__ model. To check the result, you need to let at least the advanced method finish (recommended value `timeout=2h` will guarantee this even on slower CPUs). Alternatively, you can specifically run computation of this model (do not forget to activate python environment):

```sh
python3 paynt/paynt.py --project cav21-benchmark/maze --properties hard.properties hybrid
```

The last lines of the output (or the last lines of the corresponding log file) should contain the synthesis summary. In particular, PAYNT will display the hole assignment that induces an optimal controller:

```sh
hole assignment: M_0_1=1,M_0_2=0,M_0_3=1,M_0_4=0,M_0_5=0,M_0_6=0,M_1_1=1,M_1_2=1,M_1_3=1,M_1_4=0,M_1_5=1,M_1_6=0,P_0_1=2,P_0_2=4,P_0_3=3,P_0_4=4,P_0_5=1,P_1_1=2,P_1_2=2,P_1_3=3,P_1_4=4,P_1_5=3
```

The holes are of the form `P_m_o` or `M_m_o`, where `m` is a memory value (one bit, 0 or 1) and `o` represents one of six possible wall configurations (observations) encoded in colours on Figure 5:

- `o=1` corresponds to red states (0)
- `o=2` corresponds to orange states (1,3)
- `o=3` corresponds to green states (2)
- `o=4` corresponds to gray states (4)
- `o=5` corresponds to purple states (4)
- `o=4` corresponds to gray states (4)

Semantics of hole `P_m_o` is 'direction chosen when observing `o` with memory value `m`. The direction is an integer from 1 to 4 representing north, east, south and west respectively. Similarly, semantics of hole `M_m_o` is 'memory update after moving from location `o` with memory value `m`. You can see that, for instance, in location 0, hole assignments `P_0_1 = P_1_1 = 2` and `M_0_1 = M_1_1 = 1` imply that the robot will always go east and will set its memory bit to 1. Note that there are multiple optimal controllers and you might obtain e.g. symmetric hole assignments (i.e. the one in which 0's and 1's are swapped in memory updates) that imply expected time 8.13 steps to reach the exit.

## Syntax of the PAYNT's command
PAYNT is started using the command in the following form:

```shell
python3 paynt/paynt.py [OPTIONS] [hybrid|cegar|cegis|onebyone]
```
where the options can be: 

- ``--project PATH``: specifies the path to the benchmark folder [required]
- ``--sketch FILE_IN_PATH``: specifies the file containing the template description in the PRISM guarded command language [default: ``PATH/sketch.templ``]
- ``--properties FILE_IN_PATH``: specifies the file containing specifications to synthesise against [default: ``PATH/sketch.properties``]
- ``--constants TEXT``: specifies the values of constants that are undefined in the sketch and are not holes, in the form: ``c1=0,c2=1``
- ``--short-summary``: prints also short summary of the synthesis results consisting of primary information
- ``--ce-quality``: evaluates the counter-example quality when usage the hybrid approach
- ``--ce-maxsat``: enables the construction of counter-examples using MaxSat approach and also their evaluation
- ``--help``: shows the help message of the PAYNT and exit the program

For instance, PAYNT can be run most simply as follows: 

```shell
python3 paynt/paynt.py --project cav21-benchmark/dpm-demo --constants CMAX=2 hybrid
```

The `--project` option specifies the path to the benchmark folder.
PAYNT inspects the content of this folder to find the required files for the synthesis process: `sketch.templ` and `sketch.properties`.
The first file contains the template description, and the second one the specifications.
The `--constants` option specifies the value for an undefined variable in the sketch, which is not considered as a synthesised hole.
Finally, the last argument specifies the selected synthesis method: `hybrid`.

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
On average, each member has on average 1.3K states when was constructed MDP at AR and 172 states when analysing DTMC at CEGIS.
We can also see that the problem found the optimal solution satisfying also given formula and that on our machine took 3 AR, 1354 CEGIS iterations and 23 seconds to prove this.
The last lines show the synthesised solution with concrete instantiations of holes and the found optimal value.
Notice that only the hybrid method contains both MDP- and DTMC-related information since CEGIS never deals with MDPs, and AR with DTMCs.

Furthermore, when running benchmark using the hybrid approach, you can specify an additional `--ce-quality` option that evaluates the counterexample quality. 
The summary will contain two additional rows with information about the quality as well as the construction times of the counterexamples.
You will notice that the quality of the MaxSat method will be reported as 0, since this value was not computed at all. 
We do not compute the MaxSat quality implicitly since this computation is often very time-demanding and would complicate collecting data about the novel approach for CE construction. 
To enable evaluation of the MaxSat approach, you can specify an additional option `--ce-maxsat`.

### Sketching language

PAYNT takes as an input a sketch -- program description in `PRISM` (or `JANI`) language containing some undefined parameters (holes) with associated options from domains -- and a specification given as a list of temporal logic constraints (interpreted as a conjunction of theses constrains) possibly including an optimal objective. Before explaining the sketching language, let us briefly present the key ideas of the `PRISM` language -- the full documentation of the language is available [here](https://www.prismmodelchecker.org/manual/ThePRISMLanguage/Introduction).

A `PRISM` program consists of one or more reactive modules that may interact with each other using synchronisation. A module has a set of (bounded) variables that span its state space. Possible transitions between states of a module are described by a set of guarded commands of the form:

```math
[action] guard -> prob_1 : update_1 + ... + prob_n : update_n; 
```

If the `guard` evaluates to true, an update of the variables is chosen according to the probability distribution given by expressions `p_1` through `p_n`. The `actions` are used to force two or more modules to make the command simultaneously (i.e. to synchronise).

Recall that sketch is a `PRISM` program with holes and allows us to compactly describe a set of candidates program.
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
Such specification is formalized as a list of temporal logic formulae in the `PRISM` syntax (the specification is also available within the benchmark directory [here](cav21-benchmark/dpm-demo/sketch.properties)):

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


## Exploring synthesis problems beyond the presented experiment suit

In order to further investigate the performance of the synthesis methods, we suggest performing some additional experiments that focus on three different aspects having the essential impact on the runtime of the synthesis process. 
These experiments will be based on experimenting with the provided [cav21-benchmark](./cav21-benchmark).
Therefore, before proceeding with the suggestions below, make sure to make a copy of this directory if you haven't evaluated the experiment suit presented in the paper via the [script](./experiments/experiment.sh) for running experiments.

#### Modifying the family size
Changing the family size of particular models can require nontrivial changes in the model definition and thus a certain level of understanding of the models. 
However, there are some models where the family size can be easily changed. For example, the size of the larger variant of the model can be modified in the following way:
Go to the following [sketch](./cav21-benchmark/herman/sketch.templ) and reduce the domains of the selected options (holes), e.g., modify the part of the file (lines `47-53`) in the following way:

```shell
hole int M0LFAIR in {0,1,2,3};
hole int M0HFAIR in {0,1,2,3};
hole int M1LFAIR in {0,1,2,3};
hole int M1HFAIR in {0,1,2,3};
hole int MxxA in {0,1};
hole int MxxB in {0,1};
hole int MxxC in {0,1};
```

This greatly reduces the number of randomization strategies of the protocol and thus the family size. 
We can now run optimal synthesis to find the best solution in the reduced family:

```shell
python3 paynt/paynt.py --project cav21-benchmark/herman --properties hard.properties hybrid
python3 paynt/paynt.py --project cav21-benchmark/herman --properties hard.properties cegar
```

Notice that this family contains only 2<sup>11</sup> members (as opposed to 3M members in the original model. 
You can see that the optimal value is now 24 (expected) steps and that the summary also contains the parameter assignment for this optimal member. 
If we enlarge this family by adding more strategies:

```shell
hole int M0LFAIR in {0,1,2,3,4,5,6};
hole int M0HFAIR in {0,1,2,3,4,5,6};
hole int M1LFAIR in {0,1,2,3,4,5,6};
hole int M1HFAIR in {0,1,2,3,4,5,6};
hole int MxxA in {0,1};
hole int MxxB in {0,1};
hole int MxxC in {0,1};
```

computing the optimal value now takes some more time, but the obtained value is now around 12.4 (we recommend computing it using the hybrid approach), meaning that we have found a member that can stabilize much faster. 
What happened here is that we have added some strategies to our protocol (the family now has around 19k members) and, fortunately, some of these strategies were better (wrt. the specification) than existing ones. 
Feel free to experiment with these parameter domains -- you can even try to assign different domains to different parameters `MxyFAIR` -- but be aware that the family blows up really fast and that CEGAR will struggle even with families having as few as 80k members.

#### Modifying the (average) size of the family members
Most of our models ([Grid](./cav21-benchmark/grid), [Maze](./cav21-benchmark/maze), [DPM](./cav21-benchmark/dpm) and [Herman](./cav21-benchmark/herman)) include parameter `CMAX` allowing users to change size of the particular family members (i.e. the underlying DTMCs) -- increasing this parameter increases the average size of the members. 
Please note that most properties are linked with this parameter and thus changing the parameter can change feasibility outcome and can even make some properties invalid. 
For example, you can try to analyze [Maze](./cav21-benchmark/maze) benchmark: 

```shell
python3 paynt/paynt.py --project cav21-benchmark/maze --properties easy.properties hybrid
python3 paynt/paynt.py --project cav21-benchmark/maze --properties easy.properties cegar
```
and then modify the parameter `CMAX` (line `22`) in [sketch](./cav21-benchmark/maze/sketch.templ):

```
const int CMAX = 100;
```

and rerun the two commands above. 
You can inspect that, although the number of iterations has not changed (the family size remained the same) the size of underlying DTMCs as well as the size of quotient MDPs has increased and therefore the synthesis now takes significantly more time.

#### Modifying threshold of the given property

The property thresholds for the synthesis problems can be changed in files `.properties` that are stored in particular benchmark folders. 
For example, you can try to run 

```shell
python3 paynt/paynt.py --project cav21-benchmark/grid --properties easy.properties hybrid
python3 paynt/paynt.py --project cav21-benchmark/grid --properties easy.properties cegis
```

and then modify the property threshold in the [file](./cav21-benchmark/grid/easy.properties):

```
P>=0.927 [ F "goal" & c<CMAX ]
```

and rerun the command above. 
You can see that this specification is much harder to synthesize, yet overall the problem is still unfeasible. 
If we decrease the threshold even further:

```
P>=0.926 [ F "goal" & c<CMAX ]
```

then the synthesizer will be able to provide a satisfying parameter assignment. 
Also note that assignments provided by individual synthesis methods may differ since in this case the family contains multiple feasible solutions.

#### TBD -- add more.

## Installation

The script will automatically install dependencies and compile prerequisites necessary to run PAYNT. Compilation of the tool and of all of its prerequisites might take a couple of hours. Be aware that upgrading the OS of the VM may cause problems with installation. To accelerate compilation, we recommend enabling multiple CPU cores on your VM. Such multi-core compilation is quite memory-intensive, therefore, we recommend allocating a significant amount of RAM on your VM as well. As a rule of thumb, we recommend allocating at least 2 GB RAM per core. For instance, for a VM with 4 CPU cores and at least 8 GB of RAM, the compilation should take around 30 minutes. Any errors you encounter during the compilation are most likely caused by the lack of memory: try to allocate more RAM for your VM or disable multi-core compilation (see variable `threads` in the script `install.sh`).