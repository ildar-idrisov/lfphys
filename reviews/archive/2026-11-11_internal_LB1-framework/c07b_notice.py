"""c07b: the notices and the temperature / energy around the carry of c07 (b) (p03 gas, 3-D, boundary periodic ->
walls): is the atoms' state carried, and does the notice say?"""
import json, sys
sys.path.insert(0, "/out")
from lbrf_client import get, record
runs = [r for r in get("/api/runs")[1] if "-p03-" in r["id"]]
for r in runs[:2]:
    rec = record(r["id"])
    hs = [i for i, m in enumerate(rec) if m["type"] == "header"]
    fr = [m for m in rec if m["type"] == "frame" and m.get("meas")]
    def last_before(i):
        f = [m for m in rec[:i] if m["type"] == "frame" and m.get("meas")]
        return f[-1] if f else None
    def first_after(i):
        f = [m for m in rec[i:] if m["type"] == "frame" and m.get("meas")]
        return f[0] if f else None
    a, b = last_before(hs[-1]), first_after(hs[-1])
    notes = [m["text"] for m in rec[hs[-1]:] if m["type"] == "notice"]
    st = rec[hs[-1]]["params"]["scene"]["objects"][0]
    print(r["id"], "| carried object has a state:", "state" in st, "| values:", json.dumps(st["values"], ensure_ascii=False)[:120])
    for k in ("T", "e", "N"):
        print(f"   {k}: last frame of world 1 (t={a['t']:.4g}) {a['meas'].get(k)!r} -> first frame of world 2 (t={b['t']:.4g}) {b['meas'].get(k)!r}")
    print("   notices:", notes[:3])
