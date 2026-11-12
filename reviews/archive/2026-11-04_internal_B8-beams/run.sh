#!/bin/bash
# Usage: run.sh <name-suffix> <script relative to the review folder> [args...]
# Runs a review script in the project's image, engine mounted read-only, this folder at /out, CPU only.
R=/home/ildar/hdd/projects/i/light-funnel/engine/reviews/2026-11-04_internal_B8-beams
X=$1; shift; S=$1; shift
docker run --rm --name lf-b8rb-$X --memory=6g -v /home/ildar/hdd/projects/i/light-funnel/engine:/lf:ro -v $R:/out \
  -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/$S "$@"
