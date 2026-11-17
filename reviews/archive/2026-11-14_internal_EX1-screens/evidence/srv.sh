#!/bin/sh
# private server lf-rvp-srv on port 8702: the repo read-only, recordings = scratch copy (real + toy)
P=<scratch>
docker rm -f lf-rvp-srv >/dev/null 2>&1
docker run -d --name lf-rvp-srv --memory=6g -p 127.0.0.1:8702:8479 -v <repo>:/lf:ro -v $P/runs:/lf/visualizations/runs \
  -v $P/rec:/rec:ro -e LFVIZ_RECORDINGS=/rec \
  -e LFPHYS_NO_GPU=1 ${EXTRA:--e LFVIZ_EXTRA=/lf/visualizations/tests/site_worlds} "$@" \
  -w /lf/visualizations lfphys-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 2
for i in $(seq 1 60); do curl -sf http://127.0.0.1:8702/api/health >/dev/null && break; sleep 0.5; done
curl -s http://127.0.0.1:8702/api/health | head -c 300; echo
