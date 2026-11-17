import json, sys, time, urllib.request, urllib.error, hashlib
BASE = "http://127.0.0.1:8701"
def post(path, body=None, raw=None, ctype="application/json"):
    data = raw if raw is not None else json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, method="POST", headers={"Content-Type": ctype})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.status, dict(r.headers), r.read(), time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(), time.time() - t0
def show(tag, r):
    st, h, body, dt = r
    info = body[:260].decode("utf-8", "replace") if not body[:2] == b"\x1f\x8b" else f"<gzip {len(body)} B>"
    print(f"{tag}: {st} src={h.get('X-LF-Source')} {dt:.1f}s {info}", flush=True)
    return r
def _cases():
    S = "/api/atlas/s03_projectile/explore/point"
    cases = [
     ("refused h=0 angle=0", S, {"values": {"h_m": 0.0, "angle_deg": 0.0}}),
     ("refused h=0 angle=-20 (off-grid)", S, {"values": {"h_m": 0.0, "angle_deg": -20.0}}),
     ("off-grid h=1.5", S, {"values": {"h_m": 1.5}}),
     ("off-grid angle=-30 h=20 v0=40", S, {"values": {"h_m": 20.0, "angle_deg": -30.0, "v0": 40.0}}),
     ("schema max h=21", S, {"values": {"h_m": 21.0}}),
     ("string number", S, {"values": {"h_m": "2"}}),
     ("bool for float", S, {"values": {"h_m": True}}),
     ("not a control (object)", S, {"values": {"object": "ball67"}}),
     ("not a param", S, {"values": {"zzz": 1}}),
     ("seed bool", S, {"values": {}, "seed": True}),
     ("seed -1", S, {"values": {}, "seed": -1}),
     ("seed 2^63", S, {"values": {}, "seed": 2**63}),
     ("seed float", S, {"values": {}, "seed": 1.0}),
     ("seed 7 (deterministic world)", S, {"values": {}, "seed": 7}),
     ("extra body key", S, {"values": {}, "x": 1}),
     ("values list", S, {"values": [1]}),
     ("body list", S, [1]),
     ("body null", S, None),
     ("unknown world", "/api/atlas/zz_none/explore/point", {"values": {}}),
     ("unknown atlas", "/api/atlas/s03_projectile/nope/point", {"values": {}}),
     ("alias id u32 (v02_double_slit)", "/api/atlas/v02_double_slit/explore/point", {"values": {}}),
     ("world=.. encoded", "/api/atlas/%2e%2e/explore/point", {"values": {}}),
     ("atlas=../ encoded", "/api/atlas/s03_projectile/..%2Fexplore/point", {"values": {}}),
     ("world=../../etc encoded", "/api/atlas/..%2F..%2Fetc/explore/point", {"values": {}}),
     ("world with dot-dot path", "/api/atlas/../atlas/s03_projectile/explore/point", {"values": {}}),
     ("playground world", "/api/atlas/p01_gravity/explore/point", {"values": {}}),
     ("world without screens", "/api/atlas/u31_light_travel/explore/point", {"values": {}}),
    ]
    for tag, path, body in cases:
        show(tag, post(path, body))
    show("NaN literal", post(S, raw=b'{"values": {"h_m": NaN}}'))
    show("Infinity literal", post(S, raw=b'{"values": {"v0": Infinity}}'))
    show("not JSON", post(S, raw=b'{values'))
    show("bad utf8", post(S, raw=b'\xff\xfe'))
    show("huge int value", post(S, raw=b'{"values": {"h_m": 1' + b'0'*5000 + b'}}'))
if __name__ == '__main__':
    _cases()
