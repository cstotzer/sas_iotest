FROM quay.io/jupyter/scipy-notebook

USER root

# Install required software
RUN apt-get update && apt-get install --no-install-recommends -y \
    pipx \
    fio \
    git-lfs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER jovyan

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/opt/conda

# Installing uv and let uv install dependencies, we'll use the pre-existing
# virtual environment living in /home/jovyan/base_env using the --active switch
# to keep container size to a minimun.
RUN pipx install uv --pip-args="--no-cache-dir --disable-pip-version-check"
