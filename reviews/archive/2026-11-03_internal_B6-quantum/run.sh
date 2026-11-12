#!/bin/bash
# Run a review script in the project's Docker image, engine mounted read-only, outputs to this folder.
# usage: ./run.sh <name-suffix> <script.py> [args...]   (container name lf-b6rq-<suffix>)
R=/home/ildar/hdd/projects/i/light-funnel/engine/reviews/2026-11-03_internal_B6-quantum
E=/home/ildar/hdd/projects/i/light-funnel/engine
name=lf-b6rq-$1; shift
script=$1; shift
docker run --rm --name "$name" --user 1000:1000 -e HOME=/tmp --cpus 4 -e OMP_NUM_THREADS=4 -e OPENBLAS_NUM_THREADS=4 -e MKL_NUM_THREADS=4 \
  -v $E:/lf:ro -v $R:/out -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 \
  -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server \
  -w /lf/lfphys light-funnel-viz python3 /out/$script "$@"
