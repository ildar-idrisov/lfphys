"""Live-point endpoint probes against the private server (127.0.0.1:8701)."""
import json, sys, time, urllib.request, urllib.error, hashlib
from pathlib import Path
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations/site")
BASE = "http://127.0.0.1:8701"
REC = Path("/lf/visualizations/recordings")

def post(path, body, raw=None):
    data = raw if raw is not None else json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, method="POST", headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.status, dict(r.headers), r.read(), time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(), time.time() - t0

def atlas_file(world, aid, idx):
    ix = json.loads((REC / world / "index.json").read_text())
    e = next(a for a in ix["atlases"] if a["id"] == aid)
    man = json.loads((REC / world / e["file"]).read_text())
    name = man["points"][idx][0]
    return (REC / world / e["file"]).parent / name, man

def show(tag, r):
    st, h, body, dt = r
    info = body[:300].decode("utf-8", "replace") if not body[:2] == b"\x1f\x8b" else f"<gzip {len(body)} B sha {hashlib.sha256(body).hexdigest()[:8]}>"
    print(f"{tag}: {st} src={h.get('X-LF-Source')} key={h.get('X-LF-Key')} {dt:.1f}s {info}")
    return r

def _main():
  pass
if __name__ == "__main__":
  import atlas as A
from lfviz import registry
for world, aid, vals in [("s03_projectile", "explore", {"h_m": 1.0, "v0": 15.0, "angle_deg": 45.0, "air": False}),
                         ("s03_projectile", "explore", {"h_m": 5.0, "v0": 20.0, "angle_deg": 30.0, "air": True}),
                         ("s03_projectile", "explore", {"h_m": 0.0, "v0": 25.0, "angle_deg": 90.0, "air": True}),
                         ("s03_projectile", "lab.air", {}),
                         ("u32_double_slit", "explore", {"lam_nm": 400.0, "d_um": 300.0, "a_um": 10.0}),
                         ("u32_double_slit", "explore", {})]:
    spec = next(a for a in registry.atlases_of(registry.load(world)) if a["id"] == aid)
    full = {**A.defaults(spec), **vals}
    i = A.flat_index(spec["controls"], full)
    f, man = atlas_file(world, aid, i)
    r = show(f"{world}/{aid} p{i} {vals}", post(f"/api/atlas/{world}/{aid}/point", {"values": vals}))
    print(f"   equal to the site's {f.name}: {r[2] == f.read_bytes()} ({len(r[2])} vs {f.stat().st_size} B)")
    r2 = show("   again", post(f"/api/atlas/{world}/{aid}/point", {"values": vals}))
    print(f"   again equal: {r2[2] == r[2]}")
