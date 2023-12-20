FROM movesrwth/storm-basesystem:latest

# Install dependencies
######################
# Uncomment to update packages beforehand
RUN apt-get update -qq
RUN apt-get install -y --no-install-recommends \
    uuid-dev \
    python3 \
    python3-venv

# CMake build type
ARG build_type=Release
# Additional arguments for compiling stormpy
ARG setup_args=""
# Additional arguments for compiling pycarl
ARG setup_args_pycarl=""
# Number of threads to use for parallel compilation
ARG no_threads=2
# Specific storm git commit revision SHA
ARG storm_sha=dc7960b8f0222793b591f3d6489e2f6c7da1278f

WORKDIR /opt/
RUN git clone https://github.com/moves-rwth/storm.git storm
WORKDIR /opt/storm/build
RUN git reset --hard $storm_sha
RUN cmake .. -DCMAKE_BUILD_TYPE=$build_type
RUN make storm-main storm-pomdp --jobs $no_threads
ENV PATH="/opt/storm/build/bin:$PATH"

# Obtain carl-parser from public repository
# RUN git clone https://github.com/moves-rwth/carl-parser.git

# # Switch to build directory
# RUN mkdir -p /opt/carl-parser/build
# WORKDIR /opt/carl-parser/build

# # Configure carl-parser
# RUN cmake .. -DCMAKE_BUILD_TYPE=$build_type

# # Build carl-parser
# RUN make carl-parser -j $no_threads


# Set-up virtual environment
############################
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install -U pip setuptools wheel

# Build pycarl
##############
WORKDIR /opt/pycarl

# Obtain latest version of pycarl from public repository
RUN git clone --depth 1 https://github.com/moves-rwth/pycarl.git .

# Build pycarl
RUN python setup.py build_ext $setup_args_pycarl -j $no_threads develop

# Build stormpy
###############
WORKDIR /opt/stormpy

# Copy the content of the current local stormpy repository into the Docker image
RUN git clone --depth 1 --branch synthesis https://github.com/randriu/stormpy.git .

# Build stormpy
RUN python setup.py build_ext $setup_args -j $no_threads develop

# Additional dependencies
##########################

RUN pip install -U pip setuptools wheel numpy

# Paynt / extra dependencies
RUN apt-get install -y graphviz
RUN pip install click z3-solver pysmt graphviz

# Build paynt
#############
WORKDIR /opt/paynt
COPY . .

RUN pip install -e .
