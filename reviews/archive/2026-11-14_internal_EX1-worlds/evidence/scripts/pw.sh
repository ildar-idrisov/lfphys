#!/bin/sh
# Playwright in the network namespace of lf-rvw-srv (the server is 127.0.0.1:8479 there; the site is served by lib.mjs on 8090)
W=/tmp/claude-1000/-home-ildar-hdd/2d877fb3-83c1-460d-af16-9ddd26aff08b/scratchpad/explore/rv/w
s=$1; shift
docker run --rm --init --name lf-rvw-pw-$$ --shm-size=1g --network container:lf-rvw-srv --memory=4g \
  -v $W/pw:/pw -v $W/site:/site:ro -v $W/shots:/shots -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy node /pw/$s "$@"
