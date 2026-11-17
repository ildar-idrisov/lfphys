#!/bin/bash
# dr.sh NAME MEM [docker opts...] -- cmd...   : run in lfphys-viz with repo RO and scratch RW at /s
name=$1; mem=$2; shift 2
opts=()
while [ "$1" != "--" ]; do opts+=("$1"); shift; done
shift
exec docker run --rm --name "lf-rvf-$name" --memory="$mem" --memory-swap="$mem" -e LFPHYS_NO_GPU=1 -e PYTHONDONTWRITEBYTECODE=1 \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v <repo>:/lf:ro \
  -v <scratch>:/s \
  -w /lf/visualizations "${opts[@]}" lfphys-viz "$@"
