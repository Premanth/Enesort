FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    python3 \
    python3-pip \
    python3-dev \
    linux-tools-generic \
    cpufrequtils \
    && rm -rf /var/lib/apt/lists/*

# Python analysis deps
RUN pip3 install numpy pandas scipy matplotlib tabulate

WORKDIR /ecosort

COPY . .

# Build
RUN cmake -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DECOSORT_FETCH_DEPS=ON \
    && cmake --build build --parallel $(nproc)

# Create results directory
RUN mkdir -p results/raw results/analysis results/figures results/tables

# Default: run smoke benchmark, then analyze
CMD bash -c "\
    python3 scripts/run_all.py --build-dir build --smoke && \
    python3 scripts/analyze.py --results-dir results && \
    python3 scripts/tables.py  --results-dir results && \
    python3 scripts/plots.py   --results-dir results"

