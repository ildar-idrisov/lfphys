"""Causality, "computed not drawn" and robustness probes of v01 through the test harness (no server).

Reviewer script (2026-10-22). Each probe prints PASS/FINDING with the numbers. Probes:
  A  B's clock reading shown before the Einstein synchronisation is complete
  B  GR arrivals at fast receivers (fixed-point iteration limit)
  C  GR local speed-of-light check against its own tolerance
  D  local light cone of an observer moving with v_y != 0 (flat SR)
  E  Doppler check after a boost in the middle of a pulse train
  F  emission theory: a passing-flash result revealed before B's reading can reach A
  G  boost exactly at an arrival time (duplicate arrival)
  H  GR: a boost that is timelike now but not later (inward coordinate velocity)
  I  Sun-Earth: rocket boosted into the Sun
  J  scenario texts with fixed numbers vs the run's computed values
  K  Andromeda: event in an observer's past (own slice) but in the lab future
  L  apparatus rebuild: instantaneous relocation of end B
  M  completed passing measurement withdrawn by a later boost
  N  GR: receiver inside the photon sphere (no connection returned)
  O  Newtonian corpuscles: target on the source-body line (radial)
  P  Sun-Earth under emission + newton
  Q  transport 'next event' with a pending event at the current time
  R  diagram position of reflection events
  S  lensing checks emitted before the beam reaches the hole

Run:
  docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server \
      light-funnel-viz python3 /lf/reviews/2026-10-22_internal_viz-v01_physics/check_causality.py
"""
from __future__ import annotations

import argparse
import math
import sys
import traceback

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")  # root path: the light-funnel tree mounted at /lf in the container
from harness import Harness  # noqa: E402

from v01_light_travel.engine import kepler, schwarzschild as S  # noqa: E402
from v01_light_travel.engine.consts import AU, C, DAY, GM_SUN, LIGHT_YEAR, R_SUN  # noqa: E402

V = "v01_light_travel"


def head(s):
    print("\n" + "=" * 100 + "\n" + s)


def obj(meta, oid):
    return next(o for o in meta["objects"] if o["id"] == oid)


def probe_A():
    head("A. B's clock reading before the Einstein synchronisation is complete (measure_c)")
    h = Harness(V, "measure_c")
    h.run_to(0.0005)
    meta, _ = h.sim.frame()
    for oid in ("obs1", "obs2", "obs3"):
        o = obj(meta, oid)
        ap = h.sim.world.objects[oid].apparatus
        print(f"  t = {h.sim.t:.4g} s, {oid}: synced = {o['synced']}, sync completes at t = {ap.t_sync_done:.6g} s, "
              f"tau_B sent to the view = {o['tau_b']!r}")
    o = obj(meta, "obs2")
    if not o["synced"] and o["tau_b"] is not None:
        print("  FINDING: the frame carries B's *synchronised* reading (offset fixed by the return event that lies "
              "in the future); view.js prints it as 'B τ=…' because it only tests tau_b === null.")


def probe_B():
    head("B. GR arrivals at moving receivers (lensing, observer boosted along +x = away from the source)")
    for beta in (0.3, 0.6, 0.75, 0.9):
        h = Harness(V, "lensing")
        h.action("boost", obj="obs", v=beta, unit="c", angle=0.0)
        h.action("flash", obj="src")
        w = h.sim.world
        pulse = w.pulses[-1]
        arr = w._arrivals(pulse, w.objects["obs"].wl, 0.0)
        # independent fixed point: brentq on t - t0 - dt(x(t)) per side
        from scipy.optimize import brentq
        wl = w.objects["obs"].wl
        o = np.asarray(pulse["origin"])
        ref = {}
        for side in (+1, -1):
            def F(t):
                ims = [m for m in S.connect(o, wl.pos(t), w.rs, w.laws.c, w.r_abs) if m["side"] == side]
                return t - ims[0]["dt"] if ims else math.nan
            lo, hi = 1e-9, 1.0
            try:
                ref[side] = brentq(F, lo, hi, xtol=1e-16, rtol=1e-14)
            except Exception as e:  # noqa: BLE001
                ref[side] = f"no root ({e})"
        got = {a["side"]: a["t"] for a in arr}
        print(f"  beta = {beta}: engine arrivals {got}; independent root {ref}")
        if len(arr) < len([v for v in ref.values() if isinstance(v, float)]):
            print("  FINDING: arrival(s) missing in the engine (fixed-point iteration did not converge in 60 steps; "
                  "the arrival is silently dropped)")


def probe_C():
    head("C. GR local measurement of c by a static observer: value vs reference and the check's tolerance")
    for preset, oid, horizon in (("lensing", "obs", 0.05), ("sun_earth", "station", 10.0)):
        h = Harness(V, preset)
        h.action("measure", obj=oid)
        h.run_to(horizon)
        for c in h.checks().values():
            if c["id"].startswith("loc_"):
                ok = abs(c["rel"]) <= max(c["tol"], 1e-12)
                print(f"  {preset}: c_loc = {c['value']:.12g}, ref = {c['ref']:.12g}, rel = {c['rel']:.3e}, "
                      f"tol = {c['tol']:.0e} -> {'shown ✓' if ok else 'shown ✗ (FAILED)'}")
                # exact expected value for a radial rod of proper length ell at r (closed form)
                w = h.sim.world
                r = float(np.linalg.norm(w.objects[oid].wl.pos(0.0)))
                rs = w.rs
                ell = 1e-3 * r
                from scipy import integrate, optimize
                rb = optimize.brentq(lambda x: integrate.quad(lambda y: 1 / math.sqrt(1 - rs / y), r, x,
                                                              epsrel=1e-14)[0] - ell, r, r + 2 * ell, xtol=1e-15 * r)
                ct = (rb - r) + rs * math.log((rb - rs) / (r - rs))
                c_exact = 2 * ell / (math.sqrt(1 - rs / r) * 2 * ct / w.laws.c)
                print(f"     closed form for this rod: 2 ell / (sqrt(f_A) * 2 [Δr + rs ln((r_B - rs)/(r_A - rs))]/c) = "
                      f"{c_exact:.12g}; engine vs closed form rel = {c['value'] / c_exact - 1:.2e}")


def probe_D():
    head("D. Local light cone on the diagram for an observer moving along y (flat SR)")
    h = Harness(V, "measure_c")
    h.action("boost", obj="obs1", v=0.8, unit="c", angle=90.0)
    meta, _ = h.sim.frame()
    cone = meta["cones"]["obs1"]
    print(f"  obs1 v = (0, 0.8c): cone 'fut' x-slopes = {[u / C for u in cone['fut']]} c, 'past' = "
          f"{[u / C for u in cone['past']]} c")
    if abs(abs(cone["fut"][0]) / C - 1) > 1e-9:
        print("  FINDING: the future cone drawn on the (x, t) diagram has slope ±0.6c; light moves at ±c along x in "
              "the lab (SR). The engine takes the rest-frame ±x rays, whose lab x-velocity is c/γ.")


def probe_E():
    head("E. Doppler check after a boost in the middle of a train (measure_c, SR)")
    h = Harness(V, "measure_c")
    h.action("train", obj="src", period=1e-3, count=8)
    h.run_to(0.0165)
    h.action("boost", obj="obs1", v=0.3, unit="c", angle=0.0)
    h.run_to(0.06)
    bad = []
    for c in h.checks().values():
        if c["group"] == "Доплер и красное смещение" and c["rel"] is not None and abs(c["rel"]) > c["tol"]:
            bad.append((c["label"], c["value"], c["ref"], c["rel"]))
    for c in h.of("check"):
        if c["group"] == "Доплер и красное смещение" and "Наблюдатель 1" in c["label"]:
            print(f"  t = {c['t']:.6f}: {c['label']}: value {c['value']:.9f}, ref {c['ref']:.9f}, rel {c['rel']:+.2e}")
    if bad:
        print(f"  FINDING: {len(bad)} Doppler check(s) shown failed although the physics is standard SR "
              "(pair of pulses straddles the boost)")


def probe_F():
    head("F. Emission theory: flash passes B first, then A; B's reading must travel to A as light")
    from v01_light_travel.engine.apparatus import Apparatus
    from v01_light_travel.engine.laws import Laws
    from v01_light_travel.engine.world import Obj, World
    from v01_light_travel.engine.worldlines import Piecewise
    laws = Laws("emission", "none")
    msgs = []
    L0, D = 3e5, 3e6
    w = World(laws, None, [0, 0], 4 * D, 36, lambda m, b=None: msgs.append(m))
    u = -0.5 * C
    w.add(Obj("src", "src", "beacon", "#000", Piecewise.start(laws, 0.0, 0.0, [D, 0.0], [u, 0.0]), receiver=False))
    wl = Piecewise.start(laws, 0.0, 0.0, [0.0, 0.0], [0.0, 0.0])
    o = Obj("obs", "obs", "observer", "#000", wl, movable=True)
    o.apparatus = Apparatus(laws, "obs", wl, L0, "x", "einstein")
    w.add(o)
    w.build_apparatus(o, 0.0)
    w.advance(0.003)
    w.flash("src", 0.003)
    w.advance(1.0)
    ev = [m for m in msgs if m.get("type") == "event" and m.get("kind") == "measure"]
    x_src = D + u * 0.003
    tb = 0.003 + (x_src - L0) / (C - u)       # light speed in the lab: -(c - u) = -1.5 c
    ta = 0.003 + x_src / (C - u)
    t_info = tb + L0 / C                       # B's reading, emitted by B (at rest) at c
    for e in ev:
        print(f"  measure event revealed at t = {e['t']:.9f} s; flash at B {tb:.9f}, at A {ta:.9f}; "
              f"B's reading can reach A at {t_info:.9f} s; measured {e['data']['speed'] / C:.6f} c")
        if e["t"] < t_info - 1e-12:
            print(f"  FINDING: result revealed {1e3 * (t_info - e['t']):.4f} ms before B's reading can arrive at A")


def probe_G():
    head("G. Boost exactly at an arrival time (does the arrival repeat?)")
    cases = [("measure_c", {}), ("measure_c_ether", {}), ("measure_c_emission", {}), ("lensing", {}),
             ("lensing_newton", {}), ("sun_earth", {})]
    for preset, extra in cases:
        oids = {"lensing": ("obs",), "lensing_newton": ("obs",), "sun_earth": ("station", "rocket")}.get(
            preset, ("obs1", "obs2", "obs3"))
        for oid0 in oids:
            for vb in (0.2, -0.3, 0.7):
                h = Harness(V, preset, extra or None)
                h.sim.advance(h.sim.t)  # as Runner.run() does: reveal the t = 0 events
                arr = []
                for _ in range(400):
                    te = h.sim.next_event_time()
                    if te is None:
                        break
                    h.run_to(te)
                    arr = [e for e in h.of("event") if e["kind"] == "arrival" and e.get("obj") == oid0]
                    if arr:
                        break
                if not arr:
                    print(f"  {preset}/{oid0}: no arrival found")
                    continue
                a0 = arr[0]
                if oid0 == "station":
                    continue  # not movable
                h.action("boost", obj=oid0, v=vb, unit="c", angle=90.0 if preset.startswith("lensing") else 0.0)
                h.run_to(h.sim.t * (1 + 1e-9) + 1e-12)
                arr2 = [e for e in h.of("event") if e["kind"] == "arrival" and e.get("obj") == oid0
                        and e.get("pulse") == a0["pulse"] and e.get("image") == a0["image"]]
                tag = "FINDING: duplicate" if len(arr2) > 1 else "once"
                print(f"  {preset:20s} {oid0} boost {vb:+.1f}c at its arrival t = {a0['t']:.12g}: arrival revealed "
                      f"{len(arr2)}x {[round(e['t'], 15) for e in arr2]} -> {tag}")


def probe_H():
    head("H. GR: observer boosted towards the black hole at 0.5c (coordinate velocity)")
    h = Harness(V, "lensing")
    h.action("boost", obj="obs", v=0.5, unit="c", angle=180.0)
    print(f"  boost accepted: errors so far {h.errors()}")
    rs = h.sim.world.rs
    last_ok = None
    try:
        for k in range(1, 400):
            h.run_to(k * 0.5 * rs / C)
            h.sim.frame()
            last_ok = np.linalg.norm(h.sim.world.objects["obs"].wl.pos(h.sim.t)) / rs
        print("  no exception")
    except Exception as e:  # noqa: BLE001
        x = h.sim.world.objects["obs"].wl.pos(h.sim.t)
        print(f"  last good frame at r = {last_ok:.3f} rs; exception at t = {h.sim.t:.6g} s (observer at "
              f"r = {np.linalg.norm(x) / rs:.3f} rs): {type(e).__name__}: {e}")
        print("  FINDING: the boost is validated only at the current event; the prescribed worldline turns "
              "spacelike (q = f - 0.25/f = 0 at r = 2 rs for 0.5c inward) and frame() raises")


def probe_I():
    head("I. Sun-Earth: rocket boosted towards the Sun at 0.5c")
    h = Harness(V, "sun_earth")
    h.action("boost", obj="rocket", v=0.5, unit="c", angle=180.0)
    w = h.sim.world
    inside = []
    try:
        for k in range(1, 600):
            h.run_to(float(k))
            meta, _ = h.sim.frame()
            r = np.linalg.norm(w.objects["rocket"].wl.pos(h.sim.t))
            if r < R_SUN:
                inside.append((h.sim.t, r / R_SUN, obj(meta, "rocket")["tau"]))
        print("  no exception")
    except Exception as e:  # noqa: BLE001
        x = w.objects["rocket"].wl.pos(h.sim.t)
        print(f"  exception at t = {h.sim.t} s, rocket at r = {np.linalg.norm(x) / R_SUN:.4f} R_sun: "
              f"{type(e).__name__}: {e}")
    for t, r, tau in inside[:3]:
        print(f"  t = {t:.0f} s: rocket at r = {r:.3f} R_sun (inside the Sun), frame OK, tau = {tau:.9g}")
    if inside:
        print("  FINDING: the rocket moves through the absorbing body with the exterior metric; the run fails "
              "when r drops below the radius where q = f - v^2/(c^2 f) <= 0")


def probe_J():
    head("J. Scenario texts with fixed numbers vs this run's numbers")
    h = Harness(V, None, {"scenario": "sun_earth", "se_distance_au": 5.0, "c_factor": 0.5})
    txt = h.of("header")[0]["text"]
    h.run_to(1e4)
    arr = [e for e in h.of("event") if e["kind"] == "arrival" and e["obj"] == "station"][0]
    print(f"  sun_earth, 5 au, c x 0.5: header text says '{txt[txt.index('примерно'):txt.index('примерно') + 22]}'; "
          f"the run computed {arr['data']['dt'] / 60:.2f} min")
    h = Harness(V, None, {"scenario": "andromeda", "gravity": "none", "an_dist_mly": 0.001, "an_walk": 0.5 * C})
    txt = h.of("header")[0]["text"]
    meta, _ = h.sim.frame()
    print(f"  andromeda, 1000 ly, ±0.5c: text says '...{txt[txt.index('различается'):txt.index('различается') + 22]}...', "
          f"'...{txt[txt.index('через'):txt.index('через') + 18]}...'; the run's 'now' offset at Andromeda = "
          f"{meta['now_at']['walk_to']['andromeda'] / DAY / 365.25:.1f} yr")
    h = Harness(V, None, {"scenario": "lensing", "gravity": "none"})
    txt = h.of("header")[0]["text"]
    print(f"  lensing with gravity 'none' (modified): text still says: '...{txt[-110:]}'")


def probe_K():
    head("K. Andromeda: event at lab t = +2 d; walk_to's 'now' at Andromeda at lab t = 0")
    h = Harness(V, None, {"scenario": "andromeda", "gravity": "none", "an_event_days": 2.0})
    h.run_to(0.0)
    meta, _ = h.sim.frame()
    na = meta["now_at"]["walk_to"]["andromeda"]
    emits = [e for e in h.of("event") if e["kind"] == "emit" and e.get("obj") == "andromeda"]
    print(f"  walk_to's 'now' at Andromeda = lab t {na / DAY:+.4f} d (event at +2 d is on his PAST side); "
          f"emit events known to the view: {len(emits)}")
    print("  FINDING: the observer-frame table/diagram cannot show the event that its own slice has passed, because "
          "only lab-revealed events reach the browser; worldlines on the slice are extrapolated into the lab future")


def probe_L():
    head("L. Apparatus rebuild after a boost: end B is relocated at the boost's lab time")
    h = Harness(V, "measure_c")
    h.run_to(0.005)
    ap = h.sim.world.objects["obs2"].apparatus
    t = h.sim.t
    xb_old = ap.wl_b.pos(t).copy()
    h.action("boost", obj="obs2", v=-0.8, unit="c", angle=0.0)
    xb_new = ap.wl_b.pos(t)
    xa = h.sim.world.objects["obs2"].wl.pos(t)
    print(f"  at lab t = {t}: A at x = {xa[0] / 1e3:.3f} km; B before {xb_old[0] / 1e3:.3f} km, after "
          f"{xb_new[0] / 1e3:.3f} km: jump {(xb_new[0] - xb_old[0]) / 1e3:+.3f} km in zero time, at distance "
          f"{(xb_old[0] - xa[0]) / 1e3:.1f} km from the boost event")


def probe_M():
    head("M. Passing measurement completed (both passages done) but withdrawn by a boost before the result arrives")
    h = Harness(V, "measure_c")
    w = h.sim.world
    h.run_to(0.0279)
    pend = [p for p in w.pending if not p.ev.get("cancelled") and p.ev["kind"] == "measure"
            and p.ev.get("obj") == "obs2"]
    for p in pend:
        d = p.ev["data"]
        print(f"  pending result for obs2 at t_known = {p.t:.6f} (now {h.sim.t}); B's passage already happened: "
              f"{'dtau' in d}")
    h.action("boost", obj="obs2", v=0.0, unit="c", angle=0.0)
    h.run_to(0.06)
    got = [e for e in h.of("event") if e["kind"] == "measure" and e.get("obj") == "obs2"]
    print(f"  measure events for obs2 after the run: {len(got)}")
    if pend and not got:
        print("  FINDING: the readings were taken before the boost, yet the result never reaches A")


def probe_N():
    head("N. GR: receiver inside the photon sphere")
    rs = 1.0
    for r2 in (1.6, 1.5000001, 1.4, 1.1):
        im = S.connect((60.0, 0.0), (r2, 0.0), rs, 1.0, rs)
        print(f"  radial connection 60 rs -> {r2} rs: {len(im)} image(s)"
              + ("" if im else "  <- light does reach it (radial ray, ct = Δr + rs ln(...))"))


def probe_O():
    head("O. Newtonian corpuscles: target on the line source-body (radial)")
    mu = 10 * GM_SUN
    rs = 2 * mu / C**2
    o = np.array([-100 * rs, 0.0])
    sp = math.sqrt(C**2 + 2 * mu / 100 / rs)
    for tgt in (np.array([-50 * rs, 0.0]), np.array([-50 * rs, 1e-6 * rs]), np.array([-50 * rs, 1e-3 * rs]),
                np.array([-200 * rs, 0.0]), np.array([-200 * rs, 1e-3 * rs])):
        try:
            res = kepler.connect_newton(o, tgt, sp, np.zeros(2), mu, 1.0 * rs)
            print(f"  source -100 rs, target {tgt / rs} rs: {len(res)} image(s), dt = {[r['dt'] for r in res]}")
        except Exception as e:  # noqa: BLE001
            print(f"  source -100 rs, target {tgt / rs} rs: {type(e).__name__}: {str(e)[:90]}")
    cr = kepler.crossings(o, np.array([sp, 0.0]), mu, 50 * rs, rs)
    print(f"  kepler.crossings for a radially inward corpuscle to r = 50 rs: {cr}  <- the corpuscle does cross r = 50 rs")


def probe_Q():
    head("Q. Transport: 'next event' when a pending event is at the current time")
    h = Harness(V, "measure_c")
    h.action("flash", obj="obs1")  # at t = 0 all three observers are at the flash point
    pend = sorted(p.t for p in h.sim.world.pending if not p.ev.get("cancelled") and p.ev["kind"] == "arrival")
    print(f"  pending arrivals after the flash at t = 0: first at t = {pend[:2]}")
    for _ in range(3):
        h.cmd("next_event")
    arr = [e for e in h.of("event") if e["kind"] == "arrival"]
    print(f"  after pressing 'next event' 3x: sim t = {h.sim.t}, arrivals revealed: {len(arr)}")
    if pend and pend[0] == 0.0 and not arr:
        print("  FINDING: Runner._advance(target) does nothing when target == sim.t, so the zero-delay arrival is "
              "never revealed by 'next event' (the button is stuck)")


def probe_R():
    head("R. Where the diagram puts the reflection events (view.js draws every event at wlPos(wls[e.obj], e.t))")
    h = Harness(V, "measure_c")
    h.run_to(0.003)
    w = h.sim.world
    for e in h.of("event"):
        if e["kind"] == "sync" and "отраж" in e["text"]:
            o = w.objects[e["obj"]]
            xa = o.wl.pos(e["t"])
            xb = o.apparatus.wl_b.pos(e["t"])
            print(f"  '{e['text']}' at t = {e['t']:.6g}: obj = {e['obj']} -> marker drawn at A x = {xa[0] / 1e3:.2f} km; "
                  f"the reflection happened at B x = {xb[0] / 1e3:.2f} km")


def probe_S():
    head("S. Lensing: checks about the beam's future (capture boundary, swept angles) are emitted at t = 0")
    h = Harness(V, "lensing")
    h.sim.advance(0.0)  # as Runner.run(): reveal the t = 0 events
    rs = h.sim.world.rs
    for c in h.of("check"):
        if c["id"] == "bc" or c["id"].startswith("swept_"):
            print(f"  check {c['id']!r} emitted at t = {c['t']}: value {c['value']}, note: {c['note'][:70]}")
    rays_end = []
    for m, b in h.msgs:
        if m.get("type") == "pulse" and m.get("kind") == "plane":
            T, st = b["T"], b["st"]
            off = b["off"]
            ends = [T[off[i + 1] - 1] for i in range(len(st)) if st[i] == 2]
            rays_end.append((min(ends), max(ends)))
    print(f"  the beam's captured rays reach the horizon at lab t in [{rays_end[0][0]:.3e}, {rays_end[0][1]:.3e}] s "
          f"(~{rays_end[0][0] * C / rs:.0f}-{rays_end[0][1] * C / rs:.0f} rs/c), i.e. after the check was shown")


def probe_P():
    head("P. Sun-Earth under the declared modification emission + newton (flare and Earth on the x axis)")
    try:
        h = Harness(V, None, {"scenario": "sun_earth", "kinematics": "emission", "gravity": "newton"})
        h.runner.handle({"cmd": "step", "args": {"dt": 0.0}})
        h.run_to(0.0)
        h.run_to(600.0)
        arr = [(e["obj"], round(e["t"], 6)) for e in h.of("event") if e["kind"] == "arrival"]
        print(f"  errors: {[x[:200] for x in h.errors()]}; arrivals: {arr}")
    except Exception as e:  # noqa: BLE001
        print(f"  {type(e).__name__}: {e}")
    print("  (kepler._radial calls quad(epsabs=0, epsrel=1e-14); scipy requires epsrel > 50*eps = 1.1e-14)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", default="", help="letters of the probes to run, e.g. ABG")
    a = ap.parse_args()
    probes = {k: v for k, v in globals().items() if k.startswith("probe_")}
    for name, fn in probes.items():
        if a.only and name[-1] not in a.only:
            continue
        try:
            fn()
        except Exception:  # noqa: BLE001
            print(f"  probe {name} raised:\n" + traceback.format_exc())


if __name__ == "__main__":
    main()
