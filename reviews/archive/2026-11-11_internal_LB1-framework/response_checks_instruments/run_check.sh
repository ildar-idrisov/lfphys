#!/bin/sh
# Run one of the reviewer's client scripts (or one of ours) against the processor's PRIVATE server (lf-lpi-srv, port
# 8611; never the shared one on 8479), in the light-funnel-viz image with --network host.
#   run_check.sh <before|after> <script path inside the review folders, e.g. /rev/c01_sweep_closed_form.py> [env K=V ...]
# /out is this folder (lbrf_client.py, a copy of the reviewer's with the port changed, is imported from it); the
# reviewer's folder is mounted read-only at /rev, so its own outputs are never overwritten.
phase=$1; script=$2; shift 2
RC=$(cd "$(dirname "$0")" && pwd)
REV=$(dirname "$RC")
name=$(basename "$script" .py)
envs=""; for kv in "$@"; do envs="$envs -e $kv"; done
docker run --rm --name lf-lpi-chk-$name --memory=2g --network host -v "$RC":/out -v "$REV":/rev:ro $envs \
  -e PYTHONDONTWRITEBYTECODE=1 light-funnel-viz python3 "$script" > "$RC/$phase/$name.out" 2>&1
rc=$?
for f in "$RC"/*.json; do [ -e "$f" ] && mv "$f" "$RC/$phase/"; done
echo "[$name exit $rc]"; tail -20 "$RC/$phase/$name.out"
