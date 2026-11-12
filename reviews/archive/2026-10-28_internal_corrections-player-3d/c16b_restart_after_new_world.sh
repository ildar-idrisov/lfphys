#!/bin/bash
# C1 review, check 16b (variant of c16): the server restarted gracefully (docker restart) a few seconds after a «Новый мир», then
# started again and the run resumed. meta.json is saved every 10 s while a run computes, so it may not know the newest
# world yet; the resume takes the world to rebuild from meta["worlds"][-1] but the script from the stream (after its
# last header). Own server container lf-c1rev-srv only. Output: out/c16b_restart_after_new_world.txt
set -u
REV=$(cd "$(dirname "$0")" && pwd)
ENGINE=$(cd "$REV/../../.." && pwd)  # root path fixed after the move to reviews/archive/ (processing, 2026-10-28)
RUNS=${RUNS:?runs dir of the review server}
B=http://127.0.0.1:8502
wait_up() { for i in $(seq 1 60); do curl -sf $B/api/health >/dev/null && return 0; sleep 1; done; return 1; }
heads() { docker run --rm --name lf-c1rev-c16py --user 1000:1000 -v "$ENGINE":/lf:ro -v "$RUNS":/runs -w /lf/visualizations light-funnel-viz python3 -c "
import sys
sys.path[:0] = ['/lf/visualizations/server']
from lfviz import protocol
data = open('/runs/$1/stream.lfrec', 'rb').read()
for off, msg in protocol.iter_stream(data, len(protocol.MAGIC)):
    m = protocol.peek_meta(msg)
    if m.get('type') == 'header':
        print('  stream header: world', m.get('world'), 'preset', m.get('preset'), 'title', m.get('title'))
    if m.get('type') == 'notice' and ('Продолжение' in m.get('text', '') or 'восстановлен' in m.get('text', '')):
        print('  stream notice:', m.get('text')[:110])
"; }
{
echo "C1 check 16b — a graceful restart after a new world ($(date -Iseconds))"
RID=$(curl -s -X POST $B/api/runs -H 'Content-Type: application/json' -d '{"viz":"v01_light_travel","preset":"measure_c","seed":3}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl -s -X POST $B/api/runs/$RID/command -H 'Content-Type: application/json' -d '{"cmd":"play"}' >/dev/null; sleep 12
curl -s -X POST $B/api/runs/$RID/command -H 'Content-Type: application/json' -d '{"cmd":"new_world","args":{"preset":"sun_earth"}}' >/dev/null
sleep 1
curl -s -X POST $B/api/runs/$RID/command -H 'Content-Type: application/json' -d '{"cmd":"play"}' >/dev/null; sleep 2
docker restart lf-c1rev-srv >/dev/null; echo "server restarted (docker restart: SIGTERM, graceful) 3 s after new_world"
wait_up
curl -s $B/api/runs/$RID | python3 -c 'import json,sys; m=json.load(sys.stdin); print("after the restart: state", m["state"], "| meta worlds", [(w["n"], w.get("preset")) for w in m.get("worlds", [])], "| preset", m.get("preset"), "| sim_t", m["sim_t"])'
heads $RID
curl -s -X POST $B/api/runs/$RID/command -H 'Content-Type: application/json' -d '{"cmd":"play"}'; echo; sleep 4
curl -s -X POST $B/api/runs/$RID/stop >/dev/null; sleep 2
curl -s $B/api/runs/$RID | python3 -c 'import json,sys; m=json.load(sys.stdin); print("resumed: state", m["state"], "| meta worlds", [(w["n"], w.get("preset")) for w in m.get("worlds", [])], "| errors", m.get("errors"))'
heads $RID
} 2>&1 | tee "$REV/out/c16b_restart_after_new_world.txt"
