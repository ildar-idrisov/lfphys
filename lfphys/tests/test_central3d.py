# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Three-dimensional wave functions of a central field (plan P14.5, P14.9): ``core.quantum.central3d`` and the radial
functions it is fed with (``hydrogen.radial``, ``radial.wavefunctions`` through ``RadialTable``). Every route against a
closed form or an independent method: scipy's spherical harmonics, the Cartesian forms of the real orbitals, the
quadrature rules on monomials, Bethe & Salpeter's dipole matrix element, the azimuthal current in closed form and the
continuity equation, the hydrogen closed form for the tabulated route, the 3-D grid eigenstates of
``schrodinger_nd`` (measured overlaps)."""

import math

import numpy as np
import pytest
from scipy import special

from lfphys.core.quantum import central3d as C, hydrogen as H, radial, schrodinger_nd as S

rng = np.random.default_rng(14)
EPS = np.finfo(float).eps


def _points(n=400, scale=6.0):
    return rng.normal(0.0, scale, (3, n))


# --- spherical harmonics ---------------------------------------------------------------------------------------------
def test_harmonics_match_scipy_with_the_condon_shortley_phase():
    """Both are three-term recurrences with ~l eps round-off per step (measured: 9e-14 at l <= 12, 4e-14 at l = 80)."""
    th, ph = rng.uniform(0, math.pi, 600), rng.uniform(-math.pi, math.pi, 600)
    th[:4] = [0.0, math.pi, 1e-9, math.pi - 1e-9]  # the poles
    for l in list(range(13)) + [40, 80]:
        for m in (range(-l, l + 1) if l <= 12 else (-l, -7, 0, 3, l)):
            d = np.max(np.abs(C.sph_harm(l, m, th, ph) - special.sph_harm_y(l, m, th, ph)))
            assert d < 1e-12 * (l + 1), (l, m, d)


def test_harmonics_are_orthonormal_on_the_exact_product_rule():
    T, P, W = C.angular_quadrature(4)
    for real in (False, True):
        lm = [(l, m) for l in range(5) for m in range(-l, l + 1)]
        Y = np.array([C.real_harm(l, m, T, P) if real else C.sph_harm(l, m, T, P) for l, m in lm])
        G = (np.conj(Y) * W) @ Y.T
        assert np.max(np.abs(G - np.eye(len(lm)))) < 1e-14


def test_real_orbitals_are_the_cartesian_forms():
    """p_x = sqrt(3/4pi) x/r, d_xy = sqrt(15/4pi) xy/r^2, d_z2 = sqrt(5/16pi)(3z^2 - r^2)/r^2, d_x2-y2 =
    sqrt(15/16pi)(x^2 - y^2)/r^2, p_y, p_z, d_xz, d_yz: the chemists' orbitals, positive lobes along +x, +y, +z."""
    x, y, z = _points(300)
    r, th, ph = C.spherical(x, y, z)
    ref = {(1, 1): math.sqrt(3 / (4 * math.pi)) * x / r, (1, -1): math.sqrt(3 / (4 * math.pi)) * y / r,
           (1, 0): math.sqrt(3 / (4 * math.pi)) * z / r, (2, -2): math.sqrt(15 / (4 * math.pi)) * x * y / r**2,
           (2, 1): math.sqrt(15 / (4 * math.pi)) * x * z / r**2, (2, -1): math.sqrt(15 / (4 * math.pi)) * y * z / r**2,
           (2, 0): math.sqrt(5 / (16 * math.pi)) * (3 * z * z - r * r) / r**2,
           (2, 2): math.sqrt(15 / (16 * math.pi)) * (x * x - y * y) / r**2}
    for (l, m), f in ref.items():
        assert np.max(np.abs(C.real_harm(l, m, th, ph) - f)) < 1e-14, (l, m)
    # the complex m = +1 state is -(p_x + i p_y)/sqrt 2 (Condon-Shortley)
    assert np.max(np.abs(C.sph_harm(1, 1, th, ph) + (ref[(1, 1)] + 1j * ref[(1, -1)]) / math.sqrt(2))) < 1e-14


def test_names_and_edges(ru):
    assert C.orbital_name(0, 0, True) == "s" and C.orbital_name(2, 2, True) == "d_x²−y²"
    assert C.orbital_name(1, -1, False) == "p, m = -1" and "m = +4" in C.orbital_name(5, 4, True)
    # a real orbital without a Cartesian name is named by its azimuthal factor: a symbol, the same in every language
    assert C.orbital_name(5, 4, True) == "h, m = +4 (cos)" and C.orbital_name(4, -3, True) == "g, m = -3 (sin)"
    with pytest.raises(ValueError, match="need 0 ≤ m ≤ l") as e:
        C.legendre_normalised(2, 3, 0.5)
    assert ru(e.value.args[0]) == "нужно 0 ≤ m ≤ l"
    r, th, ph = C.spherical(0.0, 0.0, 0.0)
    assert r == 0 and th == 0  # the origin: theta = 0 by convention, Y finite
    assert np.isfinite(C.sph_harm(3, 2, th, ph))


# --- quadrature rules --------------------------------------------------------------------------------------------------
def test_angular_rule_is_exact_on_monomials():
    """int x^a y^b z^c dOmega = 2 G((a+1)/2) G((b+1)/2) G((c+1)/2) / G((a+b+c+3)/2) for even a, b, c (else 0); the
    rule of l_max is exact up to degree 2 l_max + 4."""
    T, P, W = C.angular_quadrature(3)
    x, y, z = np.sin(T) * np.cos(P), np.sin(T) * np.sin(P), np.cos(T)
    for a in range(11):
        for b in range(11 - a):
            for c in range(11 - a - b):
                q = float(np.sum(W * x**a * y**b * z**c))
                ref = 0.0 if (a % 2 or b % 2 or c % 2) else 2 * math.gamma((a + 1) / 2) * math.gamma((b + 1) / 2) * \
                    math.gamma((c + 1) / 2) / math.gamma((a + b + c + 3) / 2)
                assert abs(q - ref) < 1e-13, (a, b, c, q, ref)


def test_dipole_matrix_elements_of_hydrogen():
    """<1s|z|2p0> = 2^7 sqrt 2 / 3^5 a (Bethe & Salpeter); <1s|x|2p_x> the same; <1s|(x, y, z)|2p, m = +1> =
    d (-1/sqrt 2, -i/sqrt 2, 0) (Condon-Shortley); 1s-2s: zero by parity."""
    d = H.DIPOLE_1S_2P0
    s1 = H.orbital(1, 0, 0)
    assert np.allclose(C.dipole(s1, H.orbital(2, 1, 0), 60.0), [0, 0, d], atol=1e-13, rtol=0)
    assert np.allclose(C.dipole(s1, H.orbital(2, 1, 1, real=True), 60.0), [d, 0, 0], atol=1e-13, rtol=0)
    assert np.allclose(C.dipole(s1, H.orbital(2, 1, 1), 60.0), [-d / math.sqrt(2), -1j * d / math.sqrt(2), 0],
                       atol=1e-13, rtol=0)
    assert np.max(np.abs(C.dipole(s1, H.orbital(2, 0, 0), 60.0))) < 1e-15


# --- the current -------------------------------------------------------------------------------------------------------
def test_current_of_a_complex_state_is_the_azimuthal_closed_form():
    """Centred differences of step h (truncation ~ h^2 |psi'''| / 6, round-off ~ eps |psi| / h) against
    j = (hbar m / mu) |psi|^2 (-y, x, 0) / rho^2; a real orbital carries no current at all."""
    x, y, z = _points(500, 4.0)
    for n, l, m in ((2, 1, 1), (3, 2, -2), (4, 3, 2)):
        o = H.orbital(n, l, m)
        jf, jc = C.current(o, x, y, z), C.azimuthal_current(o, x, y, z)
        assert np.max(np.abs(jf - jc)) < 1e-8 * np.max(np.abs(jc)), (n, l, m)
        assert np.max(np.abs(C.current(H.orbital(n, l, m, real=True), x, y, z))) == 0.0
    o = H.orbital(3, 2, 2, Z=2.0)  # mu and hbar scale it
    assert np.allclose(C.azimuthal_current(o, x, y, z, mu=0.5, hbar=2.0), 4 * C.azimuthal_current(o, x, y, z))


def test_closed_form_current_is_divergence_free():
    """div j by centred differences of step h: O(h^2), so halving h divides it by ~4 (here: the measured ratio)."""
    o = H.orbital(3, 2, 1)
    x, y, z = _points(200, 3.0)
    x = np.where(np.hypot(x, y) < 0.3, x + 0.6, x)  # away from the axis, where j ~ 1/rho
    jmax = np.max(np.abs(C.azimuthal_current(o, x, y, z)))

    def div(h):
        f = lambda a, b, c, i: C.azimuthal_current(o, a, b, c)[i]  # noqa: E731
        return ((f(x + h, y, z, 0) - f(x - h, y, z, 0)) + (f(x, y + h, z, 1) - f(x, y - h, z, 1)) +
                (f(x, y, z + h, 2) - f(x, y, z - h, 2))) / (2 * h)
    d1, d2 = np.max(np.abs(div(2e-3))), np.max(np.abs(div(1e-3)))
    assert d2 < 1e-5 * jmax and 3.0 < d1 / d2 < 5.0, (d1, d2, jmax)


def test_superposition_obeys_continuity_and_oscillates_at_the_bohr_frequency():
    """(1s + 2p0)/sqrt 2: d rho/dt + div j = 0 by centred differences: j with step h_j, its divergence with step h,
    time with step h_t; tolerance = their truncation (h^2 + h_j^2 + h_t^2) x 10 max|d rho/dt| (derivatives of order
    1/a) plus the round-off of the nested differences 4 eps max rho / (h_j h). <z>(t) by 3-D quadrature (radial
    Gauss-Legendre panels x the exact angular rule) = d cos(3t/8), d = 2^7 sqrt 2 / 3^5."""
    sp = C.Superposition([H.orbital(1, 0, 0), H.orbital(2, 1, 0)])
    assert sp.frequencies() == [pytest.approx(3 / 8, abs=1e-15)]
    x, y, z = _points(300, 3.0)
    t, h, hj, ht = 1.3, 1e-3, 1e-5, 1e-4
    rho = lambda tt, a=x, b=y, c=z: np.abs(sp.psi(a, b, c, tt)) ** 2  # noqa: E731
    drho = (rho(t + ht) - rho(t - ht)) / (2 * ht)
    jx = lambda a, b, c: C.current(sp, a, b, c, t, h=hj)  # noqa: E731
    div = ((jx(x + h, y, z)[0] - jx(x - h, y, z)[0]) + (jx(x, y + h, z)[1] - jx(x, y - h, z)[1]) +
           (jx(x, y, z + h)[2] - jx(x, y, z - h)[2])) / (2 * h)
    tol = (h * h + hj * hj + ht * ht) * 10 * np.max(np.abs(drho)) + 4 * EPS * np.max(rho(t)) / (hj * h)
    assert np.max(np.abs(drho + div)) < tol, (np.max(np.abs(drho + div)), tol)
    assert np.max(np.abs(drho)) > 1e4 * tol  # the test can fail: a wrong phase would leave ~ |d rho/dt|
    r, wr = C.radial_quadrature(60.0, 300)
    T, P, W = C.angular_quadrature(4)
    R3, T3 = r[:, None], T[None, :]
    X, Y, Z = R3 * np.sin(T3) * np.cos(P), R3 * np.sin(T3) * np.sin(P), R3 * np.cos(T3)
    w = wr[:, None] * r[:, None] ** 2 * W[None, :]
    for tt in (0.0, 2.0, 5.0, 8.0, 16.0):
        dens = np.abs(sp.psi(X, Y, Z, tt)) ** 2
        assert abs(np.sum(w * dens) - 1.0) < 1e-12
        assert abs(np.sum(w * dens * Z) - H.DIPOLE_1S_2P0 * math.cos(3 * tt / 8)) < 1e-12, tt


def test_px_plus_i_py_is_the_stationary_m1_state():
    sp = C.Superposition([H.orbital(2, 1, 1, real=True), H.orbital(2, 1, -1, real=True)], [1.0, 1j])
    x, y, z = _points(200, 5.0)
    assert sp.frequencies() == []
    assert np.max(np.abs(sp.psi(x, y, z, 3.0) + H.orbital(2, 1, 1).psi(x, y, z) * np.exp(1j * 3.0 / 8))) < 1e-15


# --- tabulated radial functions (the radial solver) ----------------------------------------------------------------------
def test_radial_wavefunctions_reach_their_measured_accuracy():
    """-1/r, box 100, N = 800 against the closed form on the returned grid, max |u - u_exact| / max |u|: l = 0
    extrapolated 2.6e-4 (the fine grid alone: 2.8e-3), l = 1 1.1e-4 (largest at the first point; 3.5e-5 on every
    other point); the returned estimate (coarse vs fine grid) bounds the returned u's error."""
    V = lambda r: -1.0 / r  # noqa: E731
    for l, lim in ((0, 4e-4), (1, 1.5e-4)):
        E, r, u, est = radial.wavefunctions(V, l, 1.0, 100.0, N=800, n_states=2)
        for k in range(2):
            ex = H.radial(l + 1 + k, l, r) * r
            err = np.max(np.abs(u[:, k] - ex)) / np.max(np.abs(ex))
            assert err < lim and err < est[k], (l, k, err, est[k])
            assert abs(E[k] + 0.5 / (l + 1 + k) ** 2) < 3e-4
        assert abs(np.sum(u[:, 0] ** 2) * (r[1] - r[0]) - 1.0) < 1e-12


def test_radial_table_against_the_hydrogen_closed_form():
    """Box 40, N = 800: max |R_table - R| / max |R| = 4.2e-4 (1s), 3.1e-4 (2p), measured; R(0) of 1s within 1e-3 of
    2; zero beyond the box; a table too short to extrapolate is refused."""
    x = np.linspace(0.0, 30.0, 6001)
    for l, lim in ((0, 6e-4), (1, 5e-4)):
        E, r, u, _ = radial.wavefunctions(lambda q: -1.0 / q, l, 1.0, 40.0, N=800, n_states=1)
        T = C.RadialTable(r, u[:, 0], l)
        ex = H.radial(l + 1, l, x)
        assert np.max(np.abs(T(x) - ex)) / np.max(np.abs(ex)) < lim, l
    E, r, u, _ = radial.wavefunctions(lambda q: -1.0 / q, 0, 1.0, 40.0, N=800, n_states=1)
    T = C.RadialTable(r, u[:, 0], 0)
    assert abs(float(T(0.0)) - 2.0) < 2e-3 and float(T(41.0)) == 0.0
    with pytest.raises(ValueError):
        C.RadialTable(r[:10], u[:10, 0], 0)
    with pytest.raises(ValueError):
        C.RadialTable(np.concatenate([[0.0], r]), np.concatenate([[0.0], u[:, 0]]), 0)


def test_moments_and_box_radius():
    R = lambda r: H.radial(3, 1, r)  # noqa: E731
    for k in (-2, -1, 1, 2):
        assert C.moment(R, k, 120.0) == pytest.approx(H.expectation(3, 1, k), rel=1e-12)
    rb = C.box_radius(R, 1e-3, 120.0)
    assert 1.0 - C.moment(lambda r: np.where(r <= rb, R(r), 0.0), 0, 120.0) == pytest.approx(1e-3, rel=0.05)


# --- the 3-D grid solver of schrodinger_nd: the same states, measured --------------------------------------------------
def test_grid_eigenstates_converge_to_the_exact_orbitals():
    """Hydrogen on 3-D grids (nucleus at a cell centre, box +-12 a.u.): the overlap |<psi_exact|psi_grid>|^2 of 1s and
    of the 2p subspace with the exact functions. The Coulomb cusp converges slowly (test_schrodinger_nd): measured,
    not fitted - 1s: 1 - overlap = 9.2e-3 (dx = 0.6), 5.4e-3 (dx = 0.5); 2p: 2.39e-3, 2.33e-3, limited by the box,
    which squeezes 2p (its grid energy -0.12459 against -0.125). The deficits must fall with dx."""
    out = {}
    for n, d in ((40, 0.6), (48, 0.5)):
        g = S.Grid((n, n, n), d)
        X, Y, Z = g.mesh()
        xs, ys, zs = X - d / 2, Y - d / 2, Z - d / 2
        E, st, _ = S.eigenstates(S.Hamiltonian(g, V=-1.0 / np.sqrt(xs**2 + ys**2 + zs**2)), 4, tol=1e-7)
        p1 = H.orbital(1, 0, 0).psi(xs, ys, zs)
        ov1 = abs(np.sum(np.conj(p1) * st[0]) * g.dV) ** 2 / (np.sum(np.abs(p1) ** 2) * g.dV)
        ps = [H.orbital(2, 1, m, real=True).psi(xs, ys, zs) for m in (-1, 0, 1)]
        ov2 = np.mean([np.sum(np.abs([np.sum(np.conj(a) * st[k]) * g.dV for k in (1, 2, 3)]) ** 2) /
                       (np.sum(np.abs(a) ** 2) * g.dV) for a in ps])
        assert np.ptp(E[1:4]) < 1e-7  # the 2p triplet first above 1s on the grid (2s lies above it)
        out[d] = (1 - ov1, 1 - ov2)
    (a1, a2), (b1, b2) = out[0.6], out[0.5]
    assert b1 < a1 < 1e-2 and b2 < a2 < 3e-3, out


# --- the energy of a wave function: an eigenfunction check independent of its eigenvalue ---------------------------------
@pytest.mark.parametrize("n,l,Z", [(1, 0, 1.0), (2, 1, 1.0), (3, 2, 2.0), (6, 0, 1.0), (10, 3, 1.0)])
def test_energy_terms_of_hydrogen_obey_bohr_and_the_virial_theorem(n, l, Z):
    """<T> = Z^2 / 2n^2, <V> = -Z^2 / n^2 with R' by fourth-order differences (measured: <T> within 1.6e-12, <V>
    within 4e-15)."""
    R = lambda r: H.radial(n, l, r, Z)  # noqa: E731
    T, Vv = C.energy_terms(R, C.derivative_fd(R, n / Z), l, lambda r: -Z / r, (2.0 * n * n + 40.0 * n) / Z)
    assert T == pytest.approx(Z * Z / (2 * n * n), rel=1e-10) and Vv == pytest.approx(-Z * Z / (n * n), rel=1e-10)


def test_table_derivative_gives_the_energy_to_the_tables_accuracy():
    """A tabulated 1s and 2p (box 40, N = 800): the spline's own derivative in <T> + <V> against -1/2n^2; measured
    errors 5.6e-8 (1s) and 1.4e-9 (2p) relative (the solver's extrapolated levels: 1.3e-5 and 4.2e-7); the spline's
    derivative against differences of the spline: 7e-10."""
    for l, lim in ((0, 2e-7), (1, 1e-8)):
        E, r, u, _ = radial.wavefunctions(lambda q: -1.0 / q, l, 1.0, 40.0, N=800, n_states=1)
        T = C.RadialTable(r, u[:, 0], l)
        Tk, Vk = C.energy_terms(T, T.derivative, l, lambda q: -1.0 / q, 40.0)
        assert abs((Tk + Vk) + 0.5 / (l + 1) ** 2) / (0.5 / (l + 1) ** 2) < lim, (l, Tk + Vk)
        x = np.linspace(0.5, 20.0, 400)
        assert np.max(np.abs(T.derivative(x) - C.derivative_fd(T, 1.0)(x))) < 1e-8  # the spline's derivative itself
