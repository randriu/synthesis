# Models

This directory contains the model files in PRISM-syntax we evaluated for the experiments.

The model files for

* `crypt`,
* `grid-avoid`,
* `grid`,
* `maze2`,
* `network-priorities`,
* `network`, and
* `nrp`

were originally taken from [here](http://www.prismmodelchecker.org/files/rts-poptas/). 
In the grid worlds, we often added a parameter `sl` (or `slippery`) to model uncertain movements (usually resulting in an infinite belief MDP).
We also fixed a modelling errors in `crypt` and `maze2`.

