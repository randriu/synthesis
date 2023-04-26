# base Dockerfile for using PAYNT
# credit to Matthias Volk (m.volk@utwente.nl) for original stormpy Dockerfile

# the docker image can be built by executing:
# $ docker build -t yourusername/paynt .

# this argument enables multi-core compilation, you may set it from the command line with
# --build-arg no_threads=<value>
ARG no_threads=1

#
FROM movesrwth/stormpy:1.7.0
MAINTAINER Roman Andriushchenko <iandri@fit.vut.cz>

# main folder
WORKDIR /opt

# remove existing storm & stormpy (TODO: optimize this)
RUN rm -rf storm
RUN rm -rf stormpy

# prerequisites
#RUN apt-get update
#RUN apt-get -y install texlive; exit 0
RUN pip3 install pytest pytest-runner pytest-cov numpy scipy pysmt z3-solver click toml Cython scikit-build

# download paynt, storm & stormpy
RUN git clone https://github.com/randriu/synthesis.git paynt
WORKDIR /opt/paynt
RUN git clone -b pomdp-api https://github.com/randriu/storm.git storm
RUN git clone -b pomdp-api https://github.com/randriu/stormpy.git stormpy

# CAV'23 experiments
RUN git clone  https://github.com/TheGreatfpmK/CAV23-POMDP-benchmark.git experiments

# build storm
RUN mkdir -p /opt/paynt/storm/build
WORKDIR /opt/paynt/storm/build
RUN cmake ..
RUN make storm-main storm-synthesis storm-dft --jobs $no_threads

# build stormpy
WORKDIR /opt/paynt/stormpy
RUN python3 setup.py build_ext --storm-dir /opt/paynt/storm/build --jobs $no_threads develop

# set the starting folder
WORKDIR /opt/paynt
