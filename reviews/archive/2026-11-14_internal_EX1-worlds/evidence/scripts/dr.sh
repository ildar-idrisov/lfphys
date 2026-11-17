#!/bin/sh
# run a command in lfphys-viz, CPU, memory-capped, repo read-only; $1 = container suffix
n=$1; shift
W=/tmp/claude-1000/-home-ildar-hdd/2d877fb3-83c1-460d-af16-9ddd26aff08b/scratchpad/explore/rv/w
docker run --rm --name lf-rvw-$n --memory=6g --cpus=4 -e LFPHYS_NO_GPU=1 --user "$(id -u):$(id -g)" \
  -v /home/ildar/hdd/projects/i/lfphys:/lf:ro -v $W:/w \
  -w /lf/visualizations -e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys lfphys-viz "$@"
