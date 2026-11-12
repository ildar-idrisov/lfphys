# Review B8-fdtd, script s11: the dispersion relation and the CPML, reproduced independently.
# (1) a plane wave on a periodic 2-D grid (wavevector commensurate with the box) oscillates at the grid's omega(k):
#     measured by the phase advance of the complex amplitude from a DFT, independently of the tests' recurrence fit;
#     yee_wavenumber inverts yee_frequency; 3-D;
# (2) CPML: the tests' set-up (source 3 cells from the layer, five probes up to ~70 deg) and probes at grazing
#     incidence along a long boundary (80-87 deg), and late times (the low-frequency tail), against a big reference.
import argparse
import math

import numpy as np

from lfphys.core.em import fdtd as F

argparse.ArgumentParser(description=__doc__).parse_args()

print("== (1) dispersion ==")
for N, S in ((16, 0.5), (32, 0.7)):
    for m, n in ((1, 0), (2, 1), (3, 3), (5, 2)):
        w = F.FDTD((1.0, 1.0), 1.0 / N, pol="tm", boundary="periodic", courant=S)
        k = 2 * math.pi * np.array([m, n], float)
        w.set_field("ez", lambda x, y: np.cos(k[0] * x + k[1] * y))
        # the matching H of a travelling wave would be needed for a single direction; a standing pattern suffices:
        pid = w.add_probe((0.13, 0.41), ["ez"])
        w.advance(2000)
        x = w.probe(pid)["ez"]
        # fit x_n = A cos(omega t_n + phi) by a fine DFT peak + parabolic refinement
        nfft = 1 << 22
        X = np.abs(np.fft.rfft(x * np.hanning(len(x)), nfft))
        i = int(np.argmax(X[1:])) + 1
        a, b, c = np.log(X[i - 1:i + 2])
        di = 0.5 * (a - c) / (a - 2 * b + c)
        om = 2 * math.pi * (i + di) / (nfft * w.dt)
        oy = F.yee_frequency(k, w.dx, w.dt)
        print(f"  N={N} S={S} k=2pi({m},{n}): omega_meas/omega_yee - 1 = {om / oy - 1:+.2e}; "
              f"omega_c/omega_yee - 1 = {np.linalg.norm(k) / oy - 1:+.2e}")
# inverse
rng = np.random.default_rng(2)
worst = 0.0
for _ in range(200):
    d = rng.standard_normal(3)
    d /= np.linalg.norm(d)
    dx = 0.05
    dt = 0.5 * dx
    kk = rng.uniform(0.1, 0.9) * math.pi / dx / np.max(np.abs(d))
    om = F.yee_frequency(kk * d, dx, dt)
    k2 = F.yee_wavenumber(om, d, dx, dt)
    worst = max(worst, abs(k2 / kk - 1))
print(f"  yee_wavenumber(yee_frequency(k)) / k - 1: worst {worst:.2e} over 200 random 3-D directions")

print("== (2) CPML reflection ==")
DX = 0.05
PROF = F.ModulatedGaussian(1.0, fwidth=0.5)


def run(L, src, pml, offs, steps, Ly=None):
    w = F.FDTD((L, Ly if Ly else L), DX, pol="tm", pml=pml)
    w.add_source(F.CurrentSource("ez", PROF, position=src))
    ids = [w.add_probe((src[0] + a, src[1] + b), ["ez"]) for a, b in offs]
    w.advance(steps)
    return np.array([w.probe(i)["ez"] for i in ids])


# tests' geometry
OFFS = [(0.0, -0.1), (0.0, 0.25), (0.5, -0.1), (0.9, -0.1), (0.9, 0.5)]
ref = run(14.0, (7.0, 7.0), 10, OFFS, 440)
for spec in (F.PML(10, 3), F.PML(10, 3, kappa_max=5, alpha_max=0.2)):
    t = run(2.0, (1.0, 0.15), spec, OFFS, 440)
    db = 20 * np.log10(np.max(np.abs(t - ref), axis=1) / np.max(np.abs(ref), axis=1))
    print(f"  tests' geometry, {spec.params()}: dB {np.round(db, 1)}")
# grazing: a long strip, the source 3 cells above the lower layer, probes far along it (angles from the normal)
src = (2.5, 0.15)  # the side and top layers are too far to be reached within the window
far = [(2.0, 0.0), (4.0, 0.0), (6.0, 0.0), (6.0, 0.6)]
ang = [math.degrees(math.atan2(a, 2 * 0.15 + b)) for a, b in far]
steps = int(9.0 / (0.5 * DX))
ref = run(24.0, (12.0, 12.0), 10, far, steps)
for spec in (F.PML(10, 3), F.PML(20, 3), F.PML(10, 3, kappa_max=5, alpha_max=0.2)):
    t = run(11.0, src, spec, far, steps, Ly=4.0)
    db = 20 * np.log10(np.max(np.abs(t - ref), axis=1) / np.max(np.abs(ref), axis=1))
    print(f"  grazing (image-path angles {np.round(ang, 1)} deg), {spec.params()}: dB {np.round(db, 1)}")
