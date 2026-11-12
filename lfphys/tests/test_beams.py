# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Exact beams with orbital angular momentum (core.optics.beams, beams_rotation), each against a closed form or an
independent route, with negative controls where a test checks a tolerance: the Hankel spectra by quadrature; the
source's power by Hankel-Parseval and the share the propagating beam keeps (closed form for an LG waist);
Helmholtz, div E = 0 and curl E = sigma k E by finite differences; Berry's decomposition P = p_o + curl S / 2
pointwise; the angular momenta per photon of the sampled vector field (spectral derivatives on a grid) against the
closed forms from the spectrum — the canonical split per unit length, Barnett's split of the flux, the Poynting
angular momentum — on several planes; the cost guard; the topological charge of sampled fields; the rotational Doppler
shift measured from sampled series. The thin masks (spiral plate, fork hologram, spinning surface) are tested in
test_beams_thin_masks.py."""

import math

import numpy as np
import pytest

from lfphys.core.optics import beams as B
from lfphys.core.optics import beams_rotation as ROT
from lfphys.theories.approx import beams_paraxial as PX

LAM = 1.0
K = 2 * math.pi / LAM


# --- spectra -------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("p,l", [(0, 0), (0, 3), (1, -2), (2, 1)])
def test_lg_waist_spectrum_is_the_hankel_transform_of_the_waist(p, l):
    w0 = 1.3
    fn, qmax = B.lg_waist_spectrum(p, l, w0)
    prof = lambda r: PX.lg(p, l, r, 0.0 * r, 0.0, K, w0)  # noqa: E731  (real at z = 0, phi = 0)
    q = np.linspace(0.0, qmax, 23)
    v, err = B.hankel_transform(prof, l, q, 9 * w0)
    assert np.max(np.abs(v - fn(q))) < 1e-13 and err < 1e-13
    assert abs(fn(qmax)) < 1e-15 * np.max(np.abs(fn(np.linspace(0, qmax, 400))))


@pytest.mark.parametrize("l", [0, 1, -2, 4])
def test_gaussian_vortex_spectrum_is_the_hankel_transform(l):
    w = 1.7
    fn, _ = B.gaussian_vortex_spectrum(l, w)
    q = np.linspace(0.05, 15.0 / w, 31)
    v, err = B.hankel_transform(lambda r: np.exp(-r * r / (w * w)), l, q, 7 * w, panels=400)
    assert np.max(np.abs(v - fn(q))) < 1e-12, np.max(np.abs(v - fn(q)))
    assert np.max(np.abs(v - B.gaussian_vortex_spectrum(l + 1, w)[0](q))) > 1e-2  # negative control: another order


# --- exact solutions -----------------------------------------------------------------------------------------------------
def _d(f, P, h):
    """Fourth-order central first derivatives of f at P along x, y, z: list of 3 arrays."""
    out = []
    for e in np.eye(3):
        out.append((-f(P + 2 * h * e) + 8 * f(P + h * e) - 8 * f(P - h * e) + f(P - 2 * h * e)) / (12 * h))
    return out


def _lap(f, P, h):
    tot = 0
    for e in np.eye(3):
        tot = tot + (-f(P + 2 * h * e) + 16 * f(P + h * e) - 30 * f(P) + 16 * f(P - h * e) - f(P - 2 * h * e)) / (12 * h * h)
    return tot


PTS = np.array([[0.31, -0.42, 0.2], [-0.7, 0.15, -1.3], [0.05, 0.9, 2.4]])


@pytest.mark.parametrize("l,t0", [(0, 0.3), (3, 0.9), (-2, 1.3)])
def test_bessel_beam_satisfies_helmholtz(l, t0):
    for P in PTS:
        f = lambda Q: B.bessel_beam(l, K, t0, Q[0], Q[1], Q[2])  # noqa: E731
        res = abs(_lap(f, P, 2e-3) + K * K * f(P)) / (K * K * max(abs(f(P)), 0.05))
        assert res < 1e-7, res
        g = lambda Q: B.bessel_beam(l, K, t0, Q[0], Q[1], 1.01 * Q[2])  # noqa: E731  wrong k_z
        assert abs(_lap(g, P, 2e-3) + K * K * g(P)) / (K * K * max(abs(g(P)), 0.05)) > 1e-3


def _maxwell_residuals(Efn, sigma, P, h=2e-3):
    E0 = Efn(P)
    d = _d(Efn, P, h)
    div = d[0][0] + d[1][1] + d[2][2]
    curl = np.array([d[1][2] - d[2][1], d[2][0] - d[0][2], d[0][1] - d[1][0]])
    scale = K * np.linalg.norm(E0)
    helm = _lap(Efn, P, h) + K * K * E0
    return abs(div) / scale, np.linalg.norm(curl - sigma * K * E0) / scale, np.linalg.norm(helm) / (K * scale)


@pytest.mark.parametrize("l,sigma,t0", [(0, 1, 0.5), (2, -1, 1.0), (-3, 1, 1.4)])
def test_vector_bessel_beam_is_an_exact_maxwell_field_of_helicity_sigma(l, sigma, t0):
    for P in PTS:
        div, curl, helm = _maxwell_residuals(lambda Q: B.vector_bessel_beam(l, sigma, K, t0, *Q)[0], sigma, P)
        assert div < 1e-8 and curl < 1e-8 and helm < 1e-8, (div, curl, helm)
    # negative control: J_l e^{il phi} e_sigma e^{ikcz} (the scalar Bessel beam times a uniform circular vector)
    bad = lambda Q: B.bessel_beam(l, K, t0, *Q) * np.array([1.0, 1j * sigma, 0.0]) / math.sqrt(2)  # noqa: E731
    assert _maxwell_residuals(bad, sigma, PTS[0])[0] > 1e-2


def test_bessel_cone_per_photon_closed_form():
    for l, s, t0 in [(2, 1, 0.7), (-1, 1, 1.2), (1, -1, 0.3)]:
        d = B.bessel_per_photon(l, s, t0)
        assert d["J"] == l + s and abs(d["S"] - s * math.cos(t0)) < 1e-15 and abs(d["L"] + d["S"] - d["J"]) < 1e-15


@pytest.mark.parametrize("l,sigma", [(2, 1), (1, -1), (-1, 1)])
def test_vortex_vector_beam_is_an_exact_maxwell_field(l, sigma):
    fn, qmax = B.lg_waist_spectrum(0, l, 0.6)
    beam = B.VortexBeam(l, K, fn, qmax, {sigma: 1.0})
    for P in PTS[:2]:
        div, curl, helm = _maxwell_residuals(lambda Q: beam.fields(*Q)[0], sigma, P)
        assert div < 1e-8 and curl < 1e-8 and helm < 1e-8, (div, curl, helm)
    E, H = beam.fields(*PTS[2])
    assert np.allclose(H, -1j * sigma * E)
    (F, err) = beam.radial(np.array([0.4, 1.1]), np.array([0.3, -0.8]), sigma, estimate=True)
    assert err < 1e-13


def test_berry_decomposition_pointwise():
    """P = p_o + (1/2) curl S (Berry 2009 Eq. 3.5; Bliokh et al. 2013 Eqs. 3.27, 3.43) at points of a vector Bessel
    beam and of a superposition of both helicities (E and H no longer proportional), with gradients by differences."""
    h = 1e-3

    def fields(Q):
        E1, H1 = B.vector_bessel_beam(2, 1, K, 0.8, *Q)
        E2, H2 = B.vector_bessel_beam(0, -1, K, 1.1, *Q)
        return E1 + 0.7 * E2, H1 + 0.7 * H2
    for P in PTS:
        E, H = fields(P)
        gE = np.stack(_d(lambda Q: fields(Q)[0], P, h), axis=1)  # (3 comps, 3 dirs)
        gH = np.stack(_d(lambda Q: fields(Q)[1], P, h), axis=1)
        po = B.orbital_momentum(E, H, gE, gH, K)
        dS = _d(lambda Q: B.spin_density(*fields(Q), K), P, h)
        curlS = np.array([dS[1][2] - dS[2][1], dS[2][0] - dS[0][2], dS[0][1] - dS[1][0]])
        Pv = B.poynting(E, H)
        assert np.linalg.norm(Pv - po - 0.5 * curlS) < 1e-9 * np.linalg.norm(Pv) + 1e-12
        assert np.linalg.norm(Pv - po) > 1e-3 * np.linalg.norm(Pv)  # the spin part is not negligible here


def _plane(beam, z, n=72, half=5.5):
    x = (np.arange(n) - n // 2) * (2 * half / n)
    X, Y = np.meshgrid(x, x, indexing="ij")
    E, H = beam.fields(X, Y, z)
    Ez, Hz = beam.fields(X, Y, z, deriv_z=True)
    dx = float(x[1] - x[0])
    gE = np.stack([np.stack(B.spectral_gradient(E[i], dx, dx) + (Ez[i],)) for i in range(3)])
    gH = np.stack([np.stack(B.spectral_gradient(H[i], dx, dx) + (Hz[i],)) for i in range(3)])
    return B.angular_momentum(x, x, E, H, gE, gH, K)


@pytest.mark.parametrize("l,sigma", [(2, 1), (2, -1), (-1, 1)])
def test_vector_beam_angular_momentum_per_photon(l, sigma):
    """Tight beam (w0 = 1.2 lambda, the spectrum negligible at q = k): from the sampled E and H on a transverse plane,
    canonical L_z + S_z = l + sigma, S_z = sigma <cos theta>, L_z = l + sigma (1 - <cos theta>), the energy flux over
    the energy per unit length = <cos theta>, and the angular-momentum flux over the energy flux = (l + sigma)/omega
    (Maxwell stress) — against the closed forms from the spectrum."""
    fn, qmax = B.lg_waist_spectrum(0, l, 1.2)
    beam = B.VortexBeam(l, K, fn, qmax, {sigma: 1.0})
    ref = beam.moments()
    am = _plane(beam, 0.4)
    for key in ("J", "S", "L", "flux_over_energy", "flux_J"):
        assert abs(am[key] - ref[key]) < 1e-8, (key, am[key], ref[key])
    assert abs(am["J"] - (l + sigma)) < 1e-8 and abs(am["flux_J"] - (l + sigma)) < 1e-8
    assert 0.02 < sigma * (sigma - am["S"]) < 0.2  # the spin-orbit split is real (not the paraxial S_z = sigma)


_PLANES = {}


def _focused_plane(amp: tuple, z: float):
    """The plane z of the l = 2, w0 = 1.2 lambda beam with helicity amplitudes ``amp`` (a tuple of (sigma, a)), cached:
    the window grows with w(z) (7 w(z) wide; measured window error 1e-9 at the waist, 3e-7 at z_R)."""
    key = (amp, z)
    if key not in _PLANES:
        w0 = 1.2
        fn, qmax = B.lg_waist_spectrum(0, 2, w0)
        beam = B.VortexBeam(2, K, fn, qmax, dict(amp))
        wz = w0 * math.sqrt(1 + (z / PX.rayleigh(K, w0)) ** 2)
        half = max(6.0, 5.0 * wz)
        _PLANES[key] = (beam, _plane(beam, z, 2 * int(math.ceil(6.0 * half)), half))
    return _PLANES[key]


_AMPS = (((1, 1.0),), ((-1, 1.0),), ((1, 0.6), (-1, 0.8)))


def test_poynting_angular_momentum_closed_form_on_every_plane():
    """int (r x P)_z dA = L_z + S_z + (1/2) d/dz int r.S_T dA (the spin current's moment; the identity measured with a
    difference quotient), and per photon it is J + (sigma_bar/2) <sin^2 theta / cos theta> on every plane: at the
    waist (where the beam neither converges nor diverges), near it and at z_R, for both helicities and a mixture
    (review B8-beams, O4). Tolerance: the plane's window error (1e-8 near the waist, 1e-6 at z_R; measured 1e-9 and
    3e-7). Negative control: the reference without the extra term (L_z + S_z = l + sigma) is off by > 4e-2 sigma_bar.
    The energy per unit length on the same planes against Parseval (``energy_per_length``)."""
    l, zr = 2, PX.rayleigh(K, 1.2)
    cases = [(_AMPS[0], 0.3), (_AMPS[0], 0.4), (_AMPS[0], 0.5), (_AMPS[0], zr), (_AMPS[1], 0.0), (_AMPS[2], 0.0)]
    for amp, z in cases:
        beam, am = _focused_plane(amp, z)
        ref = beam.moments()
        sb = ref["sigma_mean"]
        assert abs(ref["J_poynting"] - (l + sb + 0.5 * sb * ref["sin2_over_cos"])) < 1e-14
        tol = 1e-6 if z > 1 else 1e-8
        assert abs(am["J_poynting_per_photon"] - ref["J_poynting"]) < tol, (amp, z, am["J_poynting_per_photon"])
        assert abs(am["J_poynting_per_photon"] - (l + sb)) > 4e-2 * abs(sb)  # negative control
        assert abs(am["W"] / beam.energy_per_length() - 1) < tol
        assert abs(ref["W"] - beam.energy_per_length()) < 1e-15
    (_, a), (_, mid), (_, b) = (_focused_plane(_AMPS[0], z) for z in (0.3, 0.4, 0.5))
    rhs = mid["Lz"] + mid["Sz"] + 0.5 * (b["rS"] - a["rS"]) / 0.2
    assert abs(mid["J_poynting"] - rhs) < 1e-7 * abs(mid["J_poynting"])


def test_barnett_flux_split_against_the_canonical_split():
    """Barnett's split of the angular-momentum flux (Monteiro et al. 2009, Eq. 33: spin flux sigma/(2 omega) int |E_T|^2
    for one helicity), measured on planes from -Im(E_T* . H_T)/(2 omega), against the closed form sigma_bar <(1 + c^2)/2>
    / <c>; it does not depend on z; with the canonical split it shares only J = l + sigma, and its spin moves away
    from sigma on the other side (|S_flux| > 1 > |S|; review B8-beams, O3). Negative control: the canonical S as the
    reference of the flux split is off by > 4e-2 sigma_bar. Tolerance: the window error, as above (1e-9 near the waist,
    1e-6 at z_R: measured 1.1e-7 there for the orbital part)."""
    l, zr = 2, PX.rayleigh(K, 1.2)
    for amp, z in [(_AMPS[0], 0.4), (_AMPS[0], zr), (_AMPS[1], 0.0), (_AMPS[2], 0.0)]:
        beam, am = _focused_plane(amp, z)
        ref = beam.moments()
        sb = ref["sigma_mean"]
        tol = 1e-6 if z > 1 else 1e-9
        assert abs(am["flux_S"] - ref["S_flux"]) < tol and abs(am["flux_L"] - ref["L_flux"]) < tol, (amp, z, am)
        assert abs(am["flux_S"] + am["flux_L"] - (l + sb)) < 10 * tol
        assert abs(am["flux_S"] - ref["S"]) > 4e-2 * abs(sb)  # negative control: not the canonical spin
        if abs(sb) == 1:
            assert abs(ref["S_flux"]) > 1 > abs(ref["S"])
            assert sb * (ref["S_flux"] - sb) > 0 > sb * (ref["S"] - sb)
    # the paraxial limit: both splits tend to (l, sigma)
    fn, qmax = B.lg_waist_spectrum(0, l, 8.0)
    m = B.VortexBeam(l, K, fn, qmax, {1: 1.0}).moments()
    assert abs(m["S_flux"] - 1) < 1e-4 and abs(m["S"] - 1) < 2e-3


@pytest.mark.parametrize("p,l,w0,lam", [(0, 1, 0.6, 1.0), (0, 1, 0.3, 1.0), (0, 3, 0.3, 1.0), (0, 1, 0.3, 1.6),
                                        (0, 3, 1.5, 1.0)])
def test_propagating_fraction_of_an_lg_waist(p, l, w0, lam):
    """The share of an LG_{0,l} waist's power the propagating beam keeps: 1 - Q(|l| + 1, (k w0)^2 / 2) (regularised
    upper incomplete gamma: |A|^2 q dq ~ t^|l| e^-t dt, t = (q w0)^2 / 2); the total is 1 (the waist is normalised;
    Hankel-Parseval). Review B8-beams, O2: LG_{0,1} at w0 = 0.6 lambda loses 0.7 %, at 0.3 lambda 47 %."""
    from scipy.special import gammaincc
    k = 2 * math.pi / lam
    fn, qmax = B.lg_waist_spectrum(p, l, w0)
    beam = B.VortexBeam(l, k, fn, qmax)
    fr, err = beam.propagating_fraction()
    ref = gammaincc(abs(l) + 1, (k * w0) ** 2 / 2)
    assert abs((1 - fr) - ref) < 1e-12 + 1e-9 * ref and err < 1e-12, (1 - fr, ref, err)
    assert abs(2 * math.pi * beam.spectrum_power()[0] - 1.0) < 1e-13
    # negative control: the order |l| + 2 in the closed form is far off where anything is dropped
    if ref > 1e-6:
        assert abs((1 - fr) - gammaincc(abs(l) + 2, (k * w0) ** 2 / 2)) > 0.05 * ref


def test_spectrum_power_without_cut_off_is_parseval():
    """A Gaussian behind a spiral plate has |A| ~ q^-2 and no cut-off: its total int |A|^2 q dq over [0, inf) equals
    int |U0|^2 r dr = w^2 / 4 (Hankel-Parseval); the share beyond k is what the exact vector beam drops."""
    for l, w, lam in ((2, 1.5, 1.0), (6, 0.3, 1.6), (1, 4.0, 1.0)):
        k = 2 * math.pi / lam
        fn, qmax = B.gaussian_vortex_spectrum(l, w)
        beam = B.VortexBeam(l, k, fn, qmax)
        tot, err = beam.spectrum_power()
        assert abs(tot / (w * w / 4) - 1) < 1e-10 and err < 1e-10 * tot, (l, w, tot, err)
        fr, _ = beam.propagating_fraction()
        assert 0 < 1 - fr < 1
        assert abs(beam.spectrum_power(0, k)[0] + beam.spectrum_power(k)[0] - tot) < 1e-10 * tot


def test_gaussian_vortex_spectrum_far_tail_and_the_asymptotic_branch():
    """Beyond x = q^2 w^2 / 8 = 1e6 the spectrum uses the asymptotic series of I_{(n-1)/2} e^-x - I_{(n+1)/2} e^-x
    (SciPy's ive returns NaN near x = 1e10): it matches ive where both hold (x = 1e4 .. 1e6, orders up to 42 as in a
    fork's band; the reference's own cancellation, 4 eps ive, bounds the difference there) and the tail is finite and
    tends to the leading term n / (2 x sqrt(2 pi x)), i.e. A ~ q^-2."""
    from scipy.special import ive
    x = np.logspace(4, 6, 9)
    for n in (1, 2, 5, 12, 42):
        ia = ive((n - 1) / 2.0, x)
        ref = ia - ive((n + 1) / 2.0, x)
        # the reference loses digits to cancellation: |ref| ~ n / (2x) of ive itself, round-off 4 eps of ive
        tol = 1e-12 * np.abs(ref) + 4 * np.finfo(float).eps * ia
        assert np.all(np.abs(B._ive_diff_asymptotic(n, x) - ref) < tol), n
    fn, _ = B.gaussian_vortex_spectrum(3, 1.5)
    q = np.array([1e4, 1e6, 1e8])
    v = fn(q)
    assert np.all(np.isfinite(v))
    xx = q * q * 1.5 ** 2 / 8
    lead = math.sqrt(math.pi) * q * 1.5 ** 3 / 8 * 3 / (2 * xx * np.sqrt(2 * math.pi * xx))
    assert np.max(np.abs(v / lead - 1)) < 1e-6


def test_evanescent_fraction_by_an_independent_quadrature():
    """The share of the source's power its evanescent waves still carry at z: 1 - propagating_fraction at z = 0,
    falling with z; against scipy's adaptive quadrature of int_k |A|^2 exp(-2 sqrt(q^2 - k^2) z) q dq (LG_{0,1} at
    w0 = 0.6 lambda, the tight preset)."""
    from scipy.integrate import quad
    fn, qmax = B.lg_waist_spectrum(0, 1, 0.6)
    beam = B.VortexBeam(1, K, fn, qmax)
    assert abs(beam.evanescent_fraction(0.0) - (1 - beam.propagating_fraction()[0])) < 1e-14
    tot = 1 / (2 * math.pi)
    vals = []
    for z in (0.05, 0.2, 1.0):
        f = lambda q: float(abs(fn(np.array([q]))[0]) ** 2) * q * math.exp(-2 * math.sqrt(max(q * q - K * K, 0)) * z)  # noqa: E731
        ref = quad(f, K, qmax, limit=400, epsabs=1e-16, epsrel=1e-11)[0] / tot
        vals.append(beam.evanescent_fraction(z))
        assert abs(vals[-1] - ref) < 1e-9 * ref + 1e-15, (z, vals[-1], ref)
    assert vals[0] > vals[1] > vals[2] > 0


def test_cost_is_sized_before_the_matrices_are_built():
    """table_cost gives the node count the table uses; a request beyond max_elements is refused with the estimate
    before anything is allocated; the scalar route for a spectrum without cut-off as z_min -> 0+ (its evanescent node
    count ~ 1/z_min) is refused, not run out of memory (review B8-beams, O5, O15)."""
    fn, qmax = B.lg_waist_spectrum(0, 2, 1.2)
    beam = B.VortexBeam(2, K, fn, qmax, {1: 1.0})
    r, z = np.linspace(0, 6, 50), np.linspace(-3, 3, 7)
    cost = beam.table_cost(len(r), 6.0, 3.0, len(z))
    th, _ = beam._prop_nodes(6.0, 3.0, 2)
    assert cost["nq"] == len(th) and cost["elements"] == len(r) * len(th)
    beam.table(r, z, 1, estimate=True)  # within the budget
    small = B.VortexBeam(2, K, fn, qmax, {1: 1.0}, max_elements=cost["elements"] / 2)
    with pytest.raises(ValueError, match="max_elements"):
        small.table(r, z, 1, estimate=True)
    fs, qs = B.gaussian_vortex_spectrum(3, 2.0)
    spp = B.VortexBeam(3, K, fs, qs)
    spp.scalar(np.array([0.5, 1.0]), 0.5)  # fine at z = 0.5
    with pytest.raises(ValueError, match="max_elements"):
        spp.scalar(np.linspace(0.1, 10.0, 100), 1e-4)


def test_paraxial_limit_of_the_vector_beam():
    """w0 = 6 lambda: S_z -> sigma and L_z -> l per photon (to 1 - <cos theta> ~ 1e-3); the transverse field -> LG
    e_sigma to second order in 1/(k w0); the longitudinal field E_z is of first order (here l + sigma = 0: E_z is
    largest on the axis, where the transverse field vanishes)."""
    l, sigma, w0 = 1, -1, 6.0
    fn, qmax = B.lg_waist_spectrum(0, l, w0)
    beam = B.VortexBeam(l, K, fn, qmax, {sigma: 1.0})
    m = beam.moments()
    assert 0 < 1 - m["cos_mean"] < 2e-3 and abs(m["S"] - sigma) < 2e-3
    r = np.array([0.5, 4.0, 7.0])
    E, H = beam.fields(r, 0 * r, 0.0)
    lg = PX.lg(0, l, r, 0 * r, 0.0, K, w0)
    e = np.array([1.0, 1j * sigma, 0.0])[:, None] / math.sqrt(2)
    peak = np.max(np.abs(lg))
    assert np.max(np.abs(E[:2] - lg * e[:2])) < 3e-3 * peak
    ez = np.max(np.abs(E[2])) / peak
    assert 1.0 / (K * w0) < ez < 5.0 / (K * w0), ez  # measured 3.26 / (k w0)


# --- topological charge ------------------------------------------------------------------------------------------------
def test_topological_charge_of_sampled_fields():
    w0 = 1.0
    f = lambda x, y: PX.lg(0, 3, x, y, 0.5, K, w0)  # noqa: E731
    assert abs(B.charge_on_circle(f, 0, 0, 0.8) - 3) < 1e-12
    x = np.linspace(-3, 3, 201)
    X, Y = np.meshgrid(x, x, indexing="ij")
    # LG_{0,2} plus a little LG_{0,0}: the double vortex splits into two unit vortices off the axis
    U = PX.lg(0, 2, X, Y, 0, K, w0) + 0.3 * PX.lg(0, 0, X, Y, 0, K, w0)
    q = B.plaquette_charges(U)
    assert int(np.sum(q[q != 0])) == 2 and np.count_nonzero(q) == 2 and q.max() == 1
    assert B.charge_in_disc(U, x, x, 0, 0, 1.5) == 2
    assert B.charge_in_disc(U, x, x, 2.0, 2.0, 0.5) == 0  # negative control: a disc without a vortex
    assert B.charge_in_disc(np.abs(U) + 0j, x, x, 0, 0, 1.5) == 0  # negative control: the phase removed
    assert abs(B.charge_on_circle(lambda a, b: PX.lg(0, -4, a, b, 0, K, w0), 0, 0, 1.0) + 4) < 1e-12


# --- rotational Doppler -----------------------------------------------------------------------------------------------
def test_rotating_observer_measures_omega_minus_m_Omega():
    omega, Omega, n = 50.0, 3.0, 4096
    dt = 2 * math.pi / omega / 16
    t = np.arange(n) * dt
    for l, sigma in [(2, 1), (3, -1), (-1, 1), (1, -1)]:
        fn = lambda xx, yy, zz: B.vector_bessel_beam(l, sigma, K, 0.6, xx, yy, zz)[0]  # noqa: E731
        s = ROT.sample_rotating(fn, 0.4, 0.3, 0.2, Omega, omega, t)
        for comp in (0, 2):
            meas = ROT.peak_frequency(s[comp], dt)
            ref = ROT.rotating_frame_frequency(omega, l + sigma, Omega)
            assert abs(meas - ref) < 1e-4 * Omega, (l, sigma, comp, meas, ref)
    # control: l = sigma = 0 (a scalar Bessel beam): no shift
    s = ROT.sample_rotating(lambda xx, yy, zz: B.bessel_beam(0, K, 0.6, xx, yy, zz), 0.4, 0.3, 0.2, Omega, omega, t)
    assert abs(ROT.peak_frequency(s, dt) - omega) < 1e-4 * Omega


@pytest.mark.parametrize("vector", [True, False])
def test_turned_image_rotator_shifts_by_m_out_times_the_beam_rotation(vector):
    """Two arms: one through a rotator at rest, one through a rotator turning at Omega_p (the beam turns at
    2 Omega_p); the power on a detector beats at |m_out| 2 Omega_p (m_out = -(l + sigma), or -l for the scalar
    rotator); l = 0 through the scalar rotator: no beat."""
    Op, n = 2.0, 512
    dt = 2 * math.pi / (2 * Op) / 64
    t = np.arange(n) * dt
    xs = np.linspace(-1.5, 1.5, 21)
    X, Y = np.meshgrid(xs, xs, indexing="ij")

    def source(l, sigma):  # the vector Bessel beam, or for the scalar rotator the scalar one
        if vector:
            return lambda xx, yy, zz: B.vector_bessel_beam(l, sigma, K, 0.5, xx, yy, zz)[0]
        return lambda xx, yy, zz: B.bessel_beam(l, K, 0.5, xx, yy, zz)
    for l, sigma in [(2, 1), (3, -1), (0, 1)]:
        src = source(l, sigma)
        ref = ROT.image_rotator(src, 0.0, vector)(X, Y, 0.0)
        P = [np.sum(np.abs(ref + ROT.image_rotator(src, Op * ti, vector)(X, Y, 0.0)) ** 2) for ti in t]
        m_out = -(l + sigma) if vector else -l
        if m_out == 0:
            assert ROT.modulation_depth(P) < 1e-10
            continue
        meas = ROT.peak_frequency(P, dt, positive=True, exclude_dc=True)
        assert abs(meas - abs(m_out) * 2 * Op) < 1e-3 * Op, (l, sigma, vector, meas)
    # the frequency itself (not only the beat): the turned arm alone, sampled at a point
    l, sigma = 2, 1
    src = source(l, sigma)
    omega = 40.0
    a = np.array([np.ravel(ROT.image_rotator(src, Op * ti, vector)(0.3, 0.2, 0.0))[0] for ti in t]) * np.exp(-1j * omega * t)
    m_out = -(l + sigma) if vector else -l
    assert abs(ROT.peak_frequency(a, dt) - ROT.rotated_beam_frequency(omega, m_out, 2 * Op)) < 1e-3 * Op


def test_radial_table_interpolates_the_exact_and_the_paraxial_beam():
    """The tabulated beam (bicubic splines of the envelopes, the carrier e^{ikz} exact) against the direct quadrature
    (exact vector beam) and the closed form (paraxial LG): the interpolation error is small and falls with the grid
    (fourth order); a table on a coarser grid is measurably worse (the measure is not blind)."""
    l, sigma, w0 = 2, 1, 0.9
    fn, qmax = B.lg_waist_spectrum(0, l, w0)
    beam = B.VortexBeam(l, K, fn, qmax, {sigma: 1.0})
    rng = np.random.default_rng(3)
    pts = rng.uniform(-1, 1, (3, 40)) * np.array([[2.5], [2.5], [2.0]])
    errs = []
    for nr, nz in ((120, 60), (240, 120)):
        r = np.linspace(0, 4.0, nr)
        z = np.linspace(-2.2, 2.2, nz)
        T = B.RadialTable(r, z, K, l, {sigma: beam.table(r, z, sigma)}, {sigma: 1.0})
        errs.append(T.max_error(lambda a, b, c: beam.fields(a, b, c)[0], *pts))
    assert errs[1] < 1e-5 and errs[0] / errs[1] > 8, errs
    p = 1
    zr = PX.rayleigh(K, 2.0)
    r = np.linspace(0, 9.0, 300)
    z = np.linspace(-1.5 * zr, 1.5 * zr, 120)
    Z, R = np.meshgrid(z, r, indexing="ij")
    F0 = PX.lg(p, l, R, 0 * R, Z, K, 2.0) * np.exp(1j * K * Z)
    T = B.RadialTable(r, z, K, l, {1: np.stack([F0, 0 * F0, 0 * F0])}, {1: 1.0})
    pts = rng.uniform(-1, 1, (3, 40)) * np.array([[5.0], [5.0], [1.4 * zr]])
    e = np.array([1.0, 1j, 0.0])[:, None] / math.sqrt(2)
    direct = lambda a, b, c: PX.lg(p, l, a, b, c, K, 2.0) * np.exp(1j * K * c) * e  # noqa: E731
    assert T.max_error(direct, *pts) < 1e-6
