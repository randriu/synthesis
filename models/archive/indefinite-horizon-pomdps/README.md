Supporting material for the Paper:
#Verification of indefinite-horizon POMDPs


## Contents of this repository

* Logfiles (see subdirectory `logs` and `logs/Readme.md`)
* Model files (see subdirectory `models` and `models/Readme.md`)
* This Readme


## Storm Installation

The implementation is part of Storm since version 1.6.0. Click [here](http://www.stormchecker.org/getting-started.html) to obtain a recent version of Storm.

For our experiments in the Paper we considered [this](https://github.com/moves-rwth/storm/commit/b6fcdefbbb4fa33ca530f52a8f8a16222b09e71f) commit.
If you want to use the same version, please refer to the [installation guide](http://www.stormchecker.org/documentation/obtain-storm/build.html) to build storm from source.
Before the [Configuration Step](http://www.stormchecker.org/documentation/obtain-storm/build.html#configuration-step), make sure to checkout the appropriate commit using
```
git checkout b6fcdefbbb4fa33ca530f52a8f8a16222b09e71f
```

After the `make` step, the binary `$STORM_DIR/build/bin/storm-pomdp` should be available.
To see a list of possible options, simply run:
```
`$STORM_DIR/build/bin/storm-pomdp` --help
```
Example invocations are also given in the [logfiles](https://github.com/moves-rwth/indefinite-horizon-pomdps/tree/master/logs).