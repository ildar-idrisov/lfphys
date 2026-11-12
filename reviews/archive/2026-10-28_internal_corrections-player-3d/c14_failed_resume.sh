#!/bin/bash
# C1 review, check 14: a resume whose rebuild fails (here: the world's parameters no longer accepted by the code — as
# after a parameter is renamed or removed — simulated by adding an unknown key to the latest world's parameters in the
# run's meta.json while the review server is stopped). What state does the run end in, can the owner retry once the
# cause is gone, and what does the player say?
# Own server container lf-c1rev-srv only. Output: out/c14_failed_resume.txt
set -u
REV=$(cd "$(dirname "$0")" && pwd)
ENGINE=$(cd "$REV/../../.." && pwd)  # root path fixed after the move to reviews/archive/ (processing, 2026-10-28)
RUNS=${RUNS:?runs dir of the review server}
B=http://127.0.0.1:8502
meta() { curl -s $B/api/runs/$1 | python3 -c 'import json,sys; m=json.load(sys.stdin); print("state", m.get("state"), "| resumed", m.get("resumed"), "| errors", (m.get("errors") or [])[-1:])'; }
edit() { docker run --rm --name lf-c1rev-c14py --user 1000:1000 -v "$RUNS":/runs -w /runs light-funnel-viz python3 -c "
import json; p = '/runs/$1/meta.json'; m = json.load(open(p))
w = m['worlds'][-1]['params']
if '$2' == 'add': w['zz_removed_param'] = 1
else: w.pop('zz_removed_param', None)
json.dump(m, open(p, 'w'))
print('meta.json: worlds[-1].params', '$2', 'zz_removed_param')"; }
wait_up() { for i in $(seq 1 60); do curl -sf $B/api/health >/dev/null && return 0; sleep 1; done; return 1; }
{
echo "C1 check 14 — a failed rebuild ($(date -Iseconds))"
RID=$(curl -s -X POST $B/api/runs -H 'Content-Type: application/json' -d '{"viz":"v01_light_travel","seed":6}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl -s -X POST $B/api/runs/$RID/command -H 'Content-Type: application/json' -d '{"cmd":"play"}' >/dev/null; sleep 3
curl -s -X POST $B/api/runs/$RID/stop >/dev/null; sleep 2
echo "run $RID recorded and suspended: $(meta $RID)"
docker stop lf-c1rev-srv >/dev/null; edit $RID add; docker start lf-c1rev-srv >/dev/null; wait_up
echo "⏺ (play): $(curl -s -X POST $B/api/runs/$RID/command -H 'Content-Type: application/json' -d '{"cmd":"play"}')"; sleep 4
echo "after the failed rebuild: $(meta $RID)"
docker stop lf-c1rev-srv >/dev/null; edit $RID remove; docker start lf-c1rev-srv >/dev/null; wait_up
echo "the cause removed, server restarted: $(meta $RID)"
echo "⏺ again: $(curl -s -X POST $B/api/runs/$RID/command -H 'Content-Type: application/json' -d '{"cmd":"play"}')"
echo "POST /resume: $(curl -s -X POST $B/api/runs/$RID/resume)"
echo "RUN=$RID"
} 2>&1 | tee "$REV/out/c14_failed_resume.txt"
