#!/bin/bash
# C1 review, check 09: a record whose last message was cut short (the server was killed mid-write: docker kill, OOM,
# power loss), then resumed (the record is appended to), then the server restarted. What does the server load?
# Uses only the reviewer's own server container lf-c1rev-srv (port 8502, runs dir $RUNS); the cut is simulated by
# truncating the record by 10 bytes while that server is stopped.
# Output: out/c09_partial_tail.txt
set -u
REV=$(cd "$(dirname "$0")" && pwd)
ENGINE=$(cd "$REV/../../.." && pwd)  # root path fixed after the move to reviews/archive/ (processing, 2026-10-28)
RUNS=${RUNS:?runs dir of the review server}
OUT=$REV/out/c09_partial_tail.txt
B=http://127.0.0.1:8502
py() { docker run --rm --name lf-c1rev-c09py --user 1000:1000 -v "$ENGINE":/lf:ro -v "$RUNS":/runs -w /lf/visualizations light-funnel-viz python3 -c "$1"; }
COUNT='
import sys, json
sys.path[:0] = ["/lf/visualizations/server"]
from lfviz import protocol
rid = sys.argv[1] if len(sys.argv) > 1 else None
'
wait_up() { for i in $(seq 1 60); do curl -sf $B/api/health >/dev/null && return 0; sleep 1; done; return 1; }
{
echo "C1 check 09 — a cut last message, a resume that appends, a restart ($(date -Iseconds))"
RID=$(curl -s -X POST $B/api/runs -H 'Content-Type: application/json' -d '{"viz":"v01_light_travel","seed":4}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl -s -X POST $B/api/runs/$RID/command -H 'Content-Type: application/json' -d '{"cmd":"play"}' >/dev/null
sleep 4
curl -s -X POST $B/api/runs/$RID/stop >/dev/null; sleep 2
echo "run $RID recorded and suspended: $(curl -s $B/api/runs/$RID | python3 -c 'import json,sys; m=json.load(sys.stdin); print("state", m["state"], "n_messages", m["n_messages"], "sim_t", m["sim_t"], "size", m["size"])')"
docker stop lf-c1rev-srv >/dev/null
py "
import os
p = '/runs/$RID/stream.lfrec'
n = os.path.getsize(p)
os.truncate(p, n - 10)
print('simulated crash mid-write: the record cut from', n, 'to', n - 10, 'bytes')
"
docker start lf-c1rev-srv >/dev/null; wait_up || echo "SERVER DID NOT COME UP"
echo "after the restart: $(curl -s $B/api/runs/$RID | python3 -c 'import json,sys; m=json.load(sys.stdin); print("state", m["state"], "n_messages", m["n_messages"], "sim_t", m["sim_t"], "size", m["size"])')"
curl -s -X POST $B/api/runs/$RID/command -H 'Content-Type: application/json' -d '{"cmd":"play"}'; echo
sleep 5
curl -s -X POST $B/api/runs/$RID/stop >/dev/null; sleep 2
echo "resumed for 5 s and suspended (same server): $(curl -s $B/api/runs/$RID | python3 -c 'import json,sys; m=json.load(sys.stdin); print("state", m["state"], "n_messages", m["n_messages"], "sim_t", m["sim_t"], "size", m["size"])')"
docker restart lf-c1rev-srv >/dev/null; wait_up || echo "SERVER DID NOT COME UP"
echo "after another restart: $(curl -s $B/api/runs/$RID | python3 -c 'import json,sys; m=json.load(sys.stdin); print("state", m["state"], "n_messages", m["n_messages"], "sim_t", m["sim_t"], "size", m["size"])')"
py "
import sys
sys.path[:0] = ['/lf/visualizations/server']
from lfviz import protocol
data = open('/runs/$RID/stream.lfrec', 'rb').read()
n, last, types = 0, None, {}
for off, msg in protocol.iter_stream(data, len(protocol.MAGIC)):
    try:
        m = protocol.peek_meta(msg)
    except Exception as e:
        print('parse: message', n, 'at', off, 'undecodable:', repr(e)[:120]); break
    n += 1; last = (off, m.get('type'), m.get('t')); types[m.get('type')] = types.get(m.get('type'), 0) + 1
print('parse of the file as the server does:', n, 'messages; last parsed', last, '; file size', len(data), '; types', types)
"
} 2>&1 | tee "$OUT"
