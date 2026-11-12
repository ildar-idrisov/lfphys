"""Sampling of drawn curves (UX-ui item 3): the points the run sends for each trail / orbit / path and the turning
angle between consecutive segments (360/turning angle = points per turn), at the world's default speed and the
runner's 20 frames/s (one advance per frame, as Runner.run does). Harness, no server."""
import sys, json, math
import numpy as np
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf"]
from tests.harness import Harness

def turning(P):
    """Turning angles (deg) between consecutive segments of a polyline P (n x 3), zero-length segments dropped."""
    d = np.diff(P, axis=0)
    L = np.linalg.norm(d, axis=1)
    d = d[L > 0]
    if len(d) < 2:
        return np.array([])
    u = d / np.linalg.norm(d, axis=1)[:, None]
    c = np.clip(np.sum(u[1:] * u[:-1], axis=1), -1, 1)
    return np.degrees(np.arccos(c))

def run(h, frames, speed=None):
    if speed:
        h.runner.speed = speed
    for _ in range(frames):
        h.runner._advance(h.sim.t + h.runner.speed / h.runner.fps, budget=None)
        h.runner._frame(0.0)

def p01(preset, speed_mult=1.0, frames=200, label=None):
    h = Harness("p01_gravity", preset=preset)
    sp = h.runner.speed * speed_mult
    run(h, frames, sp)
    tr = {}
    for m, b in h.msgs:
        if m.get("type") != "trail" or m.get("reset"):
            continue
        off = 0
        P = b["pts"].reshape(-1, 3)
        for k, n in zip(m["ids"], m["counts"]):
            tr.setdefault(k, []).append(P[off:off + n]); off += n
    labels = {k: o["label"] for k, o in h.sim.objects.items()}
    out = {}
    for k, parts in tr.items():
        P = np.concatenate(parts)
        a = turning(P)
        if not len(a):
            continue
        out[labels.get(k.split("#")[0], k) + ("#" + k.split("#")[1] if "#" in k else "")] = {
            "points": int(len(P)), "turn_median_deg": round(float(np.median(a)), 2), "turn_max_deg": round(float(a.max()), 2),
            "points_per_turn_median": round(360.0 / max(float(np.median(a)), 1e-9), 1)}
    print(json.dumps({"world": label or f"p01 {preset}", "speed_s_per_s": sp, "frames": frames, "trails": out}, ensure_ascii=False), flush=True)

def v04(preset, frames=200, speed_mult=1.0):
    h = Harness("v04_orbits", preset=preset)
    sp = h.runner.speed * speed_mult
    run(h, frames, sp)
    xs, ys, ns = [], [], []
    for m, b in h.msgs:
        if m.get("type") == "trail":
            xs.append(b["x"]); ys.append(b["y"]); ns.append(m["n"])
    if not xs:
        print(json.dumps({"world": f"v04 {preset}", "trail": None})); return
    x, y = np.concatenate(xs), np.concatenate(ys)
    phi = np.unwrap(np.arctan2(y, x))
    dphi = np.abs(np.diff(phi))
    turns = abs(phi[-1] - phi[0]) / (2 * math.pi)
    P = np.stack([x, y, 0 * x], 1)
    a = turning(P)
    print(json.dumps({"world": f"v04 {preset}", "speed_s_per_s": sp, "frames": frames, "msgs": len(ns),
                      "samples": int(len(x)), "turns": round(turns, 2),
                      "dphi_median_deg": round(float(np.degrees(np.median(dphi))), 3),
                      "dphi_max_deg": round(float(np.degrees(dphi.max())), 3),
                      "turn_angle_max_deg": round(float(a.max()), 3) if len(a) else None,
                      "samples_per_msg_max": int(max(ns))}), flush=True)

def v09(preset, frames=200):
    h = Harness("v09_thomas_3d", preset=preset)
    run(h, frames)
    P = [b["pts"].reshape(-1, 3) for m, b in h.msgs if m.get("type") == "path"]
    if not P:
        print(json.dumps({"world": f"v09 {preset}", "path": None})); return
    P = np.concatenate(P)
    a = turning(P)
    print(json.dumps({"world": f"v09 {preset}", "frames": frames, "points": int(len(P)),
                      "turn_median_deg": round(float(np.median(a)), 3) if len(a) else None,
                      "turn_p95_deg": round(float(np.percentile(a, 95)), 3) if len(a) else None,
                      "turn_max_deg": round(float(a.max()), 3) if len(a) else None}), flush=True)

which = sys.argv[1:] or ["p01", "v04", "v09"]
if "p01" in which:
    p01("inner")
    p01("inner", 10.0, label="p01 inner x10 speed")
    p01("inner", 0.1, label="p01 inner x0.1 speed")
    p01("hole_stars")
    p01("kerr_orbits", frames=400)
    p01("pn_inspiral", frames=400)
if "v04" in which:
    for pr in ("default", "mercury", "neutron_star", "bh_isco", "newton_ellipse"):
        v04(pr)
    v04("default", speed_mult=100.0)
if "v09" in which:
    for pr in ("thomas", "circle", "lab"):
        v09(pr)
