# Review B8-fdtd, script s12: scattering, radiation and the near-to-far transform, reproduced.
# (1) sphere m = 1.5, a = 0.5 against core.optics.mie at 16 cells per unit (Q_sca, Q_abs, dsigma/dOmega) and the
#     same Q_sca re-normalised by the flux monitor's own measure of the incident wave (the face operator applied to
#     the grid's plane wave) -- does the claimed agreement rest on the monitor's bias?
# (2) point dipole power in 3-D (10 and 20 cells per wavelength);
# (3) the near-to-far transform's normalisation without any scatterer: a 3-D z-dipole's far field against
#     E_theta = (k^2 I l / (4 pi)) sin(theta) e^{ikr}/r (exp(-i w t), eta = 1, I l the current moment), and a 2-D
#     line current's E_z against -(omega I / 4) H_0^(1)(k rho) asymptotics;
# (4) the cylinder series: the TE Rayleigh limit (not tested), Q_abs > 0 for Im m > 0, and the convention against
#     mie (exp(-i omega t), m = n + i kappa) through a lossy cylinder's absorption against the FDTD's conductor.
import argparse
import math

import numpy as np

from lfphys.core.em import fdtd as F
from lfphys.core.optics import cylinder as cy
from lfphys.core.optics import mie

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--res", type=int, default=16)
args = ap.parse_args()

print("== (1) sphere vs Mie ==")
a = 0.5
fs = np.array([0.4, 0.6, 0.8])
res = args.res
w = F.FDTD((3.0, 3.0, 3.0), 1.0 / res, pml=10)
prof = F.ModulatedGaussian(0.6, fwidth=0.18)
w.add_source(F.PlaneWave(prof, ((0.7,) * 3, (2.3,) * 3), direction=(0, 0, 1), polarization=(1, 0, 0)))
w.add_body(F.Sphere((1.5, 1.5, 1.5), a), F.Medium(eps=2.25))
sca = w.add_flux(((0.5,) * 3, (2.5,) * 3), freqs=fs)
tot = w.add_flux(((0.85,) * 3, (2.15,) * 3), freqs=fs)
n2f = w.add_near2far(((0.45,) * 3, (2.55,) * 3), freqs=fs)
w.advance(int((prof.end() + 18) / w.dt))
cs = w.cross_sections(sca, tot)
Qs = cs["sigma_sca"] / (math.pi * a * a)
Qm = np.array([mie.efficiencies(1.5, 2 * np.pi * f * a)["Qsca"] for f in fs])
k = 2 * np.pi * fs
dxs = w.dx
# the face operator on the incident wave along z through a z-face: cos(k dx/2) (H averaged across the plane);
# the x- and y-faces see the transverse averages too; take the normal-incidence factor as the leading one
fac = np.cos(k * dxs / 2)
print(f"  Q_sca/Q_mie - 1 = {np.round(Qs / Qm - 1, 4)};  re-normalised by cos(k dx/2): "
      f"{np.round(Qs / fac / Qm - 1, 4)};  Q_abs = {np.round(cs['sigma_abs'] / (math.pi * a * a), 4)}")
th = np.array([0.3, 1.0, 1.6, 2.5])
ph = np.array([0.0, 0.7, 1.2, 0.3])
ff = w.far_field(n2f, (th, ph))
for i, f in enumerate(fs):
    kk = 2 * np.pi * f
    sc = mie.scattering(1.5, kk * a, th)
    ds = (np.abs(sc["S2"]) ** 2 * np.cos(ph) ** 2 + np.abs(sc["S1"]) ** 2 * np.sin(ph) ** 2) / kk ** 2
    print(f"  f = {f}: dsigma/dOmega / Mie - 1 = {np.round(ff['dsigma_domega'][i] / ds - 1, 4)}")

print("== (2) point dipole power, 3-D ==")
fs2 = np.array([0.8, 1.0, 1.2])
for r in (10, 20):
    dx = 1.0 / r
    prof = F.ModulatedGaussian(1.0, fwidth=0.3)
    w = F.FDTD((1.6, 1.6, 1.6), dx, pml=10)
    w.add_source(F.CurrentSource("ez", prof, position=(0.8, 0.8, 0.8)))
    fid = w.add_flux(((0.4, 0.4, 0.4), (1.2, 1.2, 1.2)), freqs=fs2)
    n = int((prof.end() + 4.0) / w.dt)
    w.advance(n)
    P = w.flux(fid)["spectrum"]
    th_ = (np.arange(n) + 0.5) * w.dt
    I = np.exp(2j * np.pi * np.outer(fs2, th_)) @ prof(th_) * w.dt
    Pex = (2 * np.pi * fs2) ** 2 * np.abs(I) ** 2 / (12 * np.pi)
    print(f"  {r} cells per unit (per wavelength at f = 1): P / (omega^2 |I l|^2 / 12 pi) - 1 = {np.round(P / Pex - 1, 4)}")

print("== (3) near-to-far normalisation without a scatterer ==")
fs3 = np.array([0.8, 1.0])
for r in (10, 20):
    dx = 1.0 / r
    prof = F.ModulatedGaussian(1.0, fwidth=0.3)
    w = F.FDTD((2.0, 2.0, 2.0), dx, pml=10)
    w.add_source(F.CurrentSource("ez", prof, position=(1.0, 1.0, 1.0)))
    nid = w.add_near2far(((0.4,) * 3, (1.6,) * 3), fs3)
    n = int((prof.end() + 5.0) / w.dt)
    w.advance(n)
    th_ = (np.arange(n) + 0.5) * w.dt
    I = np.exp(2j * np.pi * np.outer(fs3, th_)) @ prof(th_) * w.dt
    thetas = np.array([0.5, 1.0, math.pi / 2, 2.2])
    phis = np.array([0.3, 1.1, 2.0, 4.0])
    ff = w.far_field(nid, (thetas, phis))
    for i, f in enumerate(fs3):
        kk = 2 * np.pi * f
        # E = i k A e^{ikr}/(4 pi r) (the module's convention); the dipole: E_theta = -i omega mu (I l) sin(th)
        # e^{ikr}/(4 pi r) (exp(-i w t)) -> A_theta = -(I l) sin(th) (mu = eta = 1, k = omega); |.| compared
        A_exact = np.abs(I[i]) * np.sin(thetas)
        print(f"  3-D, {r} cells/unit, f = {f}: |A_theta|/|I l sin th| - 1 = "
              f"{np.round(np.abs(ff['E_theta'][i]) / A_exact - 1, 4)}; |A_phi|/|A_theta| = "
              f"{np.round(np.abs(ff['E_phi'][i]) / np.abs(ff['E_theta'][i]), 4)}")
for r in (20, 40):
    dx = 1.0 / r
    prof = F.ModulatedGaussian(1.0, fwidth=0.25)
    w = F.FDTD((4.0, 4.0), dx, pol="tm", pml=12)
    w.add_source(F.CurrentSource("ez", prof, position=(2.0, 2.0)))
    nid = w.add_near2far(((1.0, 1.0), (3.0, 3.0)), fs3)
    n = int((prof.end() + 6.0) / w.dt)
    w.advance(n)
    th_ = (np.arange(n) + 0.5) * w.dt
    I = np.exp(2j * np.pi * np.outer(fs3, th_)) @ prof(th_) * w.dt
    phis = np.array([0.0, 0.7, 2.0, 4.0])
    ff = w.far_field(nid, phis)
    for i, f in enumerate(fs3):
        kk = 2 * np.pi * f
        # E_z = -(omega mu I / 4) H_0(k rho) -> -(omega I/4) sqrt(2/(pi k rho)) e^{i(k rho - pi/4)}
        # module: E_z = i k A e^{i(k rho + pi/4)} / sqrt(8 pi k rho) -> |A| = (omega |I| / 4) sqrt(2/pi) sqrt(8 pi) / k
        A_exact = (2 * np.pi * f) * np.abs(I[i]) / 4 * math.sqrt(2 / math.pi) * math.sqrt(8 * math.pi) / kk
        print(f"  2-D TM, {r} cells/unit, f = {f}: |A|/exact - 1 = {np.round(np.abs(ff['A'][i]['tm']) / A_exact - 1, 4)}")

print("== (4) cylinder series ==")
for m in (1.5, 2.0, 1.5 + 0.2j):
    r = [cy.efficiencies(m, x, "te")["Qsca"] / (math.pi ** 2 * x ** 3 / 4 * abs((m * m - 1) / (m * m + 1)) ** 2) - 1
         for x in (0.02, 0.01, 0.005)]
    print(f"  TE Rayleigh limit Q_sca / (pi^2 x^3/4 |(m^2-1)/(m^2+1)|^2) - 1, m = {m}: {np.round(r, 6)}")
for m in (1.5 + 0.1j, 2 + 1j):
    print(f"  m = {m}: Q_abs TM {cy.efficiencies(m, 3.0, 'tm')['Qabs']:.4f}, TE {cy.efficiencies(m, 3.0, 'te')['Qabs']:.4f}"
          f"; sphere (mie) Q_abs {mie.efficiencies(m, 3.0)['Qabs']:.4f}; with conj(m): cylinder TM "
          f"{cy.efficiencies(np.conj(m), 3.0, 'tm')['Qabs']:.4f}")
