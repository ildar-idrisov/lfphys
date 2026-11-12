"""Small client for the review's checks against a PRIVATE server (never the shared one on 8479).

The server under test was started as (from engine/):

    docker run -d --name lf-lbrf-srv --memory=6g -p 8601:8479 -v <engine>:/lf:ro -v <scratch>/runs:/lf/visualizations/runs \
      -e LFPHYS_NO_GPU=1 -e LFVIZ_PLAYGROUND_CKPT=6 \
      -e LFVIZ_EXTRA=/lf/visualizations/tests/playgrounds:/lf/visualizations/tests/instruments_worlds \
      -e PYTHONDONTWRITEBYTECODE=1 -e OMP_NUM_THREADS=2 -w /lf/visualizations light-funnel-viz \
      python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 3

Scripts using this module run in the same image with ``--network host`` and import it from /out.
"""

import json
import os
import struct
import time
import urllib.error
import urllib.request

BASE = os.environ.get("LBRF_BASE", "http://127.0.0.1:8611")  # [response] the processor's private server lf-lpi-srv


def req(method, path, body=None, raw=False, timeout=120):
    data = None if body is None else json.dumps(body).encode()
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={"Content-Type": "application/json"} if data is not None else {})
    try:
        with urllib.request.urlopen(r, timeout=timeout) as f:
            out = f.read()
            return (f.status, out) if raw else (f.status, json.loads(out or b"null"))
    except urllib.error.HTTPError as e:
        out = e.read()
        try:
            return e.code, (out if raw else json.loads(out or b"null"))
        except ValueError:
            return e.code, out


def post(path, body=None, **kw):
    return req("POST", path, body if body is not None else {}, **kw)


def get(path, **kw):
    return req("GET", path, **kw)


def cmd(rid, c, args=None):
    return post(f"/api/runs/{rid}/command", {"cmd": c, "args": args or {}})


def record(rid):
    """Every message's JSON part of the run's record (the stream: 8-byte head, then u32 length | message)."""
    st, buf = get(f"/api/runs/{rid}/stream", raw=True)
    assert st == 200, st
    out, off = [], 8
    while off + 4 <= len(buf):
        (n,) = struct.unpack_from("<I", buf, off)
        m = off + 4
        (jl,) = struct.unpack_from("<I", buf, m)
        out.append(json.loads(buf[m + 4:m + 4 + jl]))
        off = m + n
    return out


def wait(pred, timeout=60.0, step=0.1):
    t0 = time.monotonic()
    while True:
        v = pred()
        if v:
            return v
        if time.monotonic() - t0 > timeout:
            raise TimeoutError("condition not reached")
        time.sleep(step)


def start(viz, preset=None, seed=1, params=None):
    body = {"viz": viz, "seed": seed}
    if preset:
        body["preset"] = preset
    if params:
        body["params"] = params
    st, js = post("/api/runs", body)
    assert st == 200, (st, js)
    rid = js["id"]
    wait(lambda: any(m["type"] == "header" for m in record(rid)), 60)
    return rid


def sweep_done(rid, n, timeout=600):
    def done():
        st, js = get(f"/api/runs/{rid}/sweeps/{n}")
        return js if js.get("state") not in ("starting", "running") and not js.get("active") else None
    return wait(done, timeout, 0.3)
