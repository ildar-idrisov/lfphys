# Review B8-fdtd, script s13: reproducibility.
# (1) state round trips in situations the tests do not build: a ramped continuous plane wave, a Bloch slab wave, a
#     plane wave added mid-run, PEC/PMC walls with a Lorentz body and a hard source, 3-D with an oblique plane wave,
#     edits made before saving; the continuation must be bit-identical (fields, psi, polarizations, monitors);
# (2) with --gpu: the same worlds on GPU 0 against the CPU (real fields bit for bit, complex to round-off).
import argparse
import math

import numpy as np

from lfphys.core import backend
from lfphys.core.em import fdtd as F

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--gpu", action="store_true")
args = ap.parse_args()


def worlds(device="cpu"):
    out = {}
    w = F.FDTD((3.0, 2.0), 0.05, pol="tm", pml=8, device=device)
    w.add_source(F.PlaneWave(F.ContinuousWave(0.8, ramp=3.0), ((0.6, 0.5), (2.4, 1.5)), direction=0.5))
    w.add_body(F.Cylinder((1.5, 1.0), 0.3), F.Medium(eps=2.0, sigma=0.3))
    w.add_flux(((0.4, 0.3), (2.6, 1.7)), freqs=[0.8])
    out["cw plane wave + conductor"] = w
    w = F.FDTD((3.0, 0.5), 0.05, pol="te", boundary={"x": "pml", "y": "periodic"}, bloch=(0.0, 2 * math.pi * 0.3),
               device=device)
    w.add_source(F.PlaneWave(F.ModulatedGaussian(1.2, fwidth=0.15), ((1.0, -math.inf), (2.0, math.inf))))
    w.add_body(F.Box((1.3, -1.0), (1.6, 1.0)), F.Medium(poles=[F.Drude(1.5, 0.2)]))
    w.add_flux(((0.5, 0.0), (0.5, 0.5)), freqs=[1.0, 1.2], direction=-1)
    out["Bloch slab TE + Drude"] = w
    w = F.FDTD((2.0, 1.5), 0.05, pol="both", boundary={"x": ("pec", "pmc"), "y": ("pmc", "pml")}, pml=6,
               device=device)
    w.add_body(F.Box((0.5, 0.4), (0.9, 0.8)), F.Medium(eps=1.5, poles=[F.Lorentz(1.0, 0.9, 0.05)]))
    w.add_source(F.CurrentSource("ez", F.GaussianPulse(0.2), position=(1.3, 0.7), hard=True))
    w.add_source(F.CurrentSource("hz", F.ModulatedGaussian(1.0, fwidth=0.3), position=(1.2, 0.6)))
    w.add_probe((1.1, 0.9))
    out["PEC/PMC/PML both pols + Lorentz + hard source"] = w
    w = F.FDTD((1.2, 1.2, 1.2), 0.08, pml=6, device=device)
    w.add_source(F.PlaneWave(F.ModulatedGaussian(0.8, fwidth=0.3), ((0.3,) * 3, (0.9,) * 3), direction=(1.0, 0.5, 2.0),
                             polarization=(0.5, -1.0, 0.0)))
    w.add_body(F.Sphere((0.6, 0.6, 0.6), 0.2), F.Medium(eps=2.25))
    w.add_near2far(((0.2,) * 3, (1.0,) * 3), [0.8])
    out["3-D oblique plane wave + sphere"] = w
    return out


def edits(name, w):
    if name == "cw plane wave + conductor":
        w.advance(40)
        w.add_body(F.Box((0.8, 0.8), (1.0, 1.2)), F.Medium(poles=[F.Debye(2.0, 0.2)]))
        w.add_source(F.PlaneWave(F.ModulatedGaussian(1.0, fwidth=0.3, t0=w.t + 2.0), ((0.6, 0.5), (2.4, 1.5)),
                                 direction=-0.3))
        w.add_dft(((1.0, 0.8), (2.0, 1.2)), [0.8, 1.0])
    w.advance(90)


def same(a, b):
    bad = []
    for c in a.comps:
        if not np.array_equal(backend.to_numpy(a.F[c]), backend.to_numpy(b.F[c])):
            bad.append(c)
    for k in a.psi:
        if not np.array_equal(backend.to_numpy(a.psi[k]), backend.to_numpy(b.psi[k])):
            bad.append(f"psi{k}")
    for c in a.disp:
        for key in ("P", "Pm", "PD"):
            if not np.array_equal(backend.to_numpy(a.disp[c][key]), backend.to_numpy(b.disp[c][key])):
                bad.append(f"disp {c} {key}")
    return bad


def maxdiff(a, b):
    return max(float(np.max(np.abs(backend.to_numpy(a.F[c]) - backend.to_numpy(b.F[c])))) /
               max(1e-300, float(np.max(np.abs(backend.to_numpy(a.F[c]))))) for c in a.comps)


print("== (1) state round trips ==")
for name, w in worlds().items():
    edits(name, w)
    d = w.state_dict()
    b = F.FDTD.from_state_dict(d, device="cpu")
    w.advance(150)
    b.advance(150)
    bad = same(w, b)
    mons = []
    for mid, m in w._monitors.items():
        if m["kind"] == "flux":
            mons.append(np.array_equal(w.flux(mid)["spectrum"], b.flux(mid)["spectrum"]))
        elif m["kind"] == "near2far":
            mons.append(np.array_equal(w.far_field(mid, (np.array([0.5]), np.array([0.2])))["E_theta"],
                                       b.far_field(mid, (np.array([0.5]), np.array([0.2])))["E_theta"]))
        elif m["kind"] == "probe":
            pa, pb = w.probe(mid), b.probe(mid)
            mons.append(all(np.array_equal(pa[k], pb[k]) for k in pa))
        elif m["kind"] == "dft":
            da, db = w.dft(mid), b.dft(mid)
            mons.append(all(np.array_equal(da[c], db[c]) for c in w.comps))
    print(f"  {name}: differing arrays after 150 more steps: {bad or 'none'}; monitors identical: {mons}")

if args.gpu:
    print("== (2) GPU 0 against the CPU ==")
    backend.configure({"kernels": {F.KERNEL: {"device": "gpu"}}})
    try:
        wc, wg = worlds("cpu"), worlds("auto")
        for name in wc:
            a, g = wc[name], wg[name]
            edits(name, a)
            edits(name, g)
            a.advance(150)
            g.advance(150)
            bad = same(a, g)
            print(f"  {name}: devices {a.device}/{g.device}; complex {a.complex}; differing arrays: {bad or 'none'}; "
                  f"largest relative difference {maxdiff(a, g):.2e}")
    finally:
        backend.configure({})
