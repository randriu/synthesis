Dynasty
=================================================
[![Build Status](https://travis-ci.org/moves-rwth/dynasty.svg?branch=master)](https://travis-ci.org/moves-rwth/dynasty)

Dynasty contains algorithms for synthesis in probabilistic program sketches.

Some of the algorithms have been published:
- [1] Milan Ceska, Christian Hensel, Sebastian Junges, Joost-Pieter Katoen: Counterexample-Driven Synthesis for Probabilistic Program Sketches, FM 2019.
- [2] Milan Ceska, Nils Jansen, Sebastian Junges, Joost-Pieter Katoen: Shepherding Hordes of Markov chains, TACAS 2019.

An overview is given in:
- [3] 	Milan Ceska, Christian Dehnert, Nils Jansen, Sebastian Junges, Joost-Pieter Katoen: Model Repair Revamped: On the Automated Synthesis of Markov Chains.

And many more details can be found in:
- [4] Sebastian Junges: Parameter Synthesis in Markov Models, PhD Thesis, RWTH Aachen University, 2020.

## Overview
We first give some installation guideline and then go into some usage examples.
A [getting started guide](https://github.com/moves-rwth/dynasty/blob/master/TUTORIAL.md) that walks users through some options is provided seperately.

**TV: I have not noticed that the "getting started guide" is the tutorial. Moreover, it seems to me that the tutorial is hardly readable without first going through the README. So, I suggest to (1) rename the "getting started guide" to a tutorial and (2) characterize better the relation of these two documents. Can one say that the tutorial provides a more detailed discussion of using various methods and options provided by the tool, but the reader is advised to first skim through the readme and then go through the tutorial?**

## Installation

### Dependencies

- Python bindings for [z3](https://github.com/Z3Prover/z3).
- The model checker storm and the python bindings for storm. Please check the [installation hints](https://moves-rwth.github.io/stormpy/installation.html#installation-steps).
- The python packages:
  * click,
  * pysmt.

### Install

First, run: 

```
python setup.py install
```

This will automatically install dynasty and its python dependencies. Notice that you have to install storm yourself (see above).
If you are planning to make changes to the code, we suggest to use `python setup.py develop`

To run the tests, run:
```
python -m pytest dynasty_tests
```

### Docker container

We automatically provide a [docker container](https://hub.docker.com/r/movesrwth/dynasty) with everything pre-installed.


## Usage examples

We support solution of three types of problems:
 - Feasibility Analysis (and its dual, Validity Analysis),
 - Optimal Feasibility Analysis,
 - Partitioning (or Threshold Analysis).
 
We support five methods of solving the above problems:
 - CEGIS [1],
 - Lifting [2],
 - (Consistent) Scheduler enumeration [2],
 - SmartSearch [to be published],
 - All-in-one [Chroszon et al, Formal Asp Comput].

As input, we take projects. Below, we first explain what a project is and then discuss the different analysis types and how to invoke the different methods for these problems. 
For details about the methods, we refer to the publications mentioned above. 

### Input: Project Folders

A project is a folder containing the various inputs for the synthesis. 

We require:
- A .templ file, which is a PRISM file with various open integer constants (holes).
- A .allowed file, which describes sets of possible values for each hole. The instantiations are the Cartesian product of such sets of values.
- A .properties file, which contains a list of PCTL formulae.

Optionally, a project may contain: 
- A .restrictions file, which contains restrictions on the intstantiations. Restrictions are currently only supported by CEGIS.
- A .optimality file, which contains a PCTL formula, a direction, and a relative precision. This file is relevant for optimal feasibility.

Notice that a project may contain more files than necessary, e.g., to allow for slight variations without duplicating everything.

For more information, look at the [examples](examples/).

### Feasibility Analysis

The goal of feasibility analysis is to find an instantiation of the holes such that the induced program satisfies the properties.
All methods we provide for solving this problem are complete, i.e., the algorithms either report a feasible solution, or if there is no feasible instantiation, the algorithms eventually report so.

**TV:The tutorial says something different! Namely: All methods presented here except the evolutionary algorithm are complete, i.e., if the there is no feasible instantiation, the algorithms eventually report so. Should be made uniform.**

Notice that one has to be careful about potentially ill-formed sketches. The checks we perform are not necessarily sufficient.

Below, we provide examples of using the different supported methods for feasability analysis on the provided case studies.

#### CEGIS
```
python dynasty.py --project examples/virus/ --sketch virus.templ --constants CMAX=0,T=18.0 --allowed virus.allowed --restrictions virus.restrictions  --properties virus.properties
```
```
python dynasty.py --project examples/grid/ --sketch 4x4grid_sl.templ --constants CMAX=11,T_EXP=10.0,T_SLOW=10.0,T_FAST=0.9 --allowed 4x4grid_sl.allowed --restrictions 4x4grid_sl.restrictions  --properties single.properties 
```
```
python dynasty.py --project examples/grid/ --sketch 4x4grid_sl.templ --constants CMAX=1,T_EXP=10.0,T_SLOW=10.0,T_FAST=0.9 --allowed 4x4grid_sl.allowed --restrictions 4x4grid_sl.restrictions  --properties reward.properties --check-prerequisites True
```

#### Lifting
```bash
python dynasty.py --project examples/grid/ --sketch 4x4grid_sl.templ --properties reward.properties --constants "CMAX=400,T_EXP=7.7,T_FAST=0.6,T_SLOW=0.995" --allowed 4x4grid_sl.allowed lift
```

#### Scheduler enumeration
```bash
python dynasty.py --project examples/grid/ --sketch 4x4grid_sl.templ --properties reward.properties --constants "CMAX=400,T_EXP=7.7,T_FAST=0.6,T_SLOW=0.995" --allowed 4x4grid_sl.allowed cschedenum
```

#### All other approaches

**TODO**

### Optimal Feasibility Analysis
Optimal feasibility analysis differs from feasibility analysis in that an optimality criterion is added.
An optimality criterion consists of a property, a direction, and a relative tolerance, described in a file containing, e.g., the following:

```
P=? [ F (o=2 & c<=5) ]
max
relative 0.0
```
The above optimality criterion says that the probability described by the first line should be maximized among all feasible options.
By increasing the relative tolerance given on the last line, the hard optimality constraint can be relaxed to requiring that the obtained instantiation is at least (1-tolerance)* "global maximum."

**TV: The last sentence above seems somehow unfinished -- basically, after substituting some values, one gets: the instantiation is at least 0.5. What does it mean to be 0.5??? A few words should be added**

When given such a criterion, the tool automatically switches to solving optimal feasibility.

Below, we provide examples of using the different supported methods for optimal feasability analysis on the provided case studies.

#### CEGIS

**TODO description**
```bash
python dynasty.py --project examples/grid/ --sketch 4x4grid_sl.templ --constants CMAX=11,T_EXP=10.0,T_SLOW=10.0,T_FAST=0.7 --allowed 4x4grid_sl.allowed --restrictions 4x4grid_sl.restrictions  --optimality fast_to_target.optimal --properties none.properties cegis
```

#### Other approaches

A support for optimal feasibility analysis is not yet implemented.


### Partitioning 
This problem is also known as threshold synthesis.
It aims to partition the set of instantiations into a set of accepting 
instantiations, i.e., instantiations that satisfy the property at hand,
and rejecting instantiations, i.e., instantiations that do not satisfy the property at hand.

In general, partitioning can be enabled by adding a switch `--partitioning`. Notice that this switch
cannot be combined with `--optimality`.

Below, we provide examples of using the different supported methods for partitioning on the provided case studies.

#### CEGIS

Currently, there is no working implementation for this type of analysis.

#### Lifting

**TODO: Description**

```bash
python --project examples/grid/ --sketch 4x4grid_sl.templ --constants CMAX=11,T_EXP=10.0,T_SLOW=10.0,T_FAST=0.9 --allowed 4x4grid_sl.allowed --restrictions 4x4grid_sl.restrictions  --properties single.properties --partitioning lift
```

#### Scheduler enumeration

**TODO: Descritption**

#### All other approaches

**TODO: Description**

### Further Options

- `--check-prerequisites`/`--no-check-prerequiites` 
One may omit the check prerequisites if the sketch already ensures that all rewards are less than infinity.

- `--print-stats` 
Print statistics at the end. Helpful to understand the algorithm performance but clutters the output. 

## The sources

**TV: What should be here???**
