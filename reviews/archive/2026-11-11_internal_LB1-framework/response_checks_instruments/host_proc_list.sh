#!/bin/sh
# List the python processes inside a private server container (name as $1), as the reviewer's c03 did (no ps there).
docker exec "$1" python3 -c "
import os
for p in sorted(os.listdir('/proc'), key=lambda s: int(s) if s.isdigit() else 0):
    if not p.isdigit(): continue
    try:
        cmd = open(f'/proc/{p}/cmdline').read().replace(chr(0), ' ').strip()
        adj = open(f'/proc/{p}/oom_score_adj').read().strip()
    except OSError: continue
    if 'python' in cmd: print(p, 'oom_adj', adj, cmd[:110])
"
