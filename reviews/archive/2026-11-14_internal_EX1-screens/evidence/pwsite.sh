#!/bin/sh
# usage: pwsite.sh script.mjs args...  : a Playwright container with its own network namespace (no host port) serving
# $P/site at http://127.0.0.1:8702/lfphys/ inside the container (python http.server), then running the script
P=<scratch>
S=$1; shift
docker run --rm --init --name lf-rvp-pws-$$ --shm-size=2g --memory=4g -v $P/pw:/pw -v $P/site:/srv:ro -v <repo>/visualizations/tests/browser:/t:ro -v $P/js:/js:ro \
  -e LFVIZ_LANG=${LANGV:-en} -e SHOTS=/pw/shots_site -e ALL_RECS=${ALL_RECS:-1} -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy sh -c "cp /t/*.mjs /pw/ && cp /js/*.mjs /pw/ 2>/dev/null; (cd /srv && python3 -m http.server 8702 --bind 127.0.0.1 >/dev/null 2>&1 &) ; sleep 1; node /pw/$S $*"
