# PAYNT

PAYNT (Probabilistic progrAm sYNThesizer) is a tool for automated synthesis of probabilistic programs. PAYNT inputs a program with holes (so-called sketch) and a specification, and outputs concrete hole assignment allowing to satisfy the specification, if such assignment exists. Internally, PAYNT interprets incomplete probabilistic program as a family of Markov chains and uses state-of-the-art synthesis methods on top of the model checker [Storm](https://github.com/moves-rwth/storm) to identify satisfying realization. PAYNT is implemend in python and uses [stormpy](https://github.com/moves-rwth/stormpy) -- python bindings for Storm. This repository contains the source code of PAYNT along with adaptations for [storm](https://github.com/moves-rwth/storm) and [stormpy](https://github.com/moves-rwth/stormpy), prerequisites for PAYNT.

## Image with the pre-installed tool

Pre-installed tool is available in [this Ubuntu 20.04 LTS virtual machine](). Compilation and installation of the tool from scratch on your system or VM will be discussed in the end of this README.

## Initial testing of the artifact

Having the tool installed, you can quickly test it by activating the python envorinment and asking PAYNT to evaluate a simple synthesis problem:

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

Based on the runtimes reported in the table, you can select a timeout value that will allow you to complete as many experiments as posssible within your allocated time. Since 1-by-1 enumeration typically requires more than a day to complete, you might be interested in at least completing synthesis via advanced methods (10 of the 15 presented experiments). Here are some suggested values:

`timeout=5m` will complete 4/10 experiments within 1 hour
`timeout=20m` will complete 6/10 experiments within 3.5 hours
`timeout=1h` will complete 7/10 experiments within 8.5 hours
`timeout=2h` will complete 9/10 experiments within 14 hours (recommended value)
`timeout=12h` will complete 10/10 experiments within 2.5 days

If the experiment associated with one-by-one enumeration hits a timeout, the runtime will be estimated based on the number of rejected assignments. However, in order to obtain reliable estimates, enumeration must run of a significant period of time, i.e. for at a couple of hours. If advanced synthesis method will hit a timeout, then, since its performance cannot be estimated in a meaningful way, the corresponding table entry will contain '-'.
Finally, statistics about average MC size are taken from logs associated with advanced synthesis (easy property) and, if the corresponding computation was interrupted, the table entry will again display '-'.

Finally, note that the evaluation of experiments is executed concurrently based on the number `nproc` of (logical) CPUs available on your system/VM. As a result, for a VM having 4 CPU cores, choosing recommended timeout value `timeout=2h` will allow to complete 9/10 experiments associated with advanced synthesis approaches as well as produce reliable estimates for 1-by-1 enumeration within 3-4 hours. It might be a good idea to let the script run overnight.

TODO LOG FILES ARE AVAILABLE

**Please note** that all of the discussed synthesis methods, specifically advanced methods (CEGIS, CEGAR, hybrid) are subject to some nondeterminism during their execution, and therefore during your particular evaluation you might obtain slightly different execution times. Furthermore, the switching nature of the integrated method heavily depends on the timing, which can again result in fluctutations in the observed measurements. However, the qualitative conclusions -- e.g. overall performance of hybrid vs 1-by-1 enumeration or comparative runtimes of synthesizing wrt. easy vs hard property -- should be preserved. Also remember that the provided runtimes for different timeout settings were estimated based on the experience with our CPU (Intel i5-8300H, 4 cores at 2.3 GHz) and that the evaluation might last longer/shorter on your machine.

### Reproducing Figure 5

Figure 5 was created manually based on the PAYNT output of optimal synthesis (hard property) for __Maze__ model. To check the result, you need to let at least the advanced method finish (recommended value `timeout=2h` will guarantee this even on slower CPUs). Alternatively, you can specifically run computation of this model (do not forget to activate python environment):

```sh
python3 paynt/paynt.py --project cav21-benchmark/maze --properties hard.properties hybrid
```

The last lines of the output (or the last lines of the corresponding log file) should contain the synthesis summary. In particular, PAYNT will display the hole assignment that induces an optimal controller:

```sh
hole assignment: M_0_1=1,M_0_2=0,M_0_3=1,M_0_4=0,M_0_5=0,M_0_6=0,M_1_1=1,M_1_2=1,M_1_3=1,M_1_4=0,M_1_5=1,M_1_6=0,P_0_1=2,P_0_2=4,P_0_3=3,P_0_4=4,P_0_5=1,P_1_1=2,P_1_2=2,P_1_3=3,P_1_4=4,P_1_5=3
```

The holes are of the form `M_m_c` or `P_m_c`, where `m` is a memory value (one bit, 0 or 1) and `o` represents one of six possible wall configurations (observations):

- `o=1` corresponds to red states (0)
- `o=2` corresponds to orange states (1,3)
- `o=3` corresponds to green states (2)
- `o=4` corresponds to gray states (4)
- `o=5` corresponds to purple states (4)
- `o=4` corresponds to gray states (4)






## How to run synthesis manually

The remainder of this README explains how to run dynasty tool manually to help you set up your own experiments. First, do not forget to activate python environment:

```sh
source env/bin/activate
```

Recall the dynasty call mentioned above:

```sh
python3 dynasty/dynasty.py --project tacas21-benchmark/grid --properties easy.properties hybrid
```

The first option `--project` specifies the path to the benchmark folder. Inspect the contents of this folder: it contains the template description (`sketch.templ`) in the PRISM guarded command language, a file (`sketch.allowed`) containing possible values for all parameters and two files (`easy.properties` and `hard.properties`) containing specifications. To select a specification to synthesize agains, we use option `--properties`. Finally, the last argument specifies the synthesis method: `hybrid`, `cegar`, `cegis` or `onebyone`. For instance, to evaluate this benchmark using CEGIS, simply run

```sh
python3 dynasty/dynasty.py --project tacas21-benchmark/grid --properties easy.properties cegis
```

The summary printed in the end contains some info abount the synthesis process: benchmark statistics, synthesis time, number of iterations, whether the synthesis problem is feasible etc. We can see that this particular Grid benchmark contains 8 holes (parameters) and 65k members, each having 1.2k states on average -- you can check that these data correspond to the ones reported in Table 1. We can also see that the problem was unfeasible and that on our machine it took CEGIS 613 iterations and 30 seconds to prove this -- you can cross-reference these data with the ones reported in the first row of Table 2. Notice that, contrary to the summary provided by running the hybrid method, this summary does not contain MDP-related information (average MDP size, number of MDP model checks etc.) since CEGIS never deals with MDPs. Similarly, summary provided by running CEGAR (this evaluation will run for about eight minutes):

```sh
python3 dynasty/dynasty.py --project tacas21-benchmark/grid --properties easy.properties cegar
```

will not contain information about DTMC size. Furthermore, when evaluating benchmark using the hybrid approach, you can specify an additional `--ce-quality` option that evaluates the counterexample quality:

```sh
python3 dynasty/dynasty.py --project tacas21-benchmark/grid --properties easy.properties hybrid --ce-quality
```

In this case, the summary will contain two additional rows with information about the quality as well as the construction times of the counterexamples, as discussed in the left-hand side of Table 2. You will notice that the quality of the MaxSat method will be reported as 0, since this value was not computed at all -- we do not compute the MaxSat quality implicitly since this computation is often very time-demanding and would complicate collecting data about the novel approach for CE construction. To enable evaluation of the MaxSat approach, you can specify an additional option `--ce-maxsat`:

```sh
python3 dynasty/dynasty.py --project tacas21-benchmark/grid --properties easy.properties hybrid --ce-quality --ce-maxsat
```

You can cross-reference the obtained summaries with the values reported in the first row of Table 2. 

## Exploring synthesis problems beyond the presented experiment suit

In order to further investigate the performance of the synthesis methods, we suggest to perform some additional experiments that focus on three different aspects having the essential impact on the runtime of the synthesis process. These experiments will be based on experimenting with the provided tacas21-benchmark, therefore, before proceeding with the suggestions below, make sure to make a copy of this directory if haven't evaluated the experiment suit presented in the paper via the `experiment.sh` suit.

#### Modifying the family size
Changing the family size of particular models can require nontrivial changes in the model definition and thus a certain level of understanding of the models. However, there are some models where the family size can be easily changed. For example, the size of the larger variant of the model can be modified in the following way:
Go to `tacas21-benchmark/herman2_larger/sketch.allowed` and reduce the domains of the selected options (holes), e.g., modify the file in the following way:

```
M0LFAIR;0;1;2
M0HFAIR;0;1;2
M1LFAIR;0;1;2
M1HFAIR;0;1;2
MxxA;0;1
MxxB;0;1
MxxC;0;1
```

This greatly reduces the number of randomization strategies of the protocol and thus the family size. We can now run optimal synthesis to find the best solution in the reduced family:

```sh
python3 dynasty/dynasty.py --project tacas21-benchmark/herman2_larger --properties none.properties --optimality 0.optimal hybrid
python3 dynasty/dynasty.py --project tacas21-benchmark/herman2_larger --properties none.properties --optimality 0.optimal cegar
```

Notice that this family contains only six hundred members (as opposed to 3M members in the original model. You can see that the optimal value is now 35.6 (expected) steps and that the summary also contains the parameter assignment for this optimal member. If we enlarge this family by adding more strategies:

```
M0LFAIR;0;1;2;3;4;5;6
M0HFAIR;0;1;2;3;4;5;6
M1LFAIR;0;1;2;3;4;5;6
M1HFAIR;0;1;2;3;4;5;6
MxxA;0;1
MxxB;0;1
MxxC;0;1
```

computing the optimal value now takes some more time, but the obtained value is now around 12.3 (we recommend computing it using the hybrid approach), meaning that we have found a member that can stabilize much faster. What happened here is that we have added some strategies to our protocol (the family now has around 19k members) and, fortunately, some of these strategies were better (wrt. the specification) than existing ones. Feel free to experiment with these parameter domains -- you can even try to assign different domains to different parameters `MxyFAIR` -- but be aware that the family blows up really fast and that CEGAR will struggle even with families having as few as 80k members.

#### Modifying the (average) size of the family members
Most of our models (Grid, Maze, DPM and Herman) include parameter CMAX allowing users to change size of the particular family members (i.e. the underlying DTMCs) -- increasing this parameter increases the average size of the members. Please note that most properties are linked with this parameter and thus changing the parameter can change feasibility outcome and can even make some properties invalid. For example, you can try to analyze maze benchmark: 

```sh
python3 dynasty/dynasty.py --project tacas21-benchmark/maze --properties easy.properties hybrid
python3 dynasty/dynasty.py --project tacas21-benchmark/maze --properties easy.properties cegar
```
and then modify the parameter CMAX in file tacas21-benchmark/maze/sketch.templ:

```
const int CMAX = 200;
```

and rerun the two commands above. You can inspect that, although the number of iterations has not changed (the family size remained the same) the size of underlying DTMCs as well as the size of quotient MDPs has increased and therefore the synthesis now takes significantly more time.

#### Modifying threshold of the given property

The property thresholds for the synthesis problems can be changed in files .properties that are stored in particular benchmark folders. For example, you can try to run 

```sh
python3 dynasty/dynasty.py --project tacas21-benchmark/grid --properties easy.properties hybrid
python3 dynasty/dynasty.py --project tacas21-benchmark/grid --properties easy.properties cegis
```

and then modify the property threshold in the file `tacas21-benchmark/grid/easy.properties`:

```
P>=0.927 [ F "goal" & c<CMAX ]
```

and rerun the command above. You can see that this specification is much harder to synthesize, yet overall the problem is still unfeasible. If we decrease the threshold even further:

```
P>=0.926 [ F "goal" & c<CMAX ]
```

then the synthesizer will be able to provide a satisfying parameter assignment. Also note that assignments provided by individual synthesis methods may differ since in this case the family contains multiple feasible solutions.


```sh
./install.sh
```

The script will automatically install dependencies and compile prerequisites necessary to run PAYNT. Compilation of the tool and of all of its prerequisites might take a couple of hours. Be aware that upgrading the OS of the VM may cause problems with installation. To accelerate compilation, we recommend enabling multiple CPU cores on your VM. Such multi-core compilation is quite memory-intensive, therefore, we recommend allocating a significant amount of RAM on your VM as well. As a rule of thumb, we recommend allocating at least 2 GB RAM per core. For instance, for a VM with 4 CPU cores and at least 8 GB of RAM, the compilation should take around 30 minutes. Any errors you encounter during the compilation are most likely caused by the lack of memory: try to allocate more RAM for your VM or disable multi-core compilation (see variable `threads` in the script `install.sh`).


