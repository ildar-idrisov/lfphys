# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Thin masks for optical vortices (theories.approx.beams_thin_masks; moved from the core after review B8-beams, O7),
each against a closed form or an independent route, with negative controls where a test checks a tolerance: the
spiral phase plate propagated exactly by two routes (angular spectrum against the order-l Hankel route); the fork
hologram's orders and their charges; its Fourier coefficients; the band-limited binary mask and the order powers
measured in the angular spectrum against the closed-form spectrum of the thin mask (review O8); the spinning rough
surface's on-axis shift and beat (Lavery et al. 2013)."""

import math

import numpy as np
import pytest

from lfphys.core.optics import angular_spectrum as AS
from lfphys.core.optics import beams as B
from lfphys.core.optics import beams_rotation as ROT
from lfphys.theories.approx import beams_paraxial as PX
from lfphys.theories.approx import beams_thin_masks as TM

LAM = 1.0
K = 2 * math.pi / LAM


# --- the spiral phase plate ------------------------------------------------------------------------------------------
def _spp_routes(l, w, z, n, dx, pad):
    """Angular spectrum (the exact 2-D spectrum 2 pi (-i)^l e^{i l phi_q} A_l(q) of the Gaussian behind the plate as
    the source) against the order-l Hankel route on the row y = 0: (largest difference / peak, the FFT field, x)."""
    fn, qmax = B.gaussian_vortex_spectrum(l, w)
    x = (np.arange(n) - n // 2) * dx

    def spec(qx, qy):
        q = np.hypot(qx, qy)
        return 2 * math.pi * (-1j) ** l * np.exp(1j * l * np.arctan2(qy, qx)) * fn(q)
    U = AS.propagate_field(AS.Spectral((n, n), spec), dx, K, z, pad=pad, check=True)
    sel = np.arange(n // 2 + int(0.5 / dx), n // 2 + int(7.5 / dx), max(1, int(1 / dx)))
    hk = B.VortexBeam(l, K, fn, qmax).scalar(np.abs(x[sel]), z)
    return float(np.max(np.abs(U[sel, n // 2] - hk)) / np.max(np.abs(U))), U, x


def test_spiral_phase_plate_exact_propagation_two_routes_charge_and_oam():
    """A Gaussian behind a continuous plate, propagated by the angular spectrum and by the order-l Hankel route. For
    l = 0 the two agree to round-off; for l = 3 the plate's singular centre sends light to all angles, which reaches
    the FFT's periodic copies: the difference is the FFT window's error and falls as the period grows (measured
    2026-11-04: 1.8e-4, then 7.1e-5 of the peak). The propagated field has charge 3 and 3 hbar per photon (to the
    window's error: 7e-6 with the period 256 lambda); the sampled plate too (to its sampling of the singular centre);
    a plate of 8 steps keeps the charge but not 3 per photon (measured 1.26 for the field propagated to z = 6; the
    sampled mask itself tends to the thin mask's (N / 2 pi) sin(2 pi l / N) = 0.90 — review B8-beams, s09 — the
    difference being the evanescent high harmonics)."""
    w, z = 2.0, 6.0
    assert _spp_routes(0, w, z, 256, 0.125, 2)[0] < 1e-13
    e1 = _spp_routes(3, w, z, 512, 0.25, 2)[0]
    e2 = _spp_routes(3, w, z, 512, 0.25, 4)[0]
    assert e2 < 0.6 * e1 and e2 < 1e-4, (e1, e2)
    l = 3
    _, U, x = _spp_routes(l, w, z, 512, 0.125, 4)
    assert abs(B.scalar_oam_per_photon(U, x, x) - l) < 1e-4
    assert B.charge_in_disc(U, x, x, 0, 0, 3 * w) == l
    dx = float(x[1] - x[0])
    X, Y = np.meshgrid(x, x, indexing="ij")
    for steps in (None, 8):
        U0 = np.exp(-(X * X + Y * Y) / w ** 2) * TM.spiral_phase_plate(X, Y, l, steps)
        Uz = TM.propagate(U0, dx, K, z)
        assert B.charge_in_disc(Uz, x, x, 0, 0, 2 * w) == l
        oam = B.scalar_oam_per_photon(Uz, x, x)
        if steps is None:
            assert abs(oam - l) < 2e-3  # the sampled singular plate
        else:
            assert abs(oam - l) > 0.5  # the stepped plate scatters into other orders
    # the centre's sample is the plate's mean around it
    assert TM.spiral_phase_plate(0.0, 0.0, 3) == 0 and TM.spiral_phase_plate(0.0, 0.0, 0) == 1
    assert abs(TM.spiral_phase_plate(0.0, 0.0, 8, steps=8) - 1) < 1e-15


# --- the fork hologram -----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("kind", ["amplitude", "binary", "blazed"])
def test_fork_hologram_order_m_carries_charge_m_l(kind):
    l, period, w = 2, 2.5, 4.0
    n, dx = 512, 0.25
    x = (np.arange(n) - n // 2) * dx
    X, Y = np.meshgrid(x, x, indexing="ij")
    U0 = np.exp(-(X * X + Y * Y) / w ** 2) * TM.fork_hologram(X, Y, l, period, kind, m_max=TM.fork_band(dx, period))
    z = 80.0  # the first orders are 35 lambda off the axis, about 5 w(z) from the zeroth
    U = TM.propagate(U0, dx, K, z)
    for m in (-1, 0, 1):
        c = TM.fork_order_coefficient(kind, m)
        if c == 0:
            continue
        xm = TM.order_position(m, period, K, z)
        assert B.charge_in_disc(U, x, x, xm, 0.0, 15.0) == m * l, (kind, m)
    # negative control: a grating without the fork (l = 0) gives no charge in the first order
    U0 = np.exp(-(X * X + Y * Y) / w ** 2) * TM.fork_hologram(X, Y, 0, period, kind)
    U = TM.propagate(U0, dx, K, z)
    assert B.charge_in_disc(U, x, x, TM.order_position(1, period, K, z), 0.0, 15.0) == 0


def test_fork_order_coefficients_are_the_fourier_series():
    f = np.linspace(-math.pi, math.pi, 4096, endpoint=False)
    for kind in TM.KINDS:
        t = {"amplitude": 0.5 * (1 + np.cos(f)), "binary": (np.cos(f) > 0) * 1.0,
             "blazed": np.exp(1j * np.mod(f, 2 * math.pi))}[kind]
        for m in range(-3, 4):
            cm = np.mean(t * np.exp(-1j * m * f))
            assert abs(cm - TM.fork_order_coefficient(kind, m)) < 2e-3, (kind, m, cm)


def test_band_limited_binary_mask_keeps_the_declared_coefficients():
    """On 9.75 samples per period (v16's fork) point samples of the binary mask have a wrong duty cycle (0.526 over the
    2-D fork, review B8-beams s07; 19/39 = 0.487 on this 1-D row, whose 39 sample phases repeat every 4 periods): the
    orders beyond the grid's band alias back. The band-limited series (``fork_band``) has c_m exactly for |m| <= M,
    measured by projection along x over 200 periods (l = 0); at the fork's centre a sample is c_0."""
    period, dx = 2.5, 2.5 / 9.75
    M = TM.fork_band(dx, period)
    assert M == 4 and M * 2 * math.pi / period < math.pi / dx < (M + 1) * 2 * math.pi / period
    x = np.arange(int(round(200 * 9.75))) * dx  # 200 periods: an integer number of them
    K = 2 * math.pi / period
    for mm, good in ((M, True), (None, False)):
        t = TM.fork_hologram(x, 0 * x + 1.0, 0, period, "binary", m_max=mm)
        for m in range(-M, M + 1):
            cm = np.mean(t * np.exp(1j * m * K * x))  # t = sum c_m e^{-i m K x} (f = -K x)
            err = abs(cm - TM.fork_order_coefficient("binary", m))
            if good:
                assert err < 1e-12, (m, cm)
            elif m == 0:
                assert err > 0.01, cm  # negative control: the point-sampled duty cycle (19 of 39 phases here)
    assert TM.fork_hologram(0.0, 0.0, 2, period, "binary", m_max=M) == 0.5
    assert TM.fork_hologram(0.0, 0.0, 1, period, "blazed") == 0.0


@pytest.mark.parametrize("kind", ["amplitude", "binary", "blazed"])
def test_fork_order_powers_against_the_closed_form_of_the_thin_mask(kind):
    """v16's default fork (l = 1, w0 = 4 lambda, period 2.5 lambda, 512 points over 131 lambda): each order's share of
    the propagating power, measured in the angular spectrum of the sampled field, against the closed-form spectrum
    of the same thin mask on the same k grid (``order_powers_closed_form``: the orders' q^-2 tails overlap). The
    tolerance is twice the grid's aliasing estimated by the closed form with the grid's periodic images (measured:
    the difference is 1.0-1.7 times that estimate over five forks). Negative controls: the point-sampled binary mask
    is off by more than the tolerance; the ideal |c_m|^2 / sum |c_j|^2 (no overlap) is off by more than 5e-3."""
    l, w0, period, n = 1, 4.0, 2.5, 512
    half = 65.67
    dx = 2 * half / n
    x = (np.arange(n) - n // 2) * dx
    X, Y = np.meshgrid(x, x, indexing="ij")
    G = np.exp(-(X * X + Y * Y) / w0 ** 2)
    M = TM.fork_band(dx, period)
    mm = M if kind == "binary" else 1
    orders = sorted(TM.order_power_reference(kind, period, K))
    meas = TM.order_powers(G * TM.fork_hologram(X, Y, l, period, kind, m_max=M), dx, K, period, orders)
    cf = TM.order_powers_closed_form(kind, l, w0, period, K, dx, n, orders, mm)
    ci = TM.order_powers_closed_form(kind, l, w0, period, K, dx, n, orders, mm, images=1)
    tol = 2 * max(abs(ci[m] - cf[m]) for m in orders) + 1e-5
    dev = max(abs(meas[m] - cf[m]) for m in orders)
    assert dev <= tol, (kind, dev, tol)
    ideal = TM.order_power_reference(kind, period, K)
    assert max(abs(cf[m] - ideal[m]) for m in orders) > 5e-3
    if kind == "binary":
        point = TM.order_powers(G * TM.fork_hologram(X, Y, l, period, kind), dx, K, period, orders)
        assert max(abs(point[m] - cf[m]) for m in orders) > tol


def test_order_leakage_is_the_share_beyond_half_the_period():
    """An order of charge 0 is a plain Gaussian: nothing beyond K/2 for w0 K/2 = 5 (exp(-12.5)); an order of charge 1
    leaks its q^-2 tail (by Parseval the share beyond q0 tends to w^2 int_q0 q^-3 ... ~ 1/(q0 w)^2)."""
    assert TM.order_leakage(1, 0, 4.0, 2.5) < 1e-5
    a, b = TM.order_leakage(1, 1, 4.0, 2.5), TM.order_leakage(1, 1, 8.0, 2.5)
    assert 0.01 < a < 0.3 and 2.5 < a / b < 5.5, (a, b)  # ~ 1/w^2 for large q0 w


# --- the spinning surface -------------------------------------------------------------------------------------------
def test_spinning_surface_on_axis_shift_and_beat():
    """Lavery et al. 2013: the light a spinning rough surface scatters onto the axis is shifted by -l Omega; for an
    incident +l and -l superposition its intensity beats at 2 |l| Omega; for l = 0 it does not beat."""
    w0, Omega = 1.0, 2 * math.pi * 10.0
    x, y, wts = TM.polar_grid(3.5 * w0, 48, 256)
    surf = TM.SpinningSurface(seed=4, n=60, radius=2.0 * w0, height=1.5, size=0.5 * w0)
    for l in (3, -2, 1):
        f_beat = abs(2 * l) * Omega / (2 * math.pi)
        dt = 1 / (8 * f_beat)
        t = np.arange(64) * dt
        Ui = PX.lg(0, l, x, y, 0.0, K, w0)
        a1 = np.array([TM.on_axis_amplitude(Ui, x, y, wts, surf, Omega * ti) for ti in t])
        assert abs(ROT.peak_frequency(a1, dt) - ROT.scattered_on_axis_shift(l, Omega)) < 1e-6 * Omega
        Us = (Ui + PX.lg(0, -l, x, y, 0.0, K, w0)) / math.sqrt(2)
        I = np.abs([TM.on_axis_amplitude(Us, x, y, wts, surf, Omega * ti) for ti in t]) ** 2
        meas = ROT.peak_frequency(I, dt, positive=True, exclude_dc=True)
        assert abs(meas - ROT.superposition_beat(l, Omega)) < 1e-4 * Omega, (l, meas)  # resolution: 8 beats
        assert ROT.modulation_depth(I) > 1e-2
    U0 = PX.lg(0, 0, x, y, 0.0, K, w0)
    I = np.abs([TM.on_axis_amplitude(U0, x, y, wts, surf, Omega * ti) for ti in np.arange(40) * 1e-3]) ** 2
    assert ROT.modulation_depth(I) < 1e-10  # control: no OAM, no beat
