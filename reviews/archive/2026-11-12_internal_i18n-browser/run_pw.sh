#!/bin/sh
# usage: run_pw.sh <script.mjs> [args...]  — runs a review script in Playwright 1.58.2 against the private server 8652
# (node_modules in the scratch dir /tmp/claude-1000/-home-ildar-hdd/2d877fb3-83c1-460d-af16-9ddd26aff08b/scratchpad/rv18b/pw; the review folder mounted read-only at /rev; shots and logs written to
# the review folder's shots/ and logs/)
s=$1; shift
docker run --rm --name lf-rv18b-pw-$(basename $s .mjs)${TAG:+-$TAG} --init --shm-size=2g --memory=4g --network host \
  -v /tmp/claude-1000/-home-ildar-hdd/2d877fb3-83c1-460d-af16-9ddd26aff08b/scratchpad/rv18b/pw:/pw -v /home/ildar/hdd/projects/i/lfphys/reviews/archive/2026-11-12_internal_i18n-browser:/rev:ro -v /home/ildar/hdd/projects/i/lfphys/reviews/archive/2026-11-12_internal_i18n-browser/shots:/shots -v /home/ildar/hdd/projects/i/lfphys/reviews/archive/2026-11-12_internal_i18n-browser/logs:/logs \
  -v /home/ildar/hdd/projects/i/lfphys/visualizations/tests/browser:/t:ro \
  --user 1000:1000 -e HOME=/tmp -e PORT=8652 -e LFVIZ_LANG -e W -e LANGS -e WORLDS -e TAG -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy \
  sh -c "cp /t/*.mjs /pw/ && cp /rev/*.mjs /pw/ && node /pw/$s $*"
