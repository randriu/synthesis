# Artifact for submission 87

This is an artifact supplemented with the TACAS 2019 submission __Roman Andriushchenko, Milan Češka, Sebastian Junges, and Joost-Pieter Katoen:__ **Inductive Synthesis for Probabilistic ProgramsReaches New Horizons**. The tool represents a branch of the [dynasty](https://github.com/moves-rwth/dynasty) tool for probabilistic synthesis and contains the dynasty code as well as its adaptations for [storm](https://github.com/moves-rwth/storm) and [stormpy](https://github.com/moves-rwth/stormpy) (prerequisites for dynasty).

**Disclaimer.** Since the initial submission of the paper manuscript, the implementation of the tool has been subject to multiple improvements and optimizations, with the most drastic changes concerning the CEGAR method and the CEGAR loop of the integrated method. As a consequence of this, the experimental evaluation of the synthesis methods has been very slightly reworked in the revised manuscript to better highlight the differences between the synthesis approaches. The conclusions drawn from the presented experiments remained the same, although in multiple cases the novel integrated method has demonstrated even more distinguished results. 

## Installation of the artifact

Installation is performed automatically by running the installation script isntall.sh:

$ chmod +x install.sh
$ sudo ./install.sh

Compilation of the tool and of all of its prerequisites will take about an hour. To accelerate compilation, we recommend enabling multiple CPU cores on your VM. Such multi-core compilation is quite memory-intensive, therefore, we recommend allocating a significant amount of RAM on your VM as well. As a rule of thumb, we recommend allocating at least 1.5 GB RAM per core. For instance, for a VM with 4 CPU cores and at least 6 GB of RAM, the compilation should take around 20 minutes. Any errors you encounter during compilation are most likely caused by the lack of memory: try to allocate more RAM for your VM or disable multi-core compilation (see exported variable COMPILE_JOBS in the script install.sh).

## Initial testing of the artifact

Having installed the tool, you can test it by evaluating a simple synthesis problem:

$ source env/bin/activate
$ python3 dynasty/dynasty.py --project tacas21-benchmark/grid --properties easy.properties cegis

The first command activates python environment, while the second one runs the dynasty itself. We will explain the syntax of the second command later. For now, we can see that we investigate the __Grid__ benchmark discussed in the TACAS'21 paper and synthesize it wrt. the easy property using the CEGIS method. The tool will print a series of log messages and, in the end, a short summary of the synthesis process. This summary contains
- statistic about the benchmark: number of holes, family size, (average) DTMC size etc.
- info about synthesis process: synthesis time, number of iterations, whether the synthesis problem is feasible etc.

We can see that this particular __Grid__ benchmark contains 8 holes (parameters) and 65k members, each having 1.2k states on average -- you can check that these data correspond to the ones reported in Table 1. We can also see that the problem was unfeasible and that on our machine it took CEGIS 613 iterations and 30 seconds to prove this -- you can cross-reference these data with the ones reported in the first row of Table 2. To see how the integrated method handles this problem, simply run

$ python3 dynasty/dynasty.py --project tacas21-benchmark/grid --properties easy.properties hybrid

On our machine, hybrid method solved this benchmark using 11 CEGIS iterations and 285 CEGAR iterations in around six seconds. Similarly, we can run CEGAR on this benchmark:

$ python3 dynasty/dynasty.py --project tacas21-benchmark/grid --properties easy.properties cegar

However, keep in mind that in this case CEGAR will run for about eight minutes. You might have noticed that, when evaluating the benchmark using CEGAR or hybrid method, the summary also contains an additional row containing info about the average MDP size of the evaluated subfamilies. Furthermore, when evaluating benchmark using the hybrid approach, you can specify an additional --ce-quality option that evaluates the counterexample quality:

$ python3 dynasty/dynasty.py --project tacas21-benchmark/grid --properties easy.properties hybrid --ce-quality

In this case, the summary will contain two additional rows with information about the quality as well as the construction times of the counterexamples, as discussed in the left-hand side of Table 2. You will notice that the quality of the MaxSat method will be reported as 0, since this value was not computed at all -- we do not compute the MaxSat quality implicitly since this computation is often very time-demanding and would complicate collecting data about the novel approach for CE construction. To enable evaluation of the MaxSat approach, you can specify an additional option --ce-maxsat:

$ python3 dynasty/dynasty.py --project tacas21-benchmark/grid --properties easy.properties hybrid --ce-quality --ce-maxsat

Using summaries from these two commands we managed to replicate data reported in the first row of Table 2. Finally, to deactivate the python environment, simply run

$ deactivate

**Please note** that all of the discussed synthesis methods -- CEGIS, CEGAR and the novel integrated method -- are subject to some nondeterminism during their execution, and therefore during your particular evaluation you might obtain slightly different numbers of iterations as well as execution times. Furthermore, the switching nature of the integrated hybrid heavily depends on the timing, which can again result in fluctutations in the observed measurements. However, the quantitative conclusions -- i.e., overall performance of hybrid vs CEGAR, or overall quality of MaxSat counterexamples vs those obtained by a novel approach -- will be preserved.

## Reproducing presented experiments

## Exploring the synthesis problems beyond the presented experiment suit


