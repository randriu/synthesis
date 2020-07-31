# Integrated synthesis of probabilistic programs

Repository for integrated synthesis of probabilistic programs (see [dynasty](https://github.com/moves-rwth/dynasty)) based on the stable versions of [storm 1.6.0](https://github.com/moves-rwth/storm) and [stormpy 1.6.0](https://github.com/moves-rwth/stormpy).

### Installation

Follow the [usual installation of dynasty](https://github.com/moves-rwth/dynasty), but use the source code for storm, stormpy and dynasty provided in this repository.

### List of modified files

(\- modified \+ added)

\- storm/src/storm/storage/sparse/StateValuations.h  
\+ storm/src/storm/research/*  

\- stormpy/src/mod_core.cpp  
\+ stormpy/src/core/research.*  

\- dynasty/dynasty/cli.py  
\- dynasty/dynasty/family_checkers/familychecker.py  
\- dynasty/dynasty/model_handling/mdp_handling.py  
\+ dynasty/Makefile  
\+ dynasty/workspace/  
\+ dynasty/dynasty/integrated_checker.py  
 