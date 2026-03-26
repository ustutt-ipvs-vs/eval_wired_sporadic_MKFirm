FROM continuumio/miniconda3 AS deps

WORKDIR /usr/src

RUN apt-get update && \
    apt-get -y install git cmake build-essential clang lld gdb bison flex perl libxml2-dev zlib1g-dev doxygen graphviz curl tar pkg-config

ENV condaenv=worstcase

COPY environment.yml .
RUN conda env create -n ${condaenv}  -f environment.yml

SHELL ["conda", "run", "--no-capture-output", "-n", "worstcase", "/bin/bash", "-c"]

FROM deps AS omnet
COPY install-omnet-docker.sh .
RUN ./install-omnet-docker.sh

FROM omnet

WORKDIR /usr/src/workspace
COPY . eval_wired_sporadic_MKFirm
WORKDIR /usr/src/workspace/eval_wired_sporadic_MKFirm

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "worstcase", "bash", "./run_worstcaseeval_docker.sh"]