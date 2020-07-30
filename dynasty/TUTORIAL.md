This file provides a more detailed introduction to using Dynasty. In particular, multiple experiments with the tool, including the inputs and expected outputs, are discussed. A shorter overview of the tool, including instructions how to install it, can be obtained in [README](https://github.com/moves-rwth/dynasty/blob/master/README.md), which we advise the reader to read or at least quickly skim through first. 

# Feasibility Analysis

Given a sketch, i.e., a probabilistic program with holes, and a specification of properties that the final program should have, the goal of feasibility analysis is to find an instantiation of the holes such that the induced program satisfies the desired properties. 

All methods implemented in the tool, except the evolutionary algorithm, are complete, i.e., they either provide a solution, or if the there is no feasible instantiation, the algorithms eventually report so.

Below, we discuss experiments with feasibility analysis in Dynasty on two particular case studies. 

## Emulation of a Six-Sided Die

Let us consider the problem of emulating a fair six-sided die with a fair coin. This problem can of course be solved when the coin is tossed repeatedly until a certain final state is reached. We encode the problem using our PRISM-based sketching language into three files, which form the compulsory input for the tool and are introduced below.

TODO: picture of the algorithm

#### Template File (*.templ)

A template, also called a sketch, is the main part of a problem specification. It encodes the whole logic of an algorithm and contains holes to be filled with suitable optional values. Below, the variable **s** represents a state of the emulation process and **d** the generated number on the die. Starting in state 0, the coin is tossed with a 50 % chance to pick one of the states 1 or 2. For either of these states, the next state has to be synthesized which the tool is instructed to do through the undefined constants x3-6. As soon as state 7 is reached, the emulation ends, and when this happens, the value of the variable **d** is contains the generated number on the die.
```
dtmc

const int x3;
const int x4;
const int x5;
const int x6;

module die
        // local state
        s : [0..7] init 0;
        // value of the dice
        d : [0..6] init 0;

        [] s=0 -> 0.5 : (s'=1) + 0.5 : (s'=2);
        [] s=1 -> 0.5 : (s'=x3) + 0.5 : (s'=x4);
        [] s=2 -> 0.5 : (s'=x5) + 0.5 : (s'=x6);
        [] s=3 -> 0.5 : (s'=1) + 0.5 : (s'=7) & (d'=1);
        [] s=4 -> 0.5 : (s'=7) & (d'=3) + 0.5 : (s'=7) & (d'=2);
        [] s=5 -> 0.5 : (s'=2) + 0.5 : (s'=7) & (d'=4);
        [] s=6 -> 0.5 : (s'=7) & (d'=6) + 0.5 : (s'=7) & (d'=5);
        [] s=7 -> 1: (s'=7);
endmodule
```

Notice that one has to be careful about potentially ill-formed sketches. The checks currently performed by the tool are not necessarily sufficient.

#### Options for Holes (*.allowed)

Possible values for each hole (i.e., an undefined constant in the template) are defined in a file with the "allowed" suffix. Each line contains the name of a hole followed by values that the hole can be instantiated with, separated by semicolons.
```
x3;0;1;2;3;4;5;6;7
x4;0;1;2;3;4;5;6;7
x5;0;1;2;3;4;5;6;7
x6;0;1;2;3;4;5;6;7
```
#### Properties (*.properties)

The properties file contains a specification of the properties that the target program should have. In this case, reachability properties specifying the probabilities with which certain states should be reached are provided. In general, expected rewards can also be provided. The below property specifications ensure fairness of the six-sided die emulated by the algorithm.
```
P>= 0.16 [F s=7 & d=1]  
P>= 0.16 [F s=7 & d=2]  
P>= 0.16 [F s=7 & d=3]  
P>= 0.16 [F s=7 & d=4]  
P>= 0.16 [F s=7 & d=5]  
P>= 0.16 [F s=7 & d=6]
```

### Running the Example

The tool can be run by specifying the project directory and all necessary files at the command line or through the configuration file. The introduced example has multiple properties and thus we can only use the evolutionary search (ea) or CEGIS (cegis) methods, which support multiple properties.

**All options specified at the command line:**
```
python3 dynasty.py  --project examples/die/  --sketch die.templ  --allowed die.allowed  --properties die.properties ea
```
**All options specified in the [configuration file](https://github.com/moves-rwth/dynasty/tree/master/examples/die/die.cfg):**
```
python3 dynasty.py --config examples/die/die.cfg
```
**Command line options override the specification given in the configuration file:**
```
python3 dynasty.py --config examples/die/die.cfg cegis
```
#### The Result
At the end of the output of the tool, one can be find the analysis result
```
Satisfiable!
using x3: 6, x4: 3, x5: 4, x6: 5
```
that contains the assignment of a value to each hole and thus provides an instance of the program that correctly emulates a fair six-sided die with a fair coin (in case you get a different result, there are four possible solutions of this particular example :alien:).

If we tweak a bit the probability, for instance, by changing *P>= ~~0.16~~ [F s=7 & d=6]* to *P>= 0.20 [F s=7 & d=6]*, the analysis result is
```
Unsatisfiable!
```
as there is no existing instance of the sketch that would satisfy the objectives.

## Grid (POMDP)


This example models a 4x4 grid containing sixteen states, where one state represents the target. We want to synthesize a finite state controller that will reach the target from randomly selected position in the least expected time. As depicted in the part of the sketch bellow, the controller has three states (possible values of 'mem' variable) and based on the current state it picks the direction of the next step (north, east, south, west) towards the target. The object of synthesis is the selection of the succeeding state (M01, M11, M21) of the controller and the selection of the direction (PO1, P11, P21). The constant CMAX denotes the upper bound for the number of steps to the target. T_EXP, T_SLOW and T_FAST are thresholds used in the property files. We can run this example with cegis, cegar(lift), and the evolutionary algorithm (TODO: other types of synthesis alg.).
```
dtmc

const int M01;
const int M11;
const int M21;
const int P01;
const int P11;
const int P21;

const int CMAX;
const double T_EXP;
const double T_SLOW;
const double T_FAST;

module countermodule
    c : [0..CMAX] init 0;
    [p] true -> (c'=min(c+1,CMAX));
endmodule

module strategy 
    pick : [0..4];
    mem : [0..2];
    [p] pick = 0 & mem = 0 & o = 1 -> (mem' = M01) & (pick' = P01);
    [p] pick = 0 & mem = 1 & o = 1 -> (mem' = M11) & (pick' = P11);
    [p] pick = 0 & mem = 2 & o = 1 -> (mem' = M21) & (pick' = P21);
    
    [done] pick = 0 & o = 2 -> true;
    
    [north] pick = 1 -> (pick' = 0);
    [east] pick = 2 -> (pick' = 0);
    [south] pick = 3 -> (pick' = 0);
    [west] pick = 4 -> (pick' = 0);
endmodule
```

### Running the Example

In Die example we have seen a specification of the possible hole values in the _*.allowed_ file, however, the undefined constants can be also specified via command line option --constants. The latter is useful when the constants are also used as thresholds in the property specification (*.properties).

**Synthetize a controler that will reach the target within 10 steps with probability equal or higher than 0.77:**
```
python3 dynasty.py --config examples/grid/4x4grid_sl.cfg  --constants CMAX=11,T_EXP=0.0,T_SLOW=0.0,T_FAST=0.77 cegis
```

In contrast with CEGIS and CEGAR, the evolutionary algorithm is incomplete and uses a timeout value of 30 seconds by default, which can be changed by the option '--timeout'.

**Running the evolution with a one second timeout for the synthesis:**
```
python3 dynasty.py --config examples/grid/4x4grid_sl.cfg  --timeout 1  --constants CMAX=11,T_EXP=0.0,T_SLOW=0.0,T_FAST=0.77 ea
```

**Synthesize a controller that will reach the target in an expected number of steps less than 15.5:**
```
python3 dynasty.py --config examples/grid/4x4grid_sl.cfg  --properties reward.properties --constants CMAX=400,T_EXP=15.5,T_FAST=0.0,T_SLOW=0.0 lift
```
If we check the expected rewards, we implicitly have to assume that the probability to reach the target set is one (TODO: cegis article link). **TV: I do not understand this. Ideally, add a clickable link to the specification file (or list its contents here) and discuss it a bit more.** This implicit assumption can be made explicit with the option '--check-prerequisites':
```
python3 dynasty.py --config examples/grid/4x4grid_sl.cfg  --check-prerequisites  --properties reward.properties --constants CMAX=400,T_EXP=15.5,T_FAST=0.0,T_SLOW=0.0 cegis
```


# Partitioning

The problem of partitioning is also known as the threshold synthesis. It aims to partition the set of instantiations into a set of accepting instantiations, i.e., instantiations that satisfy the property at hand, and rejecting instantiations, i.e., instantiations that do not satisfy the property at hand. The CEGIS method and the evolutionary search do not support this this type of synthesis.

**Partitioning on the Grid benchmark mentioned in the 'Feasibility' section (used the same option configuration as before):**
```
python3 dynasty.py --config examples/grid/4x4grid_sl.cfg  --partitioning  --constants CMAX=11,T_EXP=0.0,T_SLOW=0.0,T_FAST=0.77 lift
```

**The result depicts all instances (option combinations) that satisfy the property:**
```
Subfamilies above: 
[HoleOptions{M01: [2],M11: [0],M21: [1],P01: [3],P11: [3],P21: [2]}, HoleOptions{M01: [2],M11: [0],M21: [1],P01: [3],P11: [2],P21: [3]}, HoleOptions{M01: [1],M11: [2],M21: [0],P01: [3],P11: [3],P21: [2]}, HoleOptions{M01: [1],M11: [2],M21: [0],P01: [3],P11: [2],P21: [3]}]
```

Notice that '--partitioning' cannot be combined with '--optimality'.


# Optimality

The optimal feasibility analysis is enabled by adding an optimality criterion to the input of feasibility analysis. An optimality criterion consists of a property, a direction, and a relative tolerance, written in a file:

```
P=? [ F (o=2 & c<=5) ]
max
relative 0.0
```

The above specification describes that the probability described by the first line should be maximized among all feasible options. By increasing the relative tolerance, the hard constraint is relaxed and we only require that the obtained instantiation is at least (1-tolerance) times global maximum.

**TV: As for the above, it is the same as in README -- check what I wrote there about why I do not understand it.**

By passing such a criterion, the tool automatically switches to solving optimal feasibility, except for the evolutionary search, where the optimized property is selected from the properties file. The order of the property is specified via the option '--optimize-one'.

**TV: There is no example of any experiment. Should be provided as above, including a discussion of the output.**

## Dynamic Power Manager (DPM)

The model consists of a Service Requester (SR), a Service Provider (SP), two Service Request Queues (SRQs), and the power manager (PM). The SR models the arrival of requests and the SRQs correspond to a (finite) queues in which the requests that cannot immediately be served are stored. The SP is the resource which services requests. It can have several states of operation with varying service rates (the time taken to service requests). The PM is a controller that observes the system and issues commands to the SP which correspond instruct it to change its current state. Two SRQs vary in their priority (high and low). The fullness of each queue is has four intervals (0-3, 3-5, 5-7, 7-10). This gives in total 16 possible interval combinations. Based on the current combination the PM dynamically issues a command to SP to change its state, hence DPM. The object of synthesis is to choose the commands issued by PM so that the average power consumption of SP is minimized while there are limits on the number of lost requests in both queues. Again, we use undefined constants for the property files - T_PW (minimal average power consumption), T_LH (average number of lost requests in the high-priority queue) and T_LL (average number of lost requests in the low-priority queue).

**TODO: image**


### Running the Example

This is again multi-objective example so we can use only the methods evolutionary search (ea) and CEGIS (cegis).

