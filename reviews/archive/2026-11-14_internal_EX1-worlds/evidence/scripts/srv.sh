#!/bin/sh
# private server lf-rvw-srv on 127.0.0.1:8703; repo read-only; runs into scratch
W=/tmp/claude-1000/-home-ildar-hdd/2d877fb3-83c1-460d-af16-9ddd26aff08b/scratchpad/explore/rv/w
docker rm -f lf-rvw-srv >/dev/null 2>&1
docker run -d --name lf-rvw-srv --memory=6g -p 127.0.0.1:8703:8479 -v /home/ildar/hdd/projects/i/lfphys:/lf:ro -v $W/runs:/lf/visualizations/runs \
  -e LFPHYS_NO_GPU=1 -e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 --user "$(id -u):$(id -g)" \
  -w /lf/visualizations lfphys-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 1
for i in $(seq 1 60); do curl -sf http://127.0.0.1:8703/api/health >/dev/null && break; sleep 0.5; done
curl -s http://127.0.0.1:8703/api/health | head -c 300; echo
