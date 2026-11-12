#!/bin/sh
# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Run one review script in the runtime image with the engine mounted read-only (from engine/reviews/<this folder>):
#   sh scripts/run.sh s01_magnus_hard.py  -> out/s01_magnus_hard.txt
# Image: light-funnel-viz (CPU only). External-library checks use light-funnel-ext (IMAGE=light-funnel-ext).
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
ENGINE=$(cd "$HERE/../../.." && pwd)
S=$1; shift
NAME=lf-rev5-$(echo "$S" | cut -d_ -f1)
IMAGE=${IMAGE:-light-funnel-viz}
docker run --rm --name "$NAME" --user "$(id -u):$(id -g)" -v "$ENGINE":/lf:ro -v "$HERE":/r \
  -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/lfphys -e HOME=/tmp -w /r "$IMAGE" \
  python3 "scripts/$S" "$@" 2>&1 | tee "$HERE/out/${S%.py}.txt"
