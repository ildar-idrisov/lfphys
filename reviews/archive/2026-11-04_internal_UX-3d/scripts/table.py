#!/usr/bin/env python3
"""Collect the tours' tour.json into the review's tables (markdown on stdout)."""
import json, glob, os, sys

root = sys.argv[1] if len(sys.argv) > 1 else "pw/out"
rows = []
for f in sorted(glob.glob(f"{root}/*/tour.json")):
    d = json.load(open(f))
    s = d.get("steps", {})
    df = s.get("default")
    if not df:
        rows.append((d["tag"], None, d)); continue
    rows.append((d["tag"], df, d))

print("| tour | canvas px | box corners on screen (of 8) | camera distance: opened → after F | up | volume | lines/paths | spheres/points | translucent meshes |")
print("|---|---|---|---|---|---|---|---|---|")
for tag, df, d in rows:
    if df is None:
        print(f"| {tag} | — | failed: {str(d.get('failed',''))[:60]} | | | | | | |"); continue
    s = d["steps"]
    dist0 = df["camera"]["dist"]; distF = s.get("reset", {}).get("dist", "—")
    kinds = {}
    for L in df["layers"]:
        for k in L["parts"]:
            kinds.setdefault(L["kind"], set()).add(k.split("/")[0])
    vol = any(L["kind"] == "volume" and L["visible"] for L in df["layers"])
    lines = sum(1 for L in df["layers"] if any(k.startswith(("Line", "LineSegments")) for k in L["parts"]) and L["visible"])
    sph = sum(1 for L in df["layers"] if L["kind"] in ("spheres", "points", "marks", "body") and L["visible"])
    tr = sum(1 for L in df["layers"] if L["visible"] and any("/transp" in k and "Mesh/" in k and "Shader" not in k for k in L["parts"]))
    up = df["camera"]["up"]
    upn = {"[0, 1, 0]": "y", "[1, 0, 0]": "z", "[0, 0, -1]": "x"}.get(str([round(u) for u in up]), str(up))
    print(f"| {tag} | {int(df['canvas']['w'])}×{int(df['canvas']['h'])} | {df['cornersInside']} | {dist0:.4g} → {distF if isinstance(distF, str) else f'{distF:.4g}'} | {upn} | {'yes' if vol else '—'} | {lines} | {sph} | {tr} |")

print()
print("| tour | draw calls | triangles | lines | ms per frame (software GL) | rAF/s while rotating | scene draws/s while rotating | script share |")
print("|---|---|---|---|---|---|---|---|")
for tag, df, d in rows:
    p, fp = d.get("perf"), d.get("fps")
    if not p or not fp:
        continue
    print(f"| {tag} | {p['calls']} | {p['triangles']} | {p['lines']} | {p['msPerRender']} | {fp['rafFps']} | {fp['drawsPerSec']} | {fp['scriptShare']} |")
