#!/bin/bash
# usage: source alias-storm.sh

# multi-core compilation
export COMPILE_JOBS=$(nproc)
# single-core compilation:
# export COMPILE_JOBS=1

# environment variables
export PAYNT_ROOT=`pwd`

# environment aliases
alias enva='source $PAYNT_ROOT/env/bin/activate'
alias envd='deactivate'

storm-dependencies() {
    if [ -f /etc/redhat-release ]; then
    	echo "RedHat installation. dnf required."
        sudo dnf update
        sudo dnf -y install make automake gcc gcc-c++ kernel-devel boost-devel cln-devel
        sudo dnf -y install gmp-devel ginac-devel glpk-devel hwloc-devel z3 xerces-c-devel eigen3-devel
        sudo dnf -y install maven libuuid-devel python3-devel libffi-devel openssl-devel python3-pip
    else
        sudo apt update
        sudo apt -y install build-essential git automake cmake libboost-all-dev libcln-dev libgmp-dev libginac-dev libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev
        sudo apt -y install maven uuid-dev python3-dev libffi-dev libssl-dev python3-pip python3-venv
    fi
    # apt -y install texlive-latex-extra
    # update-alternatives --install /usr/bin/python python /usr/bin/python3 10
}

download-prerequisites() {
    mkdir -p $PAYNT_ROOT/prerequisites
    cd $PAYNT_ROOT/prerequisites
    git clone --depth 1 https://github.com/moves-rwth/pycarl.git pycarl
    git clone --depth 1 --branch cvc5-1.0.0 https://github.com/cvc5/cvc5.git cvc5
    cd -
    cd $PAYNT_ROOT
    git clone https://github.com/moves-rwth/storm.git storm
    # git clone --branch stable https://github.com/moves-rwth/storm.git storm
    git clone --branch synthesis git@github.com:randriu/stormpy.git stormpy
    cd -
}

python-environment() {
    python3 -m venv $PAYNT_ROOT/env
    enva
    pip3 install pytest pytest-runner pytest-cov numpy scipy pysmt z3-solver click toml Cython scikit-build
    envd
}

pycarl-build() {
    cd $PAYNT_ROOT/prerequisites/pycarl
    enva
    python3 setup.py build_ext --jobs $COMPILE_JOBS develop
    #[TEST] python3 setup.py test
    envd
    cd -
}

cvc5-build() {
    cd $PAYNT_ROOT/prerequisites/cvc5
    enva
    ./configure.sh --prefix="." --auto-download --python-bindings
    cd build
    make --jobs $COMPILE_JOBS
    make install
    envd
    cd -
}

storm-build() {
    mkdir -p $PAYNT_ROOT/storm/build
    cd $PAYNT_ROOT/storm/build
    cmake ..
    make storm-main storm-pomdp --jobs $COMPILE_JOBS
    # make check --jobs $COMPILE_JOBS
    cd -
}

stormpy-build() {
    cd $PAYNT_ROOT/stormpy
    enva
    python3 setup.py build_ext --jobs $COMPILE_JOBS develop
    # python3 setup.py build_ext --storm-dir $PAYNT_ROOT/storm/build --jobs $COMPILE_JOBS develop
    # python3 setup.py test
    envd
    cd -
}

download-rl() { # 
    cd $PAYNT_ROOT/rl_approach
    pip3 install tensorflow # Potentially long installation.
    pip3 install tf_agents # It is essential to install tf_agents AFTER tensorflow
    git clone https://github.com/stevencarrau/safe_RL_POMDPs safe_rl
    
    git clone https://github.com/stevencarrau/shield_rl_gridworlds.git shield_gridworlds
    git clone https://github.com/sjunges/gridworld-by-storm.git gridworlds
    cd -
}

setup-rl() {
    enva
    cd $PAYNT_ROOT/rl_approach
    cd shield_gridworlds
    python3 ./POMDP/setup.py develop
    cd ..
    mv $PAYNT_ROOT/rl_approach/safe_rl/cfgs/SwitchShield.json $PAYNT_ROOT/rl_approach/safe_rl/cfgs/SwitchShieldx.json
    mkdir -p $PAYNT_ROOT/rl_approach/safe_rl/newvideos/NS/SWITCH
    cd ..
    envd
}

synthesis-install() {
    storm-dependencies
    download-prerequisites
    python-environment
    
    # building cvc5 is optional
    # cvc5-build

    # optional unless you don't have Storm installed
    storm-build
    
    pycarl-build
    stormpy-build

    # download-rl
    # setup-rl
}
