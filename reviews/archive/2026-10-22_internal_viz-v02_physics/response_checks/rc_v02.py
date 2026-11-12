"""Response checks (written by the processing session, not by the reviewer): the reviewer's key probes re-done
against the reworked v02 API. Run from the light-funnel root:
  docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server \
    light-funnel-viz python3 /lf/reviews/archive/2026-10-22_internal_viz-v02_physics/response_checks/rc_v02.py
"""
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")  # root path: the light-funnel tree mounted at /lf
from harness import Harness  # noqa: E402

V = "v02_double_slit"


def coh_of(sim, counts):
    return sim._coherence(counts.astype(float), bins=True)


print("== R2: histogram |gamma| on multinomial samples of the run's expectation (200 samples each)")
for preset, true in (("electron_weak", math.cos(math.radians(30))), ("photon_young", 1.0), ("electron_qubit", 0.0)):
    h = Harness(V, preset)
    sim = h.sim
    P = sim.theory["curves"]["all"]
    rng = np.random.default_rng(0)
    for N in (100, 1000, 5000, 20000):
        vals, fails, errs = [], 0, []
        for _ in range(200):
            g, e = coh_of(sim, rng.multinomial(N, P / P.sum()))
            if g is None:
                fails += 1
            else:
                vals.append(g)
                errs.append(e)
        vals = np.array(vals)
        print(f"  {preset:14s} true {true:.4f} N={N:6d}: fails {fails:3d}/200, mean {vals.mean():.4f}, "
              f"std {vals.std():.4f}, median err {np.median(errs):.4f}, >1: {np.mean(vals > 1) * 100:.0f} %")

print("== R3: map contrast near the centre of the last column vs the run's expected |gamma|")
for preset in ("electron_microscope", "c60_grw", "photon_partial"):
    h = Harness(V, preset)
    blobs = [b for m, b in h.msgs if m.get("type") == "segment"][0]
    I = blobs["map"].reshape(len(blobs["map_z"]), -1)
    lam, L2, d = h.sim.particle.lam, h.sim.geom.L2, h.sim.geom.d
    xi = np.linspace(-1, 1, I.shape[1]) * blobs["map_w"][-1]
    m = np.abs(xi) < 1.0 * lam * L2 / d
    last = I[-1][m]
    print(f"  {preset:20s} map contrast {(last.max() - last.min()) / (last.max() + last.min()):.3f}, "
          f"expected |gamma| {h.sim.gamma_expected:.3f}")

print("== R4: analyzer inserted while particles fly (neutron, spin filter along x, up_z source)")
h = Harness(V, None, {"species": "neutron", "lam_nm": 2.0, "a_um": 5.0, "d_um": 25.0, "L2_m": 5.0, "rate": 20000.0,
                      "spin_state": "up_z"})
tf = h.sim.t_flight
h.run_to(3 * tf)
n0 = h.sim.counts["detected"]
h.action("apparatus", analyzer="on", analyzer_angle=90.0)
h.run_to(4 * tf)
n1 = h.sim.counts["detected"] - n0
h.run_to(6 * tf)
n2 = h.sim.counts["detected"] - n0 - n1
print(f"  detections per flight: in the flight window {n1 / tf:.0f}/s, next two flights {n2 / (2 * tf):.0f}/s "
      f"(source 20000/s; the filter passes 1/2)")

print("== R7: no-signalling check under p = 2.4 (electron eraser)")
h = Harness(V, "electron_eraser", params={"born_p": 2.4})
c = [c for c in h.checks().values() if c["id"].startswith("nosig")][0]
print(f"  value {c['value']:.4f}, ok = {c['ok']}")

print("== R8: dark counts 50/s and 500/s (photon_young, 30 s)")
for dr in (50.0, 500.0):
    h = Harness(V, None, {"dark_rate": dr}, seed=4)
    h.run_to(30.0)
    fr, _ = h.sim.frame()
    print(f"  dark {dr:5.0f}/s: chi2 {fr['chi2']['x2']:.1f}/{fr['chi2']['dof']} p = {fr['chi2']['p']:.3g}; "
          f"histogram |gamma| {fr['coh']['hist']} +- {fr['coh']['err']}")

print("== R10: 'no scattered photon' class (microscope p = 0.5)")
h = Harness(V, "electron_microscope", params={"mic_prob": 0.5})
sim = h.sim
cn = sim.theory["curves"]["noscat"]
ca = sim.theory["curves"]["all"]
print(f"  |gamma| of the noscat curve {coh_of(sim, cn * 1e6)[0]:.4f}; of the whole ensemble {coh_of(sim, ca * 1e6)[0]:.4f}")

print("== R12: seed dependence of the expected |gamma| (exact ensemble: none expected)")
for preset in ("electron_microscope", "photon_partial", "c60_grw"):
    vals = [Harness(V, preset, seed=s).sim.gamma_expected for s in range(4)]
    print(f"  {preset:20s} {[round(v, 12) for v in vals]}")

print("== R16: segment time for 12 slits")
for params in ({"species": "electron", "energy_by": "ekin", "ekin_ev": 5e4, "n_slits": 12, "a_um": 0.1, "d_um": 10.0,
                "L2_m": 1.0, "wp_mode": "microscope", "mic_lambda_nm": 1000.0},
               {"n_slits": 12, "L1_m": 0.5, "src_width_um": 2000.0}):
    t0 = time.time()
    h = Harness(V, None, params)
    t1 = time.time()
    h.run_to(500 / h.of("header")[0]["rate"])
    t2 = time.time()
    print(f"  {params.get('species', 'photon')}: first segment {t1 - t0:.1f} s, 500 particles {t2 - t1:.1f} s, "
          f"points per fringe {h.sim.pts_per_fringe:.1f}, grid check ok = {h.checks()['grid']['ok']}")

print("== R6: Aharonov-Bohm phase vs q Phi / hbar (the probe of 04_particles_ab_probe.py section 3, current API)")
for q, flux in ((2.0, 0.25), (-3.0, 1.0 / 6.0), (0.5, 1.0), (1.0, 0.5), (-1.0, 0.5)):
    h = Harness(V, None, {"species": "custom", "mass_u": 1.0, "charge_e": q, "lam_nm": 0.1,
                          "ab_flux": flux})
    ph = h.sim.exp.ab_phases(h.sim.app)[1]
    ref = 2 * math.pi * q * flux
    d = (ph - ref + math.pi) % (2 * math.pi) - math.pi
    print(f"  q = {q:+.1f} e, flux = {flux:.4f} h/e: engine {ph:+.6f}, q Phi/hbar {ref:+.6f}, difference mod 2pi {d:+.1e}")
