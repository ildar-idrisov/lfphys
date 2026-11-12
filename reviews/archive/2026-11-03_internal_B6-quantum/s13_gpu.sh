#!/bin/bash
# How s13_gpu.py was run on GPU 0 (through the session's GPU guard: one job at a time, started below 60 C, stopped at
# 83 C; GPU 1 of this host is faulty and is never used). Output: s13_gpu.out
R=/home/ildar/hdd/projects/i/light-funnel/engine/reviews/2026-11-03_internal_B6-quantum
E=/home/ildar/hdd/projects/i/light-funnel/engine
GUARD=${GUARD:-/tmp/claude-1000/-home-ildar-hdd/2d877fb3-83c1-460d-af16-9ddd26aff08b/scratchpad/gpu_run.sh}
$GUARD lf-b6rq-gpu1 --rm --gpus '"device=0"' --user 1000:1000 -e HOME=/tmp --cpus 4 -e OMP_NUM_THREADS=4 \
  -v $E:/lf:ro -v $R:/out -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server \
  -w /lf/lfphys light-funnel-viz python3 /out/s13_gpu.py
