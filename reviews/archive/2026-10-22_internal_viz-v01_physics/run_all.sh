#!/bin/sh
# Re-run every reviewer check of this folder in the project's Docker image and refresh outputs/.
# Usage (from anywhere):  sh reviews/2026-10-22_internal_viz-v01_physics/run_all.sh
set -e
LF=$(cd "$(dirname "$0")/../../.." && pwd)   # root path: the light-funnel tree (path fixed after the move to archive/)
R=reviews/archive/2026-10-22_internal_viz-v01_physics  # (path fixed after the move to archive/)
mkdir -p "$LF/$R/outputs"
for s in check_schwarzschild check_rk_and_frames check_apparatus check_kepler check_simultaneity \
         check_causality check_sweep check_colocated_flash check_fast_receivers; do
  echo "== $s"
  docker run --rm --user "$(id -u):$(id -g)" -v "$LF:/lf" -w /lf/visualizations \
    -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server light-funnel-viz \
    python3 -W ignore "/lf/$R/$s.py" > "$LF/$R/outputs/$s.txt" 2>&1 || echo "   (exit code $?)"
done
