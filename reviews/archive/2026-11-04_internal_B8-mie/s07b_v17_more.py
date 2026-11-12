# Review B8-mie, script s07b: (1) the supernumerary preset's sky_sum per wavelength (the README quotes 0.11; s07 gets
# 0.31) and the actual error of the size sum at the worst wavelength against a 25x finer sum; (2) the near and
# absorbing presets; (3) the cost of big_drops (its label: "тяжёлый расчёт, ~минута").
import sys, time
import numpy as np
for p in ("/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf/visualizations/tests"):
    sys.path.insert(0, p)
from harness import Harness  # noqa: E402
from v17_mie_scattering.viz import SKY_TH, SKY_DEG, T_LAM, MAX_NODES  # noqa: E402
from v17_mie_scattering.engine import drops as DR  # noqa: E402
from lfphys.core.optics import mie_poly as MP  # noqa: E402

h = Harness("v17_mie_scattering", "supernumerary", {"n_lam": 16})
h.run_to(16 * T_LAM + 0.01)
sm = [m for m, b in h.msgs if m.get("type") == "sky"]
print("supernumerary: rel_err per wavelength:", [(round(m["lam_nm"]), round(m["rel_err"], 3)) for m in sm])
k = int(np.argmax([m["rel_err"] for m in sm]))
lam = sm[k]["lam_nm"]
mm = DR.index(h.params, lam)
nd = MP.size_nodes(100.0, 0.005, lam * 1e-3, 1.0, max_nodes=MAX_NODES)
av = MP.average(mm, lam * 1e-3, nd, SKY_TH)
fine = MP.average(mm, lam * 1e-3, MP.size_nodes(100.0, 0.005, lam * 1e-3, 1.0, dx_max=0.01, max_nodes=10 ** 6), SKY_TH)
top = fine["dsdo"].max()
e = np.abs(av["dsdo"] - fine["dsdo"])
j = int(np.argmax(av["err"]))
print(f"  worst wavelength {lam:.1f} nm: nodes {len(nd['r'])}, dx {nd['dx']:.3f}; estimate max err/max {av['err'].max() / av['dsdo'].max():.3f} "
      f"(at {SKY_DEG[j]:.1f} deg); actual max |error|/max {e.max() / top:.2e} (at {SKY_DEG[int(np.argmax(e))]:.1f} deg)")

for preset in ("near", "absorbing"):
    t0 = time.time()
    h = Harness("v17_mie_scattering", preset)
    h.run_to(h.sim.sky_n * T_LAM + 0.01)
    print(f"\n{preset}: {time.time() - t0:.1f} s, errors {h.errors()}")
    mono = h.of("mono")[-1]
    print(f"  x = {mono['x']:.2f}, m = {mono['m']}, Q = {mono['Q']}")
    for cid, c in sorted(h.checks().items()):
        print(f"  check {cid}: value {c.get('value')} ref {c.get('ref')} tol {c.get('tol')} ok {c.get('ok')} info {c.get('info', False)}")

t0 = time.time()
h = Harness("v17_mie_scattering", "big_drops")
tb = time.time() - t0
ts = []
for kk in range(1, 4):
    t1 = time.time()
    h.run_to(kk * T_LAM + 1e-9)
    ts.append(time.time() - t1)
sm = [m for m, b in h.msgs if m.get("type") == "sky"]
print(f"\nbig_drops: build {tb:.1f} s; first three wavelengths {[round(t, 1) for t in ts]} s "
      f"({[round(m['lam_nm']) for m in sm]} nm, nodes {[m['n_nodes'] for m in sm]}, dx {[round(m['dx'], 2) for m in sm]}, "
      f"coarse {[m['coarse'] for m in sm]}); {h.sim.sky_n} wavelengths in all")
