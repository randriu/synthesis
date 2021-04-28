## Evaluating PAYNT 
We provide scripts to recreate the experiments in our paper [1], see [README.md](../README.md)).

### Reproducing [1, Table 1]

Table 1 presents results of 15 different experiments: 5 benchmarks evaluated using one-by-one enumeration and using advanced synthesis method, where the latter approach is investigated wrt. a hard and an easy property. To run these 15 evaluations, navigate to `experiments` folder and run the script:

```sh
cd experiments
./experiment.sh timeout
```

Here, `timeout` is a timeout value for each individual experiment, e.g. '5m' or '2h'. The script will evaluate the benchmarks and, for each experiment, produce a logfile available in `experiments/logs` folder. As soon as all experiments are finished, the script will parse these logfiles and output a table similar to Table 1. This table will be also stored to `experiment/logs/summary.txt`.

#### How to select the timeout value

Based on the runtimes reported in the table, you can select a timeout value that will allow you to complete as many experiments as possible within your allocated time. Since 1-by-1 enumeration typically requires more than a day to complete, you might be interested in at least completing synthesis via advanced methods (10 of the 15 presented experiments). Here are some suggested values:

- `timeout=5m` will complete 4/10 experiments within 1 hour
- `timeout=20m` will complete 6/10 experiments within 3.5 hours
- `timeout=1h` will complete 7/10 experiments within 8.5 hours
- `timeout=2h` will complete 9/10 experiments within 14 hours (recommended value)
- `timeout=12h` will complete 10/10 experiments within 2.5 days

If the experiment associated with one-by-one enumeration hits a timeout, the runtime will be estimated based on the number of rejected assignments. However, in order to obtain reliable estimates, enumeration must run of a significant period of time, i.e. for a couple of hours. If advanced synthesis method hit a timeout, then, since its performance cannot be estimated in a meaningful way, the corresponding table entry will contain '-'.
Finally, statistics about average MC size are taken from logs associated with advanced synthesis (easy property) and, if the corresponding computation was interrupted, the table entry will again display '-'.

Finally, note that the evaluation of experiments is executed concurrently based on the number `nproc` of (logical) CPUs available on your system/VM. As a result, for a VM having 4 CPU cores, choosing recommended timeout value `timeout=2h` will allow to complete 9/10 experiments associated with advanced synthesis approaches as well as produce reliable estimates for 1-by-1 enumeration within 3-4 hours. It might be a good idea to let the script run overnight. The sample log files for execution on our machine with a 12-hour timeout are available inside the supplied VM at `~synthesis/experiments/logs.zip`.

**Please note** that all of the discussed synthesis methods, specifically advanced methods (CEGIS, CEGAR, hybrid) are subject to some nondeterminism during their execution, and therefore during your particular evaluation you might obtain slightly different execution times. Furthermore, the switching nature of the integrated method heavily depends on the timing, which can again result in fluctuations in the observed measurements. However, the qualitative conclusions -- e.g. overall performance of hybrid vs 1-by-1 enumeration or comparative runtimes of synthesizing wrt. easy vs hard property -- should be preserved. Also remember that the provided runtimes for different timeout settings were estimated based on the experience with our CPU (Intel i5-8300H, 4 cores at 2.3 GHz) and that the evaluation might last longer/shorter on your machine.

### Reproducing Figure 5

Figure 5 was created manually based on the output of PAYNT when synthesizing an optimal controller (hard property) for the __Maze__ model. To check the result, you need to let at least the advanced method finish (recommended value `timeout=2h` will guarantee this even on slower CPUs). Alternatively, you can specifically run computation of this model (do not forget to activate python environment):

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
- `o=6` corresponds to black states (2)

Semantics of hole `P_m_o` is 'direction chosen when observing `o` with memory value `m`. The direction is an integer from 1 to 4 representing north, east, south and west respectively. Similarly, semantics of hole `M_m_o` is 'memory update after moving from location `o` with memory value `m`. You can see that, for instance, in location 0, hole assignments `P_0_1 = P_1_1 = 2` and `M_0_1 = M_1_1 = 1` imply that the robot will always go east and will set its memory bit to 1. Note that there are multiple optimal controllers and you might obtain e.g. symmetric hole assignments (i.e. the one in which 0's and 1's are swapped in memory updates) that imply expected time 8.13 steps to reach the exit.

## Exploring synthesis problems beyond the presented experiment suite

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

#### Automatic sketch generation

For simplification, we also provides the [script](./cav21-benchmark/herman/custom/generate_herman_sketch.py) for generating various sketches of the Herman protocol.
As we describe in the paper (Chapter 5), *Herman* protocol considers a token ring with an odd number of connected stations.
Moreover, we give each station an additional single bit of memory, and the choice between multiple different coin biases.
Therefore, this script automatically generates Herman protocol versions that differ in the number of stations and coin biases.
It can be run as follows:

```shell
python3 cav21-benchmark/herman/custom/generate_herman_sketch.py [OPTIONS]
```

where the options can be:

- `--dices`: specifies the number of considered coin biases [default: 5] (in the paper 25)
- `--stations`: specifies the number of stations which must be odd [default: 5] (in the paper 5)
- `--step`: specifies the step of the coin biases starting from 0.0 [default: 0.01] (in the paper 0.01)

For instance, we list the possible combination of options and protocol versions derived from them:

- `25, 5, 0.01` -> 25 dices with coin biases from 0.00 to 0.24 with 5 stations
- `11, 10, 0.05` -> 11 dices with coin biases from 0.00 to 0.50 with 10 stations
- `250, 3, 0.001` -> 250 dices with coin biases from 0.00 to 0.25 with 3 stations

This script generates the [sketch](./cav21-benchmark/herman/custom/sketch.templ) contains the protocol according to the specified options.
The file contains the property for synthesising an optimal strategy to stabilise in a minimal number of rounds.
For example, you can try to run

```shell
python3 cav21-benchmark/herman/custom/generate_herman_sketch.py --dices 11 --stations 3 --step 0.05
python3 paynt/paynt.py --project cav21-benchmark/herman/custom/ hybrid
```

which takes only a few seconds a returns the result, where at least two dices have the highest coin biases (0.50), which ensures the minimal number of steps equal to 4/3.
Now, you can try to reduce the step in half, which modifies the interval of possible coin biases to {0.0, 0.025, ..., 0.25}:

```shell
python3 cav21-benchmark/herman/custom/generate_herman_sketch.py --dices 11 --stations 3 --step 0.025
python3 paynt/paynt.py --project cav21-benchmark/herman/custom/ hybrid
```

This synthesis will take less time than the previous one, as the number of iterations has been reduced by almost half at both CEGIS and AR loops.
Of course, the number of expected steps will increase to 16/9 as the coins cannot reach the most fairness bias.
We note that the average size of MDP is ~300 and of DTMC ~40 in these considered variants, which is the main reason for the fast running of the synthesis.
Therefore, you can try to generate the protocol version with more processes, but with less of the number of coins and greater step:

```shell
python3 cav21-benchmark/herman/custom/generate_herman_sketch.py --dices 6 --stations 5 --step 0.10
python3 paynt/paynt.py --project cav21-benchmark/herman/custom/ hybrid
```

Variant with more processes significantly increases the MDP and DTMC sizes, in this case to 19K and 1K.
Although the size of the family is 10 times smaller (from 100K to 10K), in this case, the synthesis takes a little longer period and more iterations due to the size and complexity of the models.
Feel free to experiment with these options values, but be aware that the family blows up really fast according to the number of coins. 
As we have shown, The size of the models is significantly affected by the number of stations.

#### More example PAYNT invocations

You feel free to try and examine some other example to invoke PAYNT on available benchmarks.
We list some example commands that do not take so much time:

##### DPM

###### Feasible Synthesis (~40sec)

```shell
python3 paynt/paynt.py --project workspace/examples/dpm/half/ --properties power.properties --constants CMAX=2,THRESHOLD=0.01 hybrid
```
###### Minimal Synthesis (~40sec)

```shell
python3 paynt/paynt.py --project workspace/examples/dpm/half/ --properties optimal.properties --constants CMAX=10,THRESHOLD=0.01 hybrid
```

##### Pole

###### Epsilon Minimal Synthesis (~60sec)

```shell
python3 paynt/paynt.py --project workspace/examples/pole/orig/ --properties optimal.properties --constants CMAX=6 hybrid
```

###### Unfeasible Synthesis (~155sec)

```shell
python3 paynt/paynt.py --project workspace/examples/pole/orig/ --constants CMAX=40 hybrid
```

##### Grid

###### Multi-property (1) + Maximal Synthesis (~85sec) 

```shell
python3 paynt/paynt.py --project workspace/examples/grid/orig/ --constants CMAX=40,THRESHOLD=0.75 hybrid
```

##### Dice

###### Multi-property (2) + Minimal Synthesis (~63sec)

```shell
python3 paynt/paynt.py --project workspace/examples/dice/5/ cegar
```

##### Knuth & Yao Dice 

###### Multi-property (6) + Minimal Synthesis (~240sec (CEGIS); ~35sec (onebyone))

```shell
python3 paynt/paynt.py --project workspace/examples/kydie/ cegis
python3 paynt/paynt.py --project workspace/examples/kydie/ onebyone
```


For more observation, for instance, you can try to edit the values of the constants in the commands and observe how they affect the results and duration of the synthesis.
But be careful again because the problem of a double state explosion can very easily manifest itself and make the synthesis process much more difficult.
