#!/bin/bash
# Run one review script in the engine's image, CPU only, the engine mounted read-only (from engine/):
#   reviews/2026-11-04_internal_B8-fdtd/run.sh <name> <script.py> [args...]
set -u
NAME=$1; shift
SCRIPT=$1; shift
E=/home/ildar/hdd/projects/i/light-funnel/engine
R=$E/reviews/2026-11-04_internal_B8-fdtd
timeout 600 docker run --rm --name lf-b8rf-$NAME -v $E:/lf:ro -v $R:/out -e PYTHONDONTWRITEBYTECODE=1 \
  -e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/lfphys -w /lf/lfphys light-funnel-viz python3 /out/$SCRIPT "$@" \
  > $R/${SCRIPT%.py}.out 2>&1
echo "rc=$?" >> $R/${SCRIPT%.py}.out
