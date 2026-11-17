#!/bin/sh
# usage: LANGV=en pw.sh script.mjs args...  (Playwright container lf-rvp-pw-<pid>); scripts from the repo's tests/browser and $P/js
P=<scratch>
S=$1; shift
docker run --rm --init --name lf-rvp-pw-$$ --shm-size=2g --network host --memory=4g -v $P/pw:/pw -v <repo>/visualizations/tests/browser:/t:ro -v $P/js:/js:ro \
  -e LFVIZ_LANG=${LANGV:-en} -e SHOTS=/pw/shots -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy sh -c "cp /t/*.mjs /pw/ && cp /js/*.mjs /pw/ 2>/dev/null; node /pw/$S $*"
