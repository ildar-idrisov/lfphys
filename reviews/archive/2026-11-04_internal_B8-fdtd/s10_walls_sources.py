# Review B8-fdtd, script s10: where the walls lie, and the hard sources.
# (1) the interior length of an axis for every pair of side kinds (the user asks for L = 0.6, dx = 0.05);
#     a PEC/PMC waveguide's cut-off frequency against the requested L and the realised one;
# (2) a hard H source is set after the E update (fdtd.py:1640, 1895-1901): the E update never sees it.
#     1-D at the magic time step (c dt = dx), where a hard source of f(t) radiates exactly f(t - |x - x0|/c) to both
#     sides: hard Ez in TM against its dual, hard Hz in TE.
import argparse
import math

import numpy as np

from lfphys.core.em import fdtd as F

argparse.ArgumentParser(description=__doc__).parse_args()

print("== (1) interior length for each pair of side kinds (size 0.6, dx 0.05) ==")
for lo, hi in (("pec", "pec"), ("pmc", "pmc"), ("pec", "pmc"), ("pmc", "pec"), ("pml", "pmc"), ("pmc", "pml"),
               ("pml", "pec"), ("pml", "pml")):
    w = F.FDTD((1.0, 0.6), 0.05, pol="tm", boundary={"x": "pec", "y": (lo, hi)}, pml=4)
    # where are the walls (coordinates)? lo wall: E_t index 0 (pec/pml) or H_t index 0 (pmc); hi: via the wrap.
    y_lo = w.coord(0 + (0.5 if lo == "pmc" else 0.0), 1)
    y_hi = w.coord(w.shape[1] - (0.5 if hi == "pmc" else 0.0), 1)
    print(f"  y: ({lo:3s}, {hi:3s}) shape {w.shape[1]:3d}  reported interior {w.interior[1]:.4f}  "
          f"outer walls at y = {y_lo:+.4f} ... {y_hi:+.4f}")

# the lowest TM mode of a PEC(x)/PEC-PMC(y) box: requested Ly = 0.6 -> k_y = pi / (2 Ly)
dx = 0.05
w = F.FDTD((1.0, 0.6), dx, pol="tm", boundary={"x": "pec", "y": ("pec", "pmc")}, courant=0.6)
w.add_source(F.CurrentSource("ez", F.ModulatedGaussian(0.6, fwidth=0.4), position=(0.37, 0.23)))
pid = w.add_probe((0.71, 0.41), ["ez"])
w.advance(6000)
x = w.probe(pid)["ez"][400:]
spec = np.abs(np.fft.rfft(x * np.hanning(len(x)), 1 << 18))
fr = np.fft.rfftfreq(1 << 18, w.dt)
band = (fr > 0.4) & (fr < 0.9)
f_peak = fr[band][np.argmax(spec[band])]
for Ly, lab in ((0.6, "requested 0.6"), (w.interior[1], f"realised {w.interior[1]:.3f}")):
    k = np.array([math.pi / 1.0, math.pi / (2 * Ly)])
    print(f"  mode (1, 0): FFT peak {f_peak:.4f}; grid frequency with Ly {lab}: "
          f"{F.yee_frequency(k, dx, w.dt) / (2 * math.pi):.4f}")

print("== (2) hard sources, 1-D, magic time step: radiated waveform 1 m from the source ==")


def hard_run(pol):
    dx = 0.02
    w = F.FDTD((6.0, dx), dx, pol=pol, boundary={"x": "pml", "y": "periodic"}, courant=1.0, pml=20)
    prof = F.GaussianPulse(0.2, t0=1.2)
    comp = "ez" if pol == "tm" else "hz"
    x0 = 2.0 if pol == "tm" else 2.0 + dx / 2
    y0 = 0.0 if pol == "tm" else dx / 2
    w.add_source(F.CurrentSource(comp, prof, position=(x0, y0), hard=True))
    pid = w.add_probe((x0 + 1.0, y0), [comp])
    w.advance(int(4.0 / w.dt))
    p = w.probe(pid)
    t = p["t"] - (0.5 * w.dt if comp[0] == "h" else 0.0)
    exact = prof(t - 1.0)
    return np.max(np.abs(p[comp] - exact)), np.max(np.abs(p[comp])), comp


for pol in ("tm", "te"):
    err, amp, comp = hard_run(pol)
    print(f"  hard {comp}: max |probe - f(t - 1)| = {err:.3e} (peak {amp:.4f}; exact 1.0)")
