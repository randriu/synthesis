# the docker image can be built by executing:
# docker build -t yourusername/paynt .
# to enable multi-thread compilation, use --build-arg threads=<value>

FROM ubuntu
MAINTAINER Roman Andriushchenko <iandri@fit.vut.cz>
ARG threads=1

# execute bash when running the container
ENTRYPOINT ["/bin/bash"]

# to prevent texlive from asking our geographical area
ENV DEBIAN_FRONTEND noninteractive

# install dependencies
RUN apt update
RUN apt install -y build-essential git automake cmake libboost-all-dev libcln-dev libgmp-dev libginac-dev libglpk-dev libhwloc-dev libz3-dev libxerces-c-dev libeigen3-dev
RUN apt -y install maven uuid-dev python3-dev libffi-dev libssl-dev python3-pip python3-venv
RUN apt -y install texlive-pictures
RUN pip3 install pytest pytest-runner pytest-cov numpy scipy pysmt z3-solver click toml Cython scikit-build

# main directory
WORKDIR /synthesis

# download everything
# using --depth 1 to make the download faster and the image smaller
WORKDIR /synthesis/prerequisites
RUN git clone --depth 1 --branch master14 https://github.com/ths-rwth/carl carl
RUN git clone --depth 1 https://github.com/moves-rwth/pycarl.git pycarl
RUN git clone --depth 1 --branch cvc5-1.0.0 https://github.com/cvc5/cvc5.git cvc5
WORKDIR /synthesis
RUN git clone --depth 1 --branch pomdp-api https://github.com/randriu/storm.git storm
RUN git clone --depth 1 --branch pomdp-api https://github.com/randriu/stormpy.git stormpy
RUN git clone --depth 1 https://github.com/randriu/synthesis.git paynt


# build prerequisites
WORKDIR /synthesis/prerequisites/carl/build
RUN cmake -DUSE_CLN_NUMBERS=ON -DUSE_GINAC=ON -DTHREAD_SAFE=ON ..
RUN make lib_carl --jobs $threads

WORKDIR /synthesis/prerequisites/pycarl
RUN python3 setup.py build_ext --jobs $threads develop

#WORKDIR /synthesis/prerequisites/cvc5
#RUN ./configure.sh --prefix="." --auto-download --python-bindings
#WORKDIR /synthesis/prerequisites/cvc5/build
#RUN make --jobs $threads
#RUN make install

# build storm, set the path
WORKDIR /synthesis/storm/build
RUN cmake ..
RUN make storm-main storm-synthesis --jobs $threads
ENV PATH="/synthesis/storm/build/bin:$PATH"

# build stormpy
WORKDIR /synthesis/stormpy
RUN python3 setup.py build_ext --storm-dir /synthesis/storm/build --jobs $threads develop

# set the initial folder
WORKDIR /synthesis/paynt

# (CAV'23) download the experiment scripts
RUN git clone https://github.com/TheGreatfpmK/CAV23-POMDP-benchmark.git experiments

