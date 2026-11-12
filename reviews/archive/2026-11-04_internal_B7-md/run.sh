#!/bin/sh
# Run one review script in the project's image, CPU only, engine mounted read-only; output to <name>.out here.
# usage: ./run.sh <name>        (runs <name>.py, writes <name>.out)
# Reviewer's root path (fix only these two lines if the folder moves):
REVIEW=/home/ildar/hdd/projects/i/light-funnel/engine/reviews/2026-11-04_internal_B7-md
ENGINE=/home/ildar/hdd/projects/i/light-funnel/engine
name="$1"
docker run --rm --name "lf-b7rm-$name" -v "$ENGINE":/lf:ro -v "$REVIEW":/out \
  -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz \
  python3 "/out/$name.py" > "$REVIEW/$name.out" 2>&1
echo "exit $?" >> "$REVIEW/$name.out"
