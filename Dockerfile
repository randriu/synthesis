FROM movesrwth/stormpy:ci

# Additional arguments for compiling payntbind
ARG setup_args=""
# Number of threads to use for parallel compilation
ARG no_threads=2

WORKDIR /opt/

# install dependencies
RUN apt-get update -qq
RUN apt-get install -y graphviz
RUN pip install click z3-solver graphviz

# build paynt
WORKDIR /opt/paynt
COPY . .
WORKDIR /opt/paynt/payntbind
RUN python setup.py build_ext $setup_args -j $no_threads develop

WORKDIR /opt/paynt

# (optional) install paynt
RUN pip install -e .

# TODO tests
