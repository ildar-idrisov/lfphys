"""04: adversarial live changes, actions and worlds through the test harness (visualizations/tests/harness.py).

Each scenario runs in its own child process with a wall-time box; reported: exceptions, error messages, failing checks
(ok False, or |rel| > tol), non-finite numbers in any message or blob, notices and end events, wall time.
Usage: python3 04_adversarial_live.py [scenario-name ...]
"""
import math
import multiprocessing as mpr
import sys
import time
import traceback

import numpy as np

BOX = 90.0  # seconds per scenario


def H(preset=None, **params):
    from harness import Harness
    return Harness("v04_orbits", preset, params or None)


def scale(h):
    s = h.sim
    return (s._period_estimate(s.track) or s.track.dyn) * s.T_s


def bad_checks(h):
    out = []
    for c in h.checks().values():
        if c.get("ok") is False or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]):
            out.append(f"{c['id']} '{c['label'][:70]}' value={c['value']!r} ref={c['ref']!r} rel={c['rel']!r} "
                       f"tol={c['tol']!r}")
    return out


def nonfinite(h):
    bad = []
    for m, b in h.msgs:
        def walk(x, path):
            if isinstance(x, float) and not math.isfinite(x):
                bad.append(f"{m.get('type')}:{path}={x}")
            elif isinstance(x, dict):
                for k, v in x.items():
                    walk(v, path + "." + str(k))
            elif isinstance(x, (list, tuple)):
                for i, v in enumerate(x[:50]):
                    walk(v, path + f"[{i}]")
        walk(m, "")
        for k, a in (b or {}).items():
            a = np.asarray(a)
            if a.dtype.kind == "f" and not np.all(np.isfinite(a)):
                bad.append(f"{m.get('type')}:blob {k} has {int(np.sum(~np.isfinite(a)))} non-finite")
    return bad[:12]


def frame_now(h):
    h.runner._frame(1.0)
    f = h.of("frame")[-1]
    keys = ("seg", "r", "alive", "status", "tau", "rate", "deficit", "v")
    return {k: f.get(k) for k in keys}


def summary(h, note=""):
    ev = [f"{e['kind']}@{e['t']:.4g}" for e in h.of("event") if e.get("kind") not in ("action", "periapsis", "segment")]
    segs = [f"{s['seg']}:{s['kind']}" for s in h.of("segment")]
    return {"note": note, "errors": [e[:300] for e in h.errors()], "bad_checks": bad_checks(h),
            "nonfinite": nonfinite(h), "notices": [n["text"][:200] for n in h.of("notice")], "segments": segs,
            "events": ev[:12], "n_checks": len(h.checks()), "frame": frame_now(h), "t": h.sim.t}


# ---------------------------------------------------------------------------------------------------------------
def s_r0_near_2M():
    h = H("default")
    h.run_to(0.3 * scale(h))
    h.set(r0=2.1)                     # speed 1.2 x c: must be refused
    h.set(r0=2.1, speed=0.9)          # 0.9 c at 2.1 M
    h.run_to(h.sim.t + 50 * h.sim.T_s * 1e3)
    return summary(h)


def s_r0_2p1_speed0():
    h = H("default", r0=2.1, speed=0.0)
    h.run_to(1e3 * h.sim.T_s)
    return summary(h)


def s_photon_sphere_circular():
    out = {}
    for r0 in (3.0001, 3.01, 3.1):
        h = H("default", r0=r0, speed=1.0)
        info = dict(h.sim.info)
        h.run_to(30 * 2 * math.pi * r0**1.5 * h.sim.T_s)
        out[r0] = {"kind": info["kind"], "em1": info["em1"], **summary(h)}
    return out


def s_marginally_bound_circular_4M():
    h = H("default", r0=4.0, speed=1.0)
    info = dict(h.sim.info)
    h.run_to(30 * 2 * math.pi * 4.0**1.5 * h.sim.T_s)
    return {"kind": info["kind"], "em1": info["em1"], "r_apo": info["r_apo"], **summary(h)}


def s_isco_exact_and_near():
    out = {}
    for r0 in (6.0, 5.9999, 6.0001):
        h = H("default", r0=r0, speed=1.0)
        info = dict(h.sim.info)
        h.run_to(60 * 2 * math.pi * r0**1.5 * h.sim.T_s)
        out[r0] = {"kind": info["kind"], **summary(h)}
    return out


def s_circular_inside_isco():
    out = {}
    for r0 in (5.0, 4.5):
        h = H("default", r0=r0, speed=1.0)
        info = dict(h.sim.info)
        h.run_to(80 * 2 * math.pi * r0**1.5 * h.sim.T_s)
        out[r0] = {"kind": info["kind"], **summary(h)}
    return out


def s_huge_r0():
    out = {}
    for sp in (1.2, 1.0, 0.0, 1.6, 0.3):
        h = H("default", r0=1e8, speed=sp)
        info = dict(h.sim.info)
        t0 = time.time()
        T = 2.5 * scale(h) if info["kind"] in ("bound", "circular") else None
        if T is None:
            te = h.sim.track.next_event_after(0.0, {"horizon", "escape"})
            T = 1.01 * te * h.sim.T_s if te else 3 * scale(h)
        h.run_to(T)
        out[sp] = {"kind": info["kind"], "wall": round(time.time() - t0, 2), **summary(h)}
    return out


def s_boost_unbind():
    h = H("default")
    h.run_to(0.4 * scale(h))
    h.action("boost", dv=0.5)
    info = dict(h.sim.info)
    te = h.sim.track.next_event_after(h.sim.t / h.sim.T_s, {"escape"})
    h.run_to(1.01 * te * h.sim.T_s if te else h.sim.t + 10 * scale(h))
    return {"kind": info["kind"], **summary(h)}


def s_repeated_boosts():
    h = H("default")
    P = scale(h)
    log = []
    for i in range(25):
        h.run_to(h.sim.t + 0.05 * P)
        n = len(h.errors())
        h.action("boost", dv=0.05)
        log.append((i, h.sim.info["kind"], h.errors()[-1][:80] if len(h.errors()) > n else ""))
        if h.sim.track.ended(h.sim.t / h.sim.T_s):
            break
    h.run_to(h.sim.t + 2 * P)
    return {"log": log[-6:], **summary(h)}


def s_repeated_brakes():
    h = H("default")
    P = scale(h)
    log = []
    for i in range(40):
        h.run_to(h.sim.t + 0.03 * P)
        n = len(h.errors())
        h.action("boost", dv=-0.05)
        log.append((i, h.sim.info["kind"], h.errors()[-1][:80] if len(h.errors()) > n else ""))
        if h.sim.track.ended(h.sim.t / h.sim.T_s):
            break
    h.run_to(h.sim.t + 3 * P)
    return {"log": log[-6:], **summary(h)}


def s_boost_stop_body():
    out = {}
    for law in ("GR", "newton"):
        h = H("default", gravity=law)
        h.run_to(0.3 * scale(h))
        h.action("boost", dv=-1.0)
        info = dict(h.sim.info)
        h.run_to(h.sim.t + 5 * h.sim.track.dyn * h.sim.T_s)
        out[law] = {"kind": info["kind"], **summary(h)}
    return out


def s_relaunch_during_plunge():
    h = H("radial")
    te = h.sim.track.next_event_after(0.0, {"horizon"}) * h.sim.T_s
    h.run_to(0.9 * te)
    h.action("relaunch")
    h.run_to(h.sim.t + 0.999 * te)
    h.action("boost", dv=0.05)   # deep in the fall, near the horizon
    h.run_to(h.sim.t + 2 * te)
    h.action("relaunch")         # after the horizon
    h.run_to(h.sim.t + 2 * te)
    return summary(h)


def s_ghost_toggles():
    out = {}
    for preset in ("default", "newton_ellipse", "plunge", "radial", "mercury"):
        h = H(preset)
        P = scale(h)
        h.run_to(0.6 * P)
        h.set(ghost=True)
        h.run_to(1.4 * P)
        h.set(ghost=False)
        h.set(ghost=True)
        h.run_to(2.2 * P)
        out[preset] = summary(h)
    return out


def s_ghost_superluminal_newton():
    h = H("newton_ellipse", r0=2.5, speed=1.5)   # Newton allows v > c; the GR ghost must be refused politely
    h.run_to(2 * scale(h))
    h.set(ghost=False)
    h.set(ghost=True)
    return summary(h)


def s_new_worlds():
    from harness import Harness
    h = Harness("v04_orbits", "default")
    h.run_to(0.3 * scale(h))
    log = []
    for params in ({"gravity": "newton", "radius_km": 100.0}, {"gravity": "GR", "radius_km": 0.0, "mass_msun": 1e9},
                   {"gravity": "GR", "mass_msun": 1.0, "radius_km": 4.43}, {"gravity": "GR", "mass_msun": 1.0,
                                                                            "radius_km": 2.95}):
        n = len(h.errors())
        h.cmd("new_world", params=params)
        log.append((params, h.errors()[-1][:120] if len(h.errors()) > n else "ok", h.sim.info["kind"]))
        h.run_to(h.sim.t + 2 * scale(h))
    return {"log": log, **summary(h)}


def s_near_radial_angles():
    out = {}
    for ang in (89.99999, -89.99999, 89.9999999999, -89.9999999999, 90.0, -90.0):
        try:
            h = H("default", angle=ang, speed=0.5)
            info = dict(h.sim.info)
            te = h.sim.track.next_event_after(0.0, {"horizon", "escape"})
            h.run_to(1.01 * te * h.sim.T_s if te else 3 * scale(h))
            out[ang] = {"kind": info["kind"], "v_phi": h.sim.init["v_phi"], **summary(h)}
        except Exception:
            out[ang] = {"exception": traceback.format_exc()[-600:]}
    return out


def s_newton_radial_and_eccentric():
    out = {}
    for ang, sp in ((0.0, 0.0), (-89.9, 1.0), (-89.0, 1.0), (-80.0, 1.0)):
        h = H("newton_ellipse", angle=ang, speed=sp, ghost=False)
        info = dict(h.sim.info)
        h.run_to(3.2 * scale(h))
        out[(ang, sp)] = {"kind": info["kind"], "r_peri": info["r_peri"], **summary(h)}
    return out


def s_bound_beyond_r_far():
    out = {}
    for law, k in (("GR", 1.3416), ("newton", 1.4141)):
        h = H("default", gravity=law, speed=k)
        info = dict(h.sim.info)
        te = h.sim.track.next_event_after(0.0, {"escape", "apo"})
        h.run_to(1.001 * te * h.sim.T_s if te else 5 * scale(h))
        out[law] = {"kind": info["kind"], "kind_text": info["kind_text"], "r_apo": info["r_apo"], **summary(h)}
    return out


def s_next_event_everywhere():
    out = {}
    for preset in ("default", "mercury", "bh_isco", "plunge", "radial", "newton_ellipse", "neutron_star"):
        h = H(preset)
        kinds = []
        for _ in range(6):
            h.cmd("next_event")
            kinds.append(round(h.sim.t / h.sim.T_s, 3))
        out[preset] = {"t_M": kinds, **summary(h)}
    return out


def s_neutron_star_grazing():
    out = {}
    for r0, sp in ((5.81, 1.0), (5.9, 1.05), (5.9, 0.99)):
        h = H("neutron_star", r0=r0, speed=sp)
        info = dict(h.sim.info)
        h.run_to(10 * h.sim.track.dyn * h.sim.T_s)
        out[(r0, sp)] = {"kind": info["kind"], **summary(h)}
    return out


SCEN = {k[2:]: v for k, v in globals().items() if k.startswith("s_")}


def child(name, q):
    try:
        t0 = time.time()
        r = SCEN[name]()
        q.put(("ok", r, time.time() - t0))
    except Exception:
        q.put(("exception", traceback.format_exc()[-2000:], None))


def _empty(v):
    try:
        return v is None or (isinstance(v, (list, str, tuple, dict)) and len(v) == 0)
    except Exception:
        return False


def show(name, status, res, wall):
    print(f"\n### {name}: {status}" + (f" (wall {wall:.1f} s)" if wall else ""))
    if isinstance(res, dict):
        for k, v in res.items():
            if isinstance(v, dict) and ("errors" in v or "exception" in v):
                print(f"  [{k}]")
                for kk, vv in v.items():
                    if not _empty(vv):
                        print(f"     {kk}: {vv}")
            elif not _empty(v):
                print(f"  {k}: {v}")
    else:
        print(res)


if __name__ == "__main__":
    names = sys.argv[1:] or list(SCEN)
    for name in names:
        q = mpr.Queue()
        p = mpr.Process(target=child, args=(name, q))
        p.start()
        p.join(BOX)
        if p.is_alive():
            p.kill()
            p.join()
            show(name, f"TIMEOUT > {BOX:.0f} s (killed)", None, None)
            continue
        try:
            status, res, wall = q.get(timeout=5)
        except Exception:
            status, res, wall = "no result (child died)", None, None
        show(name, status, res, wall)
        sys.stdout.flush()
