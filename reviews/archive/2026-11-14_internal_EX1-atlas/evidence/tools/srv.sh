#!/bin/bash
# srv.sh NAME REPO_DIR RUNS RECS [extra -e opts...]  : private server on 127.0.0.1:8701
name=$1; repo=$2; runs=$3; recs=$4; shift 4
docker rm -f "lf-rvf-$name" >/dev/null 2>&1
docker run -d --name "lf-rvf-$name" --memory=6g --memory-swap=6g -p 127.0.0.1:8701:8479 \
  --user "$(id -u):$(id -g)" -e HOME=/tmp -e LFPHYS_NO_GPU=1 -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$repo":/lf${RO:-:ro} -v "$runs":/runs -v "$recs":/recs:ro -e LFVIZ_RECORDINGS=/recs "$@" \
  -w /lf/visualizations lfphys-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --runs-dir /runs --max-workers 2
