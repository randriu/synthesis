# usage: docker build -t yourusername/paynt .
# command-line arguments can be specified e.g. as follows: --build-arg no_threads=8

# base image
ARG base_image=movesrwth/stormpy:ci
FROM $base_image

# additional arguments for compiling payntbind
ARG setup_args=""
# number of threads to use for parallel compilation
ARG no_threads=2

WORKDIR /opt/

# install dependencies
RUN apt-get update -qq
RUN apt-get install -y graphviz

# install paynt
WORKDIR /opt/paynt
COPY . .
RUN pip install .
