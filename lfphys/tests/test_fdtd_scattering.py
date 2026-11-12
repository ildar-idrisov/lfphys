# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P1 (B8): radiation and scattering against closed forms and exact series.

* A point dipole's radiated power, P = omega^4 |p|^2 / (12 pi eps0 c^3) (Larmor's dipole formula; Jackson, Classical
  Electrodynamics, 3rd ed., eq. 9.24), in the solver's units with the current moment I l = -i omega p:
  P = omega^2 |I l|^2 / (12 pi); in 2-D a line current I: P' = omega |I|^2 / 8 per unit length (from the far field
  E_z = -(omega mu I / 4) H_0^(1)(k rho): |E|^2 2 pi rho / (2 eta) with |H_0|^2 -> 2 / (pi k rho)), and its dual for a
  magnetic line current. Measured from the DFT flux through a closed box; second order in the cell.
* The TF/SF plane wave is an exact plane wave of the grid: the leak into the scattered-field region is round-off
  (measured 2-3e-9 of the incident peak); the negative control builds the same wave with the continuum wavenumber
  omega n / c instead of the grid's and leaks ~1e-3.
* 2-D scattering by a dielectric and a PEC cylinder against the exact series (``core.optics.cylinder``): Q_sca from a
  closed flux box in the scattered-field region, the far-field pattern from the near-to-far transform.
* 3-D scattering by a sphere against the exact Mie series (``core.optics.mie``, written by B8's Mie part; incident
  x-polarized along +z: E_theta = e^{ikr}/(-ikr) cos(phi) S2, E_phi = -e^{ikr}/(-ikr) sin(phi) S1).
"""

import math

import numpy as np
import pytest

from lfphys.core import backend
from lfphys.core.em import fdtd as F
from lfphys.core.em import fdtd_tfsf
from lfphys.core.optics import cylinder as cy
from lfphys.core.optics import mie


def _gpu():
    return backend.devices()["gpu"]["available"]


# --- dipole radiation ---------------------------------------------------------------------------------------------
def _current_dft(prof, fs, n, dt):
    th = (np.arange(n) + 0.5) * dt  # the current enters at t_{n+1/2}
    return np.exp(2j * np.pi * np.outer(fs, th)) @ prof(th) * dt


def test_dipole_power_3d():
    fs = np.array([0.8, 1.0, 1.2])
    errs = []
    for res in (10, 20):
        dx = 1.0 / res
        prof = F.ModulatedGaussian(1.0, fwidth=0.3)
        w = F.FDTD((1.6, 1.6, 1.6), dx, pml=10)
        w.add_source(F.CurrentSource("ez", prof, position=(0.8, 0.8, 0.8)))
        fid = w.add_flux(((0.4, 0.4, 0.4), (1.2, 1.2, 1.2)), freqs=fs)
        n = int((prof.end() + 4.0) / w.dt)
        w.advance(n)
        P = w.flux(fid)["spectrum"]
        I = _current_dft(prof, fs, n, w.dt)
        Pex = (2 * np.pi * fs) ** 2 * np.abs(I) ** 2 / (12 * np.pi)
        errs.append(P / Pex - 1)
    assert np.all(np.abs(errs[1]) < 0.02), errs
    ratio = np.abs(errs[0] / errs[1])
    assert np.all((ratio > 3.0) & (ratio < 5.0)), errs


@pytest.mark.parametrize("pol", ["tm", "te"])
def test_line_source_power_2d(pol):
    fs = np.array([0.8, 1.0, 1.2])
    errs = []
    comp = "ez" if pol == "tm" else "hz"
    for res in (20, 40):
        dx = 1.0 / res
        prof = F.ModulatedGaussian(1.0, fwidth=0.25)
        w = F.FDTD((4.0, 4.0), dx, pol=pol, pml=12)
        pos = (2.0, 2.0) if pol == "tm" else (2.0 + dx / 2, 2.0 + dx / 2)
        w.add_source(F.CurrentSource(comp, prof, position=pos))
        fid = w.add_flux(((1.0, 1.0), (3.0, 3.0)), freqs=fs)
        n = int((prof.end() + 6.0) / w.dt)
        w.advance(n)
        P = w.flux(fid)["spectrum"]
        # a magnetic current M enters Faraday's law at t_n
        I = _current_dft(prof, fs, n, w.dt) if pol == "tm" else \
            np.exp(2j * np.pi * np.outer(fs, np.arange(n) * w.dt)) @ prof(np.arange(n) * w.dt) * w.dt
        errs.append(P / (2 * np.pi * fs * np.abs(I) ** 2 / 8) - 1)
    assert np.all(np.abs(errs[1]) < 0.006), errs  # measured 0.11-0.25 % (TM), 0.18-0.41 % (TE) at 40 cells per unit
    ratio = np.abs(errs[0] / errs[1])
    assert np.all((ratio > 3.5) & (ratio < 4.5)), errs


# --- the TF/SF plane wave -------------------------------------------------------------------------------------------
def _leak_2d(pol, angle):
    w = F.FDTD((5.0, 5.0), 0.05, pol=pol, pml=12)
    prof = F.ModulatedGaussian(1.0, fwidth=0.3)
    w.add_source(F.PlaneWave(prof, ((1.5, 1.5), (3.5, 3.5)), direction=angle))
    c = "ez" if pol == "tm" else "hz"
    X, Y = np.meshgrid(*w.coords(c), indexing="ij")
    tf = (X > 1.6) & (X < 3.4) & (Y > 1.6) & (Y < 3.4)
    sf = ((X < 1.3) | (X > 3.7) | (Y < 1.3) | (Y > 3.7)) & (X > 0) & (X < 5) & (Y > 0) & (Y < 5)
    mtf = msf = 0.0
    for _ in range(int((prof.end() + 7) / w.dt) // 20):
        w.advance(20)
        f = np.abs(w.field(c))
        mtf, msf = max(mtf, f[tf].max()), max(msf, f[sf].max())
    return msf / mtf, w.checks()


@pytest.mark.parametrize("pol", ["tm", "te"])
@pytest.mark.parametrize("deg", [0.0, 30.0, 57.0])
def test_tfsf_leak_is_round_off_2d(pol, deg):
    leak, checks = _leak_2d(pol, math.radians(deg))
    assert leak < 1e-7, leak
    assert checks["tfsf_1"]["window_tail"] < 1e-6


def test_tfsf_leak_with_the_continuum_wavenumber(monkeypatch):
    """The negative control: an incident wave with k = omega n / c (not the grid's) leaks ~1e-3."""
    monkeypatch.setattr(fdtd_tfsf, "yee_wavenumber", lambda w, d, dx, dt, nb=1.0: nb * np.asarray(w, float))
    leak, _ = _leak_2d("tm", math.radians(30))
    assert leak > 1e-4, leak


def test_tfsf_continuous_wave():
    """A ramped continuous wave (30 deg, f = 1, ramp 6 time units): exact at its frequency once the ramp is over; the
    ramp's envelope travels with the discrete group delay, an approximation. Measured leak: up to 4e-4 of the
    incident amplitude while the ramp lasts (2.4e-3 for a 2-unit ramp), 1.6e-7 ... 1.3e-8 afterwards (the waves leaked
    earlier leaving through the layers); the amplitude in the total-field box is 1 to 1e-7."""
    w = F.FDTD((5.0, 5.0), 0.05, pol="tm", pml=12)
    w.add_source(F.PlaneWave(F.ContinuousWave(1.0, ramp=6.0), ((1.5, 1.5), (3.5, 3.5)), direction=math.radians(30)))
    X, Y = np.meshgrid(*w.coords("ez"), indexing="ij")
    tf = (X > 1.6) & (X < 3.4) & (Y > 1.6) & (Y < 3.4)
    sf = ((X < 1.3) | (X > 3.7) | (Y < 1.3) | (Y > 3.7)) & (X > 0) & (X < 5) & (Y > 0) & (Y < 5)
    during, late = 0.0, []
    for k in range(12):
        w.advance(int(2.0 / w.dt))
        f = np.abs(w.field("ez"))
        if w.t <= 11:
            during = max(during, f[sf].max() / f[tf].max())
        else:
            late.append(f[sf].max() / f[tf].max())
    assert during < 1e-3 and late[-1] < 1e-6, (during, late)
    assert abs(np.abs(w.field("ez"))[tf].max() - 1.0) < 1e-6


@pytest.mark.parametrize("direction,pol", [((0, 0, 1), (1, 0, 0)), ((1.0, 0.5, 2.0), (0.5, -1.0, 0.0))],
                         ids=["normal", "oblique"])
def test_tfsf_leak_3d(direction, pol):
    """Measured: 4.9e-10 of the peak at oblique incidence (419 distinct incident series, 3.3 MB)."""
    w = F.FDTD((1.6, 1.6, 1.6), 0.08, pml=8)
    prof = F.ModulatedGaussian(0.8, fwidth=0.3)
    w.add_source(F.PlaneWave(prof, ((0.4,) * 3, (1.2,) * 3), direction=direction, polarization=pol))
    X, Y, Z = np.meshgrid(*w.coords("ex"), indexing="ij")
    tf = (np.abs(X - 0.8) < 0.3) & (np.abs(Y - 0.8) < 0.3) & (np.abs(Z - 0.8) < 0.3)
    inside = (X > 0) & (X < 1.6) & (Y > 0) & (Y < 1.6) & (Z > 0) & (Z < 1.6)
    sf = inside & ((np.abs(X - 0.8) > 0.55) | (np.abs(Y - 0.8) > 0.55) | (np.abs(Z - 0.8) > 0.55))
    mtf = msf = 0.0
    for _ in range(int((prof.end() + 4) / w.dt) // 10):
        w.advance(10)
        f = np.abs(w.field("ex"))
        mtf, msf = max(mtf, f[tf].max()), max(msf, f[sf].max())
    assert msf / mtf < 1e-7, msf / mtf


def _slab_leak(f_par, fw, pol="tm"):
    """A Bloch slab wave with two finite faces (x = 2 and 4; y periodic): only leak reaches the scattered side."""
    w = F.FDTD((6.0, 1.0), 0.05, pol=pol, boundary={"x": "pml", "y": "periodic"}, pml=16,
               bloch=(0.0, 2 * math.pi * f_par) if f_par else None)
    prof = F.ModulatedGaussian(1.2, fwidth=fw)
    w.add_source(F.PlaneWave(prof, ((2.0, -math.inf), (4.0, math.inf)), direction=0.0))
    c = "ez" if pol == "tm" else "hz"
    x = w.coords(c)[0]
    sf = ((x > 0.2) & (x < 1.8)) | ((x > 4.2) & (x < 5.8))
    tf = (x > 2.2) & (x < 3.8)
    msf = mtf = 0.0
    for _ in range(int((prof.end() + 12) / w.dt) // 20):
        w.advance(20)
        a = np.abs(w.field(c))
        msf, mtf = max(msf, a[sf].max()), max(mtf, a[tf].max())
    return msf / mtf, w.checks()["tfsf_1"]["window_tail"]


def test_bloch_slab_leak_near_the_cut_off():
    """Review B8-fdtd F7. A pulse 1.2 +- 0.15 whose spectrum reaches the Bloch wave's cut-off (k_par = 2 pi x 0.6,
    cut-off f = 0.6) leaked 5.9e-6; the cause is not the FFT window's length (its tail, 1.8e-5, is the same for
    M = 4096 ... 65536) but the precursor of the spectrum cut sharply at the cut-off: the grid's wave is not zero at
    the start of the run, where the injection begins. Such a wave is now refused (tail > 1e-6, the leak ~0.3-0.4 x
    the tail); a narrower band is accepted and leaks at the level of the profile's own cut-off. Away from the cut-off
    (k_par = 2 pi x 0.3) the leak stays 2-3e-9; k_par = 2 pi x 0.5 (tail 9.1e-7) is accepted with the leak below
    0.4 x the tail (measured 3.4e-7)."""
    with pytest.raises(ValueError, match="начале счёта"):
        _slab_leak(0.6, 0.15)
    leak, tail = _slab_leak(0.6, 0.08)
    assert leak < 1e-8 and tail < 1e-7, (leak, tail)
    leak, tail = _slab_leak(0.3, 0.15)
    assert leak < 1e-8, leak
    leak, tail = _slab_leak(0.5, 0.15)
    assert tail < 1e-6 and leak < 0.4 * tail, (leak, tail)


# --- 2-D cylinder ----------------------------------------------------------------------------------------------------
def _cylinder(med, pol, res, fs, a=0.5):
    w = F.FDTD((4.0, 4.0), 1.0 / res, pol=pol, pml=16)
    prof = F.ModulatedGaussian(0.7, fwidth=0.25)
    w.add_source(F.PlaneWave(prof, ((0.8, 0.8), (3.2, 3.2)), direction=0.0))
    w.add_body(F.Cylinder((2.0, 2.0), a), med)
    sca = w.add_flux(((0.5, 0.5), (3.5, 3.5)), freqs=fs)
    tot = w.add_flux(((1.2, 1.2), (2.8, 2.8)), freqs=fs)
    n2f = w.add_near2far(((0.4, 0.4), (3.6, 3.6)), freqs=fs)
    w.advance(int((prof.end() + 25) / w.dt))
    return w, w.cross_sections(sca, tot), n2f


@pytest.mark.parametrize("pol", ["tm", "te"])
def test_dielectric_cylinder_against_the_series(pol):
    """m = 1.5, a = 0.5, x = 1.3...3.1, sub-pixel averaging; Q_sca with both normalisations (review B8-fdtd F5): the
    exact incident intensity, and the incident wave as the flux monitor measures it (``normalisation="monitor"``,
    Meep's convention; the two differ by the monitor factor cos(k dx/2) exactly). Measured (2026-11-04, after the
    review), at 20 / 40 / 80 cells per unit:
    TM exact +0.11...+0.21 % / +0.03...+0.06 % / +0.007...+0.016 %; monitor +0.39...+1.47 % / +0.10...+0.37 % /
    +0.024...+0.093 % (both second order: ratios 3.3-4.0);
    TE exact -0.02...+0.89 % / -0.12...+0.29 % / -0.09...+0.11 %; monitor +0.18...+2.13 % / -0.07...+0.60 % /
    -0.08...+0.19 % (not monotone at f = 0.4: the diagonal-only averaging, first order for in-plane E on a curved
    surface, F6).
    Neither number is the scheme's error alone: the monitor measures each scattered wave weaker by 1 - O((k dx)^2)
    depending on its direction (``FDTD.cross_sections``), as large as the scheme's error here, and the exact-intensity
    numbers are smaller because that bias cancels part of the scheme's positive error [the earlier statement
    "0.03-0.3 % of the series" was this cancellation, error in earlier]. The absorption of the lossless cylinder is the
    flux monitors' second-order error (below 0.01 Q at 20 cells, 0.0025 at 40); the far field within 0.4 % / 0.7 %
    (TM) and 0.6 % / 0.9 % (TE) of the pattern's peak at 40 cells (exact / monitor)."""
    a = 0.5
    fs = np.array([0.4, 0.6, 0.8, 1.0])
    ex = np.array([cy.efficiencies(1.5, 2 * np.pi * f * a, pol)["Qsca"] for f in fs])
    err, errm, qabs = [], [], []
    for res in (20, 40):
        w, cs, n2f = _cylinder(F.Medium(eps=2.25), pol, res, fs, a)
        sca, tot = (k for k, m in w._monitors.items() if m["kind"] == "flux")
        cm = w.cross_sections(sca, tot, normalisation="monitor")
        assert np.allclose(cs["sigma_sca"] / cm["sigma_sca"], cm["monitor_factor"], rtol=1e-12, atol=0)
        k_grid = F.yee_wavenumber(2 * np.pi * fs, (1.0, 0.0), 1.0 / res, w.dt)
        assert np.allclose(cm["monitor_factor"], np.cos(k_grid / res / 2), rtol=1e-13, atol=0)
        err.append(cs["sigma_sca"] / (2 * a) / ex - 1)
        errm.append(cm["sigma_sca"] / (2 * a) / ex - 1)
        qabs.append(cs["sigma_abs"] / (2 * a))
    assert np.all(np.abs(err[0]) < (0.004 if pol == "tm" else 0.012)), err
    assert np.all(np.abs(err[1]) < (0.001 if pol == "tm" else 0.004)), err
    assert np.all(np.abs(errm[0]) < (0.02 if pol == "tm" else 0.025)), errm
    assert np.all(np.abs(errm[1]) < (0.005 if pol == "tm" else 0.008)), errm
    if pol == "tm":  # second order with either normalisation
        for e in (err, errm):
            ratio = e[0] / e[1]
            assert np.all((ratio > 3.0) & (ratio < 5.0)), ratio
    assert np.all(np.abs(qabs[1]) < 0.003), qabs
    # the far-field pattern (40 cells per unit; measured within 0.4-0.9 % of the peak)
    phis = np.array([0.0, 0.6, 1.2, 2.0])
    for norm in ("exact", "monitor"):
        ff = w.far_field(n2f, phis, normalisation=norm)
        for i, f in enumerate(fs):
            ds = cy.dsigma_dphi(1.5, 2 * np.pi * f * a, pol, phis, k=2 * np.pi * f)
            dev = np.abs(ff["dsigma_dphi"][i] - ds) / ds.max()  # relative to the pattern's peak (minima are tiny)
            assert np.all(dev < 0.01), (norm, f, dev)


@pytest.mark.parametrize("pol", ["tm", "te"])
def test_pec_cylinder_against_the_series(pol):
    """PEC by staircase (first order): TM's E_z nodes inside the conductor are zero; TE's E components are zero where
    their whole Yee edge is inside. Measured Q_sca errors (exact intensity) at 20 / 40 / 80 cells per unit
    (f = 0.4, 0.7, 1.0): TM -3.2...-4.6 % / -1.6...-2.0 % / -0.78...-0.90 %; TE -0.5...+9.0 % / -1.7...+1.0 % /
    -0.8...+0.4 % (with the node rule +10...+30 % / +2.8...+6.8 % / +1.6...+3.8 %). [The numbers stated before the
    review, TM -2.7...-4.0 % / -1.5...-1.9 % / -0.8 % and TE -0.3...+6.4 % / -1.2...+1.4 % / -0.7...+0.6 %, were not
    those of this test; the original code gives the numbers above: error in earlier, found while processing review
    B8-fdtd.]"""
    a = 0.5
    fs = np.array([0.4, 0.7, 1.0])
    ex = np.array([cy.efficiencies("pec", 2 * np.pi * f * a, pol)["Qsca"] for f in fs])
    err = []
    for res in (20, 40):
        _, cs, _ = _cylinder(F.Medium.pec(), pol, res, fs, a)
        err.append(cs["sigma_sca"] / (2 * a) / ex - 1)
    assert np.all(np.abs(err[1]) < (0.025 if pol == "tm" else 0.02)), err
    if pol == "tm":
        assert np.all(np.abs(err[0]) / np.abs(err[1]) > 1.6), err  # first order


def test_absorbing_cylinder_absorption():
    """A lossy (conducting) cylinder: sigma_abs from the net flux into a total-field box, from the volume integral
    (1/2) omega Im(eps_d) |E|^2 of a DFT monitor, and from the exact series with m = sqrt(eps(f))."""
    a = 0.5
    fs = np.array([0.5, 0.7, 0.9])
    med = F.Medium(eps=2.0, sigma=1.0)
    w = F.FDTD((4.0, 4.0), 1.0 / 40, pol="tm", pml=16)
    prof = F.ModulatedGaussian(0.7, fwidth=0.2)
    w.add_source(F.PlaneWave(prof, ((0.8, 0.8), (3.2, 3.2)), direction=0.0))
    w.add_body(F.Cylinder((2.0, 2.0), a), med)
    sca = w.add_flux(((0.5, 0.5), (3.5, 3.5)), freqs=fs)
    tot = w.add_flux(((1.2, 1.2), (2.8, 2.8)), freqs=fs)
    vol = w.add_dft(((1.45, 1.45), (2.55, 2.55)), fs, ["ez"])
    w.advance(int((prof.end() + 25) / w.dt))
    cs = w.cross_sections(sca, tot)
    I = w.incident_intensity(fs)
    Pv = w.absorbed_power(vol)["power"] / I
    m = np.sqrt(med.epsilon(fs))
    ex_abs = np.array([cy.efficiencies(mm, 2 * np.pi * f * a, "tm")["Qabs"] for mm, f in zip(m, fs)]) * 2 * a
    ex_sca = np.array([cy.efficiencies(mm, 2 * np.pi * f * a, "tm")["Qsca"] for mm, f in zip(m, fs)]) * 2 * a
    assert np.all(np.abs(cs["sigma_abs"] / ex_abs - 1) < 0.03), cs["sigma_abs"] / ex_abs - 1
    assert np.all(np.abs(cs["sigma_sca"] / ex_sca - 1) < 0.03), cs["sigma_sca"] / ex_sca - 1
    assert np.all(np.abs(Pv / cs["sigma_abs"] - 1) < 0.02), Pv / cs["sigma_abs"] - 1


# --- 3-D sphere -------------------------------------------------------------------------------------------------------
def _sphere(res, device="auto", fs=(0.4, 0.6, 0.8)):
    a = 0.5
    fs = np.asarray(fs, float)
    w = F.FDTD((3.0, 3.0, 3.0), 1.0 / res, pml=10, device=device)
    prof = F.ModulatedGaussian(0.6, fwidth=0.18)
    w.add_source(F.PlaneWave(prof, ((0.7,) * 3, (2.3,) * 3), direction=(0, 0, 1), polarization=(1, 0, 0)))
    w.add_body(F.Sphere((1.5, 1.5, 1.5), a), F.Medium(eps=2.25))
    sca = w.add_flux(((0.5,) * 3, (2.5,) * 3), freqs=fs)
    tot = w.add_flux(((0.85,) * 3, (2.15,) * 3), freqs=fs)
    n2f = w.add_near2far(((0.45,) * 3, (2.55,) * 3), freqs=fs)
    w.advance(int((prof.end() + 18) / w.dt))
    cs = w.cross_sections(sca, tot)
    cm = w.cross_sections(sca, tot, normalisation="monitor")
    th = np.array([0.3, 1.0, 1.6, 2.5])
    ph = np.array([0.0, 0.7, 1.2, 0.3])
    ff = w.far_field(n2f, (th, ph))
    out = {"Qsca": cs["sigma_sca"] / (math.pi * a * a), "Qabs": cs["sigma_abs"] / (math.pi * a * a), "ds": [],
           "Qsca_monitor": cm["sigma_sca"] / (math.pi * a * a)}
    out["Qmie"] = np.array([mie.efficiencies(1.5, 2 * np.pi * f * a)["Qsca"] for f in fs])
    for i, f in enumerate(fs):
        k = 2 * np.pi * f
        sc = mie.scattering(1.5, k * a, th)
        ds = (np.abs(sc["S2"]) ** 2 * np.cos(ph) ** 2 + np.abs(sc["S1"]) ** 2 * np.sin(ph) ** 2) / k ** 2
        out["ds"].append(ff["dsigma_domega"][i] / ds - 1)
    return out


def test_sphere_against_mie():
    """m = 1.5, a = 0.5, x = 1.26, 1.88, 2.51, 16 cells per unit (CPU, ~15 s). Measured: Q_sca +1.66 / +0.33 /
    +1.20 % off Mie with the exact intensity, +1.97 / +1.03 / +2.47 % with the monitor's (review B8-fdtd F5; the
    monitor factor -0.3 / -0.7 / -1.2 %); dsigma/dOmega at four directions off by up to 5.9 % (exact), 7.2 %
    (monitor); Q_abs of the lossless sphere -0.001...-0.005 (the monitors' second-order error)."""
    r = _sphere(16)
    assert np.all(np.abs(r["Qsca"] / r["Qmie"] - 1) < 0.025), r["Qsca"] / r["Qmie"] - 1
    assert np.all(np.abs(r["Qsca_monitor"] / r["Qmie"] - 1) < 0.03), r["Qsca_monitor"] / r["Qmie"] - 1
    assert np.all(np.abs(r["Qabs"]) < 0.01), r["Qabs"]
    assert np.all(np.abs(np.array(r["ds"])) < 0.08), r["ds"]


@pytest.mark.skipif(not _gpu(), reason="needs GPU 0 (minutes on the CPU)")
def test_sphere_against_mie_converges_gpu():
    """32 cells per unit on GPU 0. Measured (after review B8-fdtd): Q_sca +0.76 / -0.01 / +0.30 % with the exact
    intensity, +0.84 / +0.16 / +0.61 % with the monitor's (16 cells: +1.66 / +0.33 / +1.20 % and +1.97 / +1.03 /
    +2.47 %): error ratios 2.2-4.1 (monitor 2.3-6.3; a ratio of 33 at f = 0.6 is a zero crossing); dsigma/dOmega off
    by up to 1.9 % (exact) and 2.0 % (monitor). The averaging keeps the diagonal only (VP-EP, first order in general for
    in-plane E on a curved surface: F6); the earlier "between first and second order" read these two points only."""
    backend.configure({"kernels": {F.KERNEL: {"device": "gpu"}}})
    try:
        r16, r32 = _sphere(16, "auto"), _sphere(32, "auto")
    finally:
        backend.configure({})
    for key in ("Qsca", "Qsca_monitor"):
        e16 = np.abs(r16[key] / r16["Qmie"] - 1)
        e32 = np.abs(r32[key] / r32["Qmie"] - 1)
        print("sphere", key, "errors", e16, e32, "far field", np.array(r16["ds"]), np.array(r32["ds"]))
        assert np.all(e32 < 0.01), (key, e32)
        assert np.all(e32 < e16 / 1.8), (key, e16, e32)
    assert np.all(np.abs(np.array(r32["ds"])) < 0.04), r32["ds"]


@pytest.mark.skipif(not _gpu(), reason="needs GPU 0 (minutes on the CPU)")
def test_te_high_contrast_cylinder_is_first_order_gpu():
    """Review B8-fdtd F6: for E in the plane of a curved surface the diagonal-only (VP-EP) averaging converges at
    first order. TE cylinder eps = 6, a = 0.5, f = 0.5, run until the field has decayed (pulse end + 60): Q_sca
    +2.62 % / +1.44 % at 40 / 80 cells per unit (exact intensity; +2.70 / +1.46 % monitor's), ratio 1.83 (160 cells:
    +0.77 %, ratio 1.86; GPU 0, ~55 s). A full-tensor averaging would make this test fail (ratio ~4): then the module's
    validity must be restated."""
    import math as _m
    backend.configure({"kernels": {F.KERNEL: {"device": "gpu"}}})
    a = 0.5
    fs = np.array([0.5])
    ex = cy.efficiencies(_m.sqrt(6.0), 2 * np.pi * 0.5 * a, "te")["Qsca"]
    err = []
    try:
        for res in (40, 80):
            w = F.FDTD((3.2, 3.2), 1.0 / res, pol="te", pml=max(16, res // 2), device="auto")
            prof = F.ModulatedGaussian(0.7, fwidth=0.15)
            w.add_source(F.PlaneWave(prof, ((0.6, 0.6), (2.6, 2.6)), direction=0.0))
            w.add_body(F.Cylinder((1.6, 1.6), a), F.Medium(eps=6.0))
            sca = w.add_flux(((0.4, 0.4), (2.8, 2.8)), freqs=fs)
            w.advance_to(prof.end() + 60.0)
            err.append(float(w.cross_sections(sca)["sigma_sca"][0] / (2 * a) / ex - 1))
    finally:
        backend.configure({})
    print("TE eps 6 Q_sca errors", err)
    assert 0.02 < err[0] < 0.03 and 1.5 < err[0] / err[1] < 2.3, err
