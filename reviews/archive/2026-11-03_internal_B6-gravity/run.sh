#!/bin/bash
# Run one reviewer script in Docker (CPU only), engine/ mounted read-only at /lf, this folder at /out.
# usage: reviews/2026-11-03_internal_B6-gravity/run.sh <name> <command...>   (from engine/)
# The output goes to /out/<name>.out (this folder).
set -u
ENGINE=$(cd "$(dirname "$0")/../.." && pwd)
HERE=$(cd "$(dirname "$0")" && pwd)
NAME=$1; shift
docker run --rm --name "lf-b6rg-$NAME" \
  -v "$ENGINE":/lf:ro -v "$HERE":/out \
  -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -e OMP_NUM_THREADS=2 -e OPENBLAS_NUM_THREADS=2 \
  -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys:/lf/visualizations/tests \
  -w /lf/lfphys --cpus 2 light-funnel-viz "$@" > "$HERE/$NAME.out" 2>&1
echo "exit $?" >> "$HERE/$NAME.out"
