# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
# lfphys visualizations: the one server, its worker processes and the tests.
# CPU by default (numpy/scipy); CuPy with the NVIDIA CUDA 12 runtime libraries from PyPI (requirements.lock) lets the
# engine's backend (lfphys.core.backend, plan P11) move heavy kernels to GPU 0 when the container is given that GPU
# (docker-compose: service viz). Without a GPU the same image runs everything on the CPU. The wheels are CUDA 12.9;
# on an older 12.x driver (this host: 550, CUDA 12.4) they run by minor-version compatibility, which holds because
# CuPy compiles kernels to SASS, not PTX: leave CUPY_COMPILE_WITH_PTX unset (lfphys/README.md, "CPU and GPU").
# Build and run from engine/, the repository root (README.md):
#   docker compose -f visualizations/docker/docker-compose.yml build
#   docker compose -f visualizations/docker/docker-compose.yml up -d
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    OMP_NUM_THREADS=2 \
    OPENBLAS_NUM_THREADS=2

COPY visualizations/docker/requirements.lock /tmp/requirements.lock
RUN pip install -r /tmp/requirements.lock

RUN groupadd -g 1000 lf 2>/dev/null || true; \
    useradd -u 1000 -g 1000 -m -s /bin/bash lf 2>/dev/null || true

# CuPy compiles its kernels into a cache under $HOME; a user without a home here (any UID but 1000) would lose the
# GPU silently (review B1-9): a cache every user can write
ENV CUPY_CACHE_DIR=/tmp/cupy-kernel-cache

WORKDIR /lf/visualizations
EXPOSE 8479
CMD ["python3", "server/serve.py", "--host", "0.0.0.0", "--port", "8479"]
