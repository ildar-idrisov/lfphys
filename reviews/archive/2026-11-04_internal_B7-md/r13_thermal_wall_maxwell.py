"""Thermal (diffuse) wall: the re-emitted velocities themselves, recorded by wrapping the engine's own event methods
at run time (no engine file changed). Law (Maxwell's diffuse wall, full accommodation): the normal speed has the
flux-weighted density ~ v exp(-m v^2 / 2T_w), CDF 1 - exp(-m v^2 / 2T_w); each tangential component N(0, T_w/m).
Emitted samples are fresh random draws, so independent: KS with the DKW bound (alpha = 0.01) is valid.
Negative control: the normal speed against the half-Gaussian (a non-flux-weighted emission) is rejected.
Both engines: core.md.system.MD (2-D and 3-D) and core.md.hard.HardSpheres (2-D)."""
import common  # noqa: F401
import math

import numpy as np

from lfphys.core.md import observables as ob
from lfphys.core.md.hard import HardSpheres
from lfphys.core.md.system import MD
from scipy import special

Tw, m = 1.7, 2.0
sd = math.sqrt(Tw / m)


def report(tag, vn, vt):
    vn, vt = np.asarray(vn), np.asarray(vt).reshape(-1)
    r = ob.ks_cdf(vn, lambda s: 1 - np.exp(-s * s / (2 * sd * sd)))
    neg = ob.ks_cdf(vn, lambda s: special.erf(s / (math.sqrt(2) * sd)))
    rt = ob.ks_gaussian(vt, sd)
    print(f"{tag}: {len(vn)} emissions; normal speed vs flux-weighted: D = {r['D']:.4f} (bound {r['bound']:.4f}) "
          f"within {r['within']}; vs half-Gaussian: D = {neg['D']:.4f} within {neg['within']}; tangential "
          f"({len(vt)}): D = {rt['D']:.4f} (bound {rt['bound']:.4f}) within {rt['within']}; mean emitted energy "
          f"{0.5 * m * (np.mean(vn ** 2) + np.mean(vt ** 2) * (len(vt) / len(vn))) / Tw:.4f} T_w")


for dim in (2, 3):
    rec_n, rec_t = [], []
    orig = MD._wall_event

    def wrapped(self, key, r, s, _orig=orig, _n=rec_n, _t=rec_t):
        _orig(self, key, r, s)
        if self._walls[key]["kind"] == "thermal":
            a = "xyz".index(key[0])
            _n.extend(np.abs(self._v[r, a]).tolist())
            _t.extend(np.delete(self._v[r], a, axis=1).reshape(-1).tolist())
    MD._wall_event = wrapped
    md = MD(dim=dim, box=[8.0] * dim, boundary="walls", pair=None, dt=0.05, seed=31 + dim)
    md.add_species("A", mass=m)
    md.fill("A", n=1500, T=0.5)
    md.set_wall("x", "lo", "thermal", T=Tw)
    md.set_wall("y", "hi", "thermal", T=Tw)
    md.step(3000)
    MD._wall_event = orig
    report(f"MD {dim}-D", rec_n, rec_t)

rec_n, rec_t = [], []
orig = HardSpheres._process


def wrapped_h(self, ev, _orig=orig):
    t, _, kind, i, j, ci, cj = ev
    ok = _orig(self, ev)
    if ok and kind == 2:
        a, side = j // 2, ("hi" if j % 2 else "lo")
        if self._walls[f"{'xyz'[a]}-{side}"]["kind"] == "thermal":
            rec_n.append(abs(self._v[i, a]))
            rec_t.extend(np.delete(self._v[i], a).tolist())
    return ok


HardSpheres._process = wrapped_h
hs = HardSpheres(2, (20.0, 20.0), boundary="walls", seed=35)
hs.add_species("a", mass=m, sigma=0.3)
hs.fill("a", n=300, T=0.5)
hs.set_wall("x", "lo", "thermal", T=Tw)
hs.advance(600.0)
HardSpheres._process = orig
report("hard 2-D", rec_n, rec_t)
