# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P1 (B8): reflection at a planar interface against Fresnel's coefficients (``core.optics.interfaces``) for a
dielectric, a conductor, Drude, Debye and Lorentz media, at normal and oblique incidence (TE = s, TM = p, Brewster's
angle); and how the flux monitor sees a plane wave (review B8-fdtd F5).

The runs are one cell wide and periodic across (Bloch-periodic for oblique incidence: the wave keeps k_y and each
frequency f meets the interface at sin(theta) = k_y / (2 pi f)); the plane wave enters through a one-sided TF/SF face,
so the scattered-field region holds the reflected wave alone, whose flux is divided by the incident intensity.

**The monitor and the normalisation.** The flux monitor averages E and H to the centres of its face's cells, so it
measures the grid's own plane wave weaker than its true flux density by a closed-form factor (``FDTD.monitor_factor``,
``fdtd_tfsf.monitor_factor``): cos(k_v dx/2) cos^2(k_t dx/2) in 2-D TM, cos(k_v dx/2) in 2-D TE (v the face's normal,
t the other in-plane axis), = 1 - (k dx)^2/8 + ... at normal incidence. ``test_monitor_factor_is_what_the_monitor_
measures`` checks it on the incident wave alone (to 2e-9). The reflected wave travels along the same axis as the
incident one, so R = flux / ``incident_intensity(normalisation="monitor")`` is free of the monitor's bias, while
R / ``incident_intensity()`` (the exact intensity) is low by the factor (-0.3 % ... -2.8 % at 20 cells per unit for
f = 0.5 ... 1.5). Before the review the planar numbers were taken with the exact intensity, so the stated scheme
errors contained the monitor's (-(k dx)^2/8) [error in earlier, review B8-fdtd F5].

Two references, both closed forms:
* **The grid's own exact reflection.** On the Yee grid a planar interface reflects with
  r_d = (e^{i k1 dx} - e^{i k2 dx}) / (e^{i k2 dx} - e^{-i k1 dx}) when it lies on an H node (both media sampled sharply)
  and r_d = (sin k1 dx - sin k2 dx) / (sin k1 dx + sin k2 dx) when it lies on an E node with the arithmetic mean of eps
  there — in modulus Schneider's (Understanding the FDTD Method) eqs. 7.72 and 7.90 (checked to round-off,
  sources/verification_2026-11-04_p1_fdtd.md) — (derived here from the discrete Helmholtz equation
  E_{i+1} - 2 E_i + E_{i-1} + (Omega dx)^2 eps_i E_i = 0 with the discrete wavenumbers
  (2/dx) sin(k_j dx / 2) = sqrt(Omega^2 eps_j - K_y^2) and the scheme's own permittivity ``Medium.epsilon_discrete``).
  The monitor-normalised R equals |r_d|^2 to 2e-4 (measured 2e-6 ... 9.6e-5: the pulse spectrum's truncation and the
  layer's reflection) — the implementation is the scheme.
* **Fresnel with the model's eps(f)**: approached at second order in the cell (the error falls 3.8-4.6x per halving).
  The Yee scheme's interface error is large at coarse grids (n = 2 at 10 cells per wavelength in the medium: +10.7 %
  of R with the interface on an H node, -10.3 % on an E node; the exact-intensity numbers +9.3 % / -11.4 % included
  the monitor's -2.4 %), which the first reference shows to be the scheme's, not the code's.
"""

import math

import numpy as np
import pytest

from lfphys.core.em import fdtd as F
from lfphys.core.optics.interfaces import fresnel


def _kd(Om, eps, dx, ky=0.0):
    s = np.sqrt(Om ** 2 * eps - (2 / dx * np.sin(ky * dx / 2)) ** 2 + 0j) * dx / 2
    k = 2 / dx * np.arcsin(s)
    return np.where(np.imag(k) < 0, -k, k)


def _r_grid(k1, k2, dx, place):
    if place == "h":
        return (np.exp(1j * k1 * dx) - np.exp(1j * k2 * dx)) / (np.exp(1j * k2 * dx) - np.exp(-1j * k1 * dx))
    return (np.sin(k1 * dx) - np.sin(k2 * dx)) / (np.sin(k1 * dx) + np.sin(k2 * dx))


def _reflect(med, res, place="h", pol="tm", fs=None, ky=0.0, prof=None):
    """(R by the monitor normalisation, R by the exact intensity, the grid's exact |r_d|^2, the monitor factor as
    this test computes it independently) at frequencies fs."""
    fs = np.linspace(0.5, 1.5, 5) if fs is None else np.asarray(fs, float)
    dx = 1.0 / res
    w = F.FDTD((6.0, dx), dx, pol=pol, boundary={"x": "pml", "y": "periodic"}, pml=20,
               bloch=(0.0, ky) if ky else None)
    prof = prof or F.ModulatedGaussian(1.0, fwidth=0.3)
    w.add_source(F.PlaneWave(prof, ((2.0, -math.inf), (math.inf, math.inf))))
    w.add_body(F.HalfSpace((3.0 + (0.5 * dx if place == "h" else 0.0), 0.0), (-1.0, 0.0)), med)
    fid = w.add_flux(((1.0, 0.0), (1.0, dx)), freqs=fs, direction=-1)
    w.advance(int((prof.end() + 14) / w.dt))
    P = w.flux(fid)["spectrum"] / dx
    Rm = P / w.incident_intensity(fs, normalisation="monitor")
    Rx = P / w.incident_intensity(fs)
    Om = 2 / w.dt * np.sin(2 * np.pi * fs * w.dt / 2)
    k1 = _kd(Om, 1.0, dx, ky)
    k2 = _kd(Om, med.epsilon_discrete(fs, w.dt), dx, ky)
    Rd = np.abs(_r_grid(k1, k2, dx, place)) ** 2
    fac = np.cos(np.real(k1) * dx / 2) * (np.cos(ky * dx / 2) ** 2 if pol == "tm" else 1.0)
    return Rm, Rx, Rd, fac


def _fresnel_normal(med, fs):
    n = np.sqrt(med.epsilon(fs) + 0j)
    return np.abs((1 - n) / (1 + n)) ** 2


MEDIA = {
    "dielectric n=2": F.Medium(eps=4.0),
    "conductor": F.Medium(eps=2.0, sigma=3.0),
    "Drude metal": F.Medium(poles=[F.Drude(2.0, 0.1)]),
    "Debye": F.Medium(eps=2.0, poles=[F.Debye(3.0, 0.2)]),
    "Lorentz": F.Medium(eps=1.5, poles=[F.Lorentz(1.0, 1.1, 0.2)]),
}


@pytest.mark.parametrize("name", list(MEDIA))
@pytest.mark.parametrize("pol", ["tm", "te"])
def test_normal_incidence_reflection(name, pol):
    """Measured (2026-11-04, after review B8-fdtd): monitor-normalised R / |r_d|^2 - 1 within 2e-6 ... 9.6e-5; the
    exact-intensity R lower by the monitor factor (to 2e-16 of it); Fresnel errors of the monitor-normalised R at 40
    cells per unit: n = 2 +0.6 ... +5.8 % (H node) / -0.6 ... -5.7 % (E node), conductor +0.4 ... +4.0 %, Drude
    +0.12 ... +0.22 %, Debye +0.6 ... +4.7 %, Lorentz +0.5 ... +3.1 %; ratios 20/40 cells 3.8-4.6."""
    med = MEDIA[name]
    fs = np.linspace(0.5, 1.5, 5)
    places = ("h", "e") if med.plain else ("h",)
    for place in places:
        errs = []
        for res in (20, 40):
            Rm, Rx, Rd, fac = _reflect(med, res, place, pol, fs)
            assert np.all(np.abs(Rm / Rd - 1) < 2e-4), (name, place, res, Rm / Rd - 1)
            # the engine's monitor factor is the closed form computed here (normal incidence: cos(k1 dx/2))
            assert np.allclose(Rx / Rm, fac, rtol=1e-12, atol=0), (name, place, res)
            # the negative control: with the exact intensity R is low by the monitor's factor, beyond the tolerance
            if res == 20:
                assert np.all(Rx / Rd - 1 < -2e-3), (name, place, Rx / Rd - 1)
            errs.append(np.abs(Rm / _fresnel_normal(med, fs) - 1))
        ratio = errs[0] / errs[1]
        big = errs[0] > 1e-3  # where the coarse error is resolvable
        assert np.all((ratio[big] > 3.5) & (ratio[big] < 4.8)), (name, place, ratio)
        assert np.all(errs[1] < 0.07), (name, place, errs[1])


def test_drude_reflection_is_not_the_dielectric_one():
    """The negative control of the dispersive tests: Fresnel with eps_inf alone (no poles) is far from the measured
    R of the Drude metal."""
    med = MEDIA["Drude metal"]
    fs = np.linspace(0.5, 1.5, 5)
    R = _reflect(med, 40, "h", "tm", fs)[0]
    assert np.all(R > 0.5) and np.all(np.abs(R - _fresnel_normal(F.Medium(eps=1.0), fs)) > 0.5)


def test_oblique_incidence_s_and_p():
    """Bloch-periodic run with k_y = 2 pi x 0.6: TE_z(Hz) = p, TM_z(Ez) = s; f = 0.9...1.5 -> 42...24 deg. The pulse
    1.2 +- 0.1 (it was +- 0.12, whose spectrum at the cut-off 0.6 left a window tail of 1.3e-6, now refused: review
    B8-fdtd F7). Measured (monitor-normalised): s equals |r_d|^2 to 4.3e-5; Fresnel errors s 4.0-16.6 % / 1.0-3.8 %,
    p 12-22 % / 2.9-4.9 % at 20 / 40 cells per unit (ratios 4.1-4.4)."""
    ky = 2 * np.pi * 0.6
    fs = np.array([0.9, 1.0, 1.2, 1.5])
    th = np.arcsin(0.6 / fs)
    prof = F.ModulatedGaussian(1.2, fwidth=0.1)
    errs = {"s": [], "p": []}
    for res in (20, 40):
        Rm, Rx, Rd, fac = _reflect(F.Medium(eps=2.25), res, "h", "tm", fs, ky, prof)
        assert np.all(np.abs(Rm / Rd - 1) < 2e-4), Rm / Rd - 1
        assert np.allclose(Rx / Rm, fac, rtol=1e-12, atol=0)
        errs["s"].append(np.abs(Rm / np.array([fresnel(1, 1.5, t, "s")[2] for t in th]) - 1))
        Rm, Rx, _, fac = _reflect(F.Medium(eps=2.25), res, "h", "te", fs, ky, prof)
        assert np.allclose(Rx / Rm, fac, rtol=1e-12, atol=0)  # TE: cos(k_x dx/2) alone
        errs["p"].append(np.abs(Rm / np.array([fresnel(1, 1.5, t, "p")[2] for t in th]) - 1))
    for k in ("s", "p"):
        ratio = errs[k][0] / errs[k][1]
        assert np.all((ratio > 3.5) & (ratio < 4.8)), (k, ratio)
        assert np.all(errs[k][1] < 0.06), (k, errs[k][1])


def test_brewster_angle():
    """p polarization at Brewster's angle atan(1.5) for f = 1: the amplitude |r_p| = sqrt(R_p) is the grid's error,
    O(dx^2), so R_p falls ~16x per halving of the cell (measured 9.0e-5 at 20 cells per wavelength, 5.5e-6 at 40);
    s polarization at the same angle reflects 15 % (the negative control). The pulse 1.0 +- 0.025 (it was +- 0.03,
    whose spectrum at the cut-off 0.83 left a window tail above 1e-7)."""
    thB = math.atan(1.5)
    ky = 2 * np.pi * math.sin(thB)
    prof = F.ModulatedGaussian(1.0, fwidth=0.025)
    Rp = []
    for res in (20, 40):
        Rp.append(float(_reflect(F.Medium(eps=2.25), res, "h", "te", [1.0], ky, prof)[0][0]))
    Rs = _reflect(F.Medium(eps=2.25), 20, "h", "tm", [1.0], ky, prof)[0]
    assert Rp[0] < 2e-4 and Rp[1] < 2e-5, Rp
    assert 3.0 < math.sqrt(Rp[0] / Rp[1]) < 5.0, Rp
    assert abs(Rs[0] / fresnel(1, 1.5, thB, "s")[2] - 1) < 0.1 and Rs[0] > 0.1


@pytest.mark.parametrize("pol", ["tm", "te"])
def test_monitor_factor_is_what_the_monitor_measures(pol):
    """Review B8-fdtd F5. The incident wave alone (no scatterer) through a plane x = 2 inside the total-field box, at
    0, 30 and 45 deg, 10 and 20 cells per unit: the measured flux per length equals ``incident_intensity(
    normalisation="monitor", axis="x")`` times the discrete direction cosine K_x / |K| (K_u = (2/dx) sin(k_u dx/2),
    k the grid's wavevector from ``yee_wavenumber``, computed here) to 2e-9 (measured 5e-11 ... 1.6e-9); the exact
    intensity is off by the factor itself (-0.15 ... -7 %: the negative control)."""
    for deg in (0.0, 30.0, 45.0):
        for res in (10, 20):
            dx = 1.0 / res
            fs = np.array([0.5, 1.0])
            w = F.FDTD((4.0, 4.0), dx, pol=pol, pml=12)
            th = math.radians(deg)
            prof = F.ModulatedGaussian(0.75, fwidth=0.25)
            w.add_source(F.PlaneWave(prof, ((0.5, 0.5), (3.5, 3.5)), direction=th))
            fid = w.add_flux(((2.0, 1.5), (2.0, 2.5)), freqs=fs)
            w.advance(int((prof.end() + 6) / w.dt))
            P = w.flux(fid)["spectrum"]
            km = F.yee_wavenumber(2 * np.pi * fs, (math.cos(th), math.sin(th)), dx, w.dt)
            Kx = 2 / dx * np.sin(km * math.cos(th) * dx / 2)
            Ky = 2 / dx * np.sin(km * math.sin(th) * dx / 2)
            cosK = Kx / np.hypot(Kx, Ky)
            Im = w.incident_intensity(fs, normalisation="monitor", axis="x")
            Ix = w.incident_intensity(fs)
            assert np.all(np.abs(P / (Im * cosK) - 1) < 2e-9), (pol, deg, res, P / (Im * cosK) - 1)
            assert np.all(np.abs(P / (Ix * cosK) - 1) > 1e-3), (pol, deg, res)
            # the closed form in 2-D: TM cos(k_x dx/2) cos^2(k_y dx/2), TE cos(k_x dx/2)
            fac = np.cos(km * math.cos(th) * dx / 2) * (np.cos(km * math.sin(th) * dx / 2) ** 2 if pol == "tm" else 1)
            assert np.allclose(w.monitor_factor(fs, "x"), fac, rtol=1e-13, atol=0)
