# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P7: generic bound Kerr orbits (lfphys.core.gravity.kerr_orbits) against independent routes.

* Constants (E, L, Q) of (p, e, x): against the exact solution of the three defining equations R(r_p) = R(r_a) = 0,
  Theta(theta_min) = 0 (or R = R' = 0 at e = 0) solved by ``mp.findroot`` at 40 digits; tolerance: the engine's own
  first-order running error bound along its actual operations (``_common.Fe`` of the comparison suite, its ``math``
  replaced by the bounded one; Higham, Accuracy and Stability, Sec. 3.3).
* Frequencies: against 30-digit quadratures of the periods and averages over the Mino phases (r = p/(1 + e cos chi),
  cos theta = sqrt(z_-) cos chi: smooth integrands, tanh-sinh); tolerance B (sum_i |x_i dF/dx_i| + |F|) for the inputs
  x = (p, e, x) with B = 256 u (64 u each for the constants, the roots, the elliptic integrals and the sums), the
  derivatives by central differences of the engine's function.
* Positions: against the Hamiltonian route (kerr_geodesics.integrate, DOP853, error estimated by a second run at a
  100 times tighter tolerance); conservation of Q and mu^2 = 1 along it.
* Limits: the circular equatorial orbits of ``kerr.circular_e_l`` (both with running bounds), the Schwarzschild
  closed forms, the exact Schwarzschild periapsis advance and radial period of ``orbits`` (elliptic K; Gauss-Legendre).
"""

import math
import sys
from pathlib import Path

import mpmath as mp
import numpy as np
import pytest

from lfphys.core.gravity import kerr, kerr_geodesics as KG, kerr_orbits as KO, orbits

sys.path.insert(0, str(Path(__file__).resolve().parent / "external"))
from _common import FMATH, Fe  # noqa: E402  (pure Python: the running error bound, no third-party library)

U = 2.0 ** -53
B256 = 256 * U

ORBITS = [  # chi, p, e, x
    (0.9, 6.0, 0.7, math.cos(math.radians(20))),  # Fujita & Hikida 2009, Table 3
    (0.5, 10.0, 0.3, 0.5), (0.99, 4.0, 0.2, 0.9), (0.9, 12.0, 0.6, -0.4), (0.3, 30.0, 0.1, 0.05),
    (0.7, 8.0, 0.0, 0.7), (0.7, 9.0, 0.4, 1.0), (0.7, 14.0, 0.5, -1.0), (0.6, 10.0, 0.4, 0.0),
    (0.0, 12.0, 0.5, 0.6),
]


class _bounded:
    def __enter__(self):
        self.saved = KO.math
        KO.math = FMATH

    def __exit__(self, *a):
        KO.math = self.saved


def exact_constants(chi, p, e, x, guess):
    """E, L, Q solving the defining equations at 40 digits (start: the engine's values)."""
    with mp.workdps(40):
        a, p_, e_, x_ = mp.mpf(chi), mp.mpf(p), mp.mpf(e), mp.mpf(x)
        z = 1 - x_ ** 2

        def R(r, E, L, Q):
            dl = r * r - 2 * r + a * a
            return (E * (r * r + a * a) - a * L) ** 2 - dl * (r * r + (L - a * E) ** 2 + Q)

        def eqs(E, L, Q):
            if e_ > 0:
                out = [R(p_ / (1 + e_), E, L, Q), R(p_ / (1 - e_), E, L, Q)]
            else:
                out = [R(p_, E, L, Q), mp.diff(lambda r: R(r, E, L, Q), p_)]
            out.append(Q - z * (a * a * (1 - E * E) + L * L / (1 - z)) if x_ != 0 else L)
            return out
        sol = mp.findroot(eqs, [mp.mpf(g) for g in guess], tol=mp.mpf(10) ** -36, maxsteps=100)
        return [sol[i] for i in range(3)]


@pytest.mark.parametrize("orb", ORBITS)
def test_constants_against_the_exact_solution(orb):
    """Schmidt's closed form is within its own running error bound of the 40-digit solution (that bound is large
    where the elimination cancels: nearly polar orbits, large p); the Newton-polished constants are within
    |J^-1| e_F, J the Jacobian of the defining equations and e_F the a-priori round-off of their evaluation
    (gamma_16 times the sum of the absolute values of their terms) - the conditioning of the problem itself."""
    chi, p, e, x = orb
    E, L, Q = KO.constants(chi, p, e, x)
    ex = exact_constants(chi, p, e, x, (E, L, Q))
    with _bounded():
        Eb, Lb, Qb = KO.schmidt_constants(Fe(chi), Fe(p), Fe(e), Fe(x))
    Es, Ls, Qs = KO.schmidt_constants(chi, p, e, x)
    for got, b, ref in ((Es, Eb, ex[0]), (Ls, Lb, ex[1]), (Qs, Qb, ex[2])):
        bnd = b.e if isinstance(b, Fe) else 0.0
        assert (b.v if isinstance(b, Fe) else b) == got  # the bounded run is the same sequence of operations
        assert abs(got - float(ref)) <= bnd + 2 * U * abs(float(ref)) + 1e-300, (got, ref, bnd)
    F, J, S = KO._residual(chi, p, e, x, E, L, Q)
    Jinv = np.linalg.inv(np.array(J))
    g16 = 16 * U / (1 - 16 * U)
    tol = np.abs(Jinv) @ (g16 * np.array(S)) * 2 + 2 * U * np.abs([E, L, Q])
    for got, ref, t in zip((E, L, Q), ex, tol):
        assert abs(got - float(ref)) <= t, (got, ref, t)


@pytest.mark.parametrize("chi", [0.0, 0.5, 0.9, 0.999])
@pytest.mark.parametrize("pro", [True, False])
def test_circular_equatorial_limit_is_kerr_closed_form(chi, pro):
    r_isco = kerr.isco(chi, pro)
    for f in (1.01, 1.5, 3.0, 30.0):
        r = r_isco * f
        E, L, Q = KO.constants(chi, r, 0.0, 1.0 if pro else -1.0)
        e2, l2 = kerr.circular_e_l(r, chi, pro)
        with _bounded():
            Eb, Lb, _ = KO.constants(Fe(chi), Fe(r), Fe(0.0), Fe(1.0 if pro else -1.0))
        saved = kerr.math
        kerr.math = FMATH
        try:
            e2b, l2b = kerr.circular_e_l(Fe(r), Fe(chi), pro)
        finally:
            kerr.math = saved
        assert Q == 0.0
        assert abs(E - e2) <= Eb.e + e2b.e and abs(L - l2) <= Lb.e + l2b.e, (r, E, e2, L, l2)


def test_schwarzschild_constants_and_inclination_symmetry():
    """a = 0: E, L of the planar orbit; L_z = x L, Q = (1 - x^2) L^2 (the orbital plane is arbitrary)."""
    for p, e in ((10.0, 0.3), (7.0, 0.5), (40.0, 0.0)):
        E0, L0, Q0 = KO.constants(0.0, p, e, 1.0)
        assert Q0 == 0.0
        assert abs(E0 ** 2 - ((p - 2) ** 2 - 4 * e * e) / (p * (p - 3 - e * e))) <= 8 * U
        for x in (0.3, -0.8):
            E, L, Q = KO.constants(0.0, p, e, x)
            assert E == E0 and abs(L - x * L0) <= 2 * U * abs(L) and abs(Q - (1 - x * x) * L0 ** 2) <= 4 * U * Q


# --- frequencies ---------------------------------------------------------------------------------------------------
def exact_frequencies(chi, p, e, x, guess):
    E, L, Q = exact_constants(chi, p, e, x, guess)
    with mp.workdps(30):
        a = mp.mpf(chi)
        p_, e_ = mp.mpf(p), mp.mpf(e)
        r1, r2 = p_ / (1 - e_), p_ / (1 + e_)
        one = 1 - E * E
        s = 2 / one - (r1 + r2)
        prod = a * a * Q / (one * r1 * r2)
        r3 = (s + mp.sqrt(s * s - 4 * prod)) / 2
        r4 = prod / r3
        beta = a * a * one
        bq = Q + beta + L * L
        bzp = (bq + mp.sqrt(bq * bq - 4 * beta * Q)) / 2
        zm = Q / bzp if bzp else mp.mpf(0)

        def r_of(c):
            return p_ / (1 + e_ * mp.cos(c))

        def dlam_r(c):  # dlambda/dchi for r = p/(1 + e cos chi)
            r = r_of(c)
            return mp.sqrt(1 - e_ * e_) / ((1 + e_ * mp.cos(c)) * mp.sqrt(one * (r - r3) * (r - r4)))

        def dlam_t(c):  # dlambda/dchi for cos theta = sqrt(z_-) cos chi
            return 1 / mp.sqrt(bzp - beta * zm * mp.cos(c) ** 2)
        Lr = 2 * mp.quad(dlam_r, [0, mp.pi])
        Lt = 4 * mp.quad(dlam_t, [0, mp.pi / 2])

        def Tr(r):
            dl = r * r - 2 * r + a * a
            P = E * (r * r + a * a) - a * L
            return (r * r + a * a) / dl * P

        def Pr(r):
            dl = r * r - 2 * r + a * a
            return a / dl * (E * (r * r + a * a) - a * L)
        avg_Tr = 2 * mp.quad(lambda c: Tr(r_of(c)) * dlam_r(c), [0, mp.pi]) / Lr
        avg_Pr = 2 * mp.quad(lambda c: Pr(r_of(c)) * dlam_r(c), [0, mp.pi]) / Lr
        avg_s2 = 4 * mp.quad(lambda c: (1 - zm * mp.cos(c) ** 2) * dlam_t(c), [0, mp.pi / 2]) / Lt
        avg_cs2 = 4 * mp.quad(lambda c: dlam_t(c) / (1 - zm * mp.cos(c) ** 2), [0, mp.pi / 2]) / Lt
        gam = avg_Tr - a * a * E * avg_s2 + a * L
        ups_phi = avg_Pr + L * avg_cs2 - a * E
        out = {"Upsilon_r": 2 * mp.pi / Lr, "Upsilon_theta": 2 * mp.pi / Lt, "Upsilon_phi": ups_phi, "Gamma": gam}
        out.update({"Omega_r": out["Upsilon_r"] / gam, "Omega_theta": out["Upsilon_theta"] / gam,
                    "Omega_phi": ups_phi / gam})
        return out


def _freq_tol(chi, p, e, x, key, method):
    """B256 (sum over the inputs p, e, x of |v dF/dv| + sum over the float constants E, L, Q of |c dF/dc| + |F|):
    the inputs and the representation of the constants (e.g. 1 - E^2 amplifies the rounding of E by 1/(1 - E^2))."""
    o = KO.KerrOrbit(chi, p, e, x)
    f = o.frequencies(method)[key]
    tot = abs(f)
    for i, v in enumerate((p, e, x)):
        if v == 0.0 or (i == 2 and abs(v) == 1.0):
            continue  # an exact special value (circular, equatorial, polar) is not perturbed
        h = 1e-6 * abs(v)
        args = [p, e, x]
        lo, hi = list(args), list(args)
        lo[i], hi[i] = v - h, v + h
        tot += abs(v) * abs(KO.KerrOrbit(chi, *hi).frequencies(method)[key]
                            - KO.KerrOrbit(chi, *lo).frequencies(method)[key]) / (2 * h)
    c = [o.E, o.L, o.Q]
    for i, v in enumerate(c):
        if v == 0.0:
            continue
        h = 1e-7 * abs(v)
        lo, hi = list(c), list(c)
        lo[i], hi[i] = v - h, v + h
        fl = KO.KerrOrbit(chi, p, e, x, consts=lo).frequencies(method)[key]
        fh = KO.KerrOrbit(chi, p, e, x, consts=hi).frequencies(method)[key]
        tot += abs(v) * abs(fh - fl) / (2 * h)
    return B256 * tot


@pytest.mark.parametrize("orb", [o for o in ORBITS if o[3] != 0.0 and o[2] > 0.0][:6])
def test_frequencies_against_quadrature_both_routes(orb):
    chi, p, e, x = orb
    o = KO.KerrOrbit(chi, p, e, x)
    ex = exact_frequencies(chi, p, e, x, (o.E, o.L, o.Q))
    for method in ("closed", "average"):
        f = o.frequencies(method)
        for k in ("Upsilon_r", "Upsilon_theta", "Upsilon_phi", "Gamma", "Omega_r", "Omega_theta", "Omega_phi"):
            tol = _freq_tol(chi, p, e, x, k, method)
            assert abs(f[k] - float(ex[k])) <= tol, (method, k, f[k], ex[k], tol)


def test_fujita_hikida_table_3():
    """FH 2009 Table 3 ("This work"), a = 0.9 M, p = 6 M, e = 0.7, theta_inc = 20 deg. The engine is within its
    derived tolerance of the 30-digit reference; the published 17-digit values differ from the reference by
    1.2e-13 .. 2.3e-13 (relative; measured 2026-10-29) - more than the 1e-15 that FH state between their two
    methods, so their printed digits carry the error of their constants of motion; recorded, bounded by 1e-12."""
    chi, p, e, x = 0.9, 6.0, 0.7, math.cos(math.radians(20.0))
    o = KO.KerrOrbit(chi, p, e, x)
    ex = exact_frequencies(chi, p, e, x, (o.E, o.L, o.Q))
    fh = {"Omega_r": 1.8928532285101992e-2, "Omega_theta": 2.7299110395017517e-2,
          "Omega_phi": 3.0550463796964692e-2}
    f = o.frequencies()
    for k, v in fh.items():
        assert abs(f[k] - float(ex[k])) <= _freq_tol(chi, p, e, x, k, "closed")
        assert abs(v / float(ex[k]) - 1) < 1e-12


def test_schwarzschild_frequencies_against_the_exact_periapsis_advance():
    """a = 0, equatorial: Omega_phi/Omega_r = 1 + (periapsis advance)/(2 pi) and Omega_r = 2 pi/t_r, the advance
    and the coordinate-time radial period from ``orbits`` (elliptic K and Gauss-Legendre in the Schwarzschild
    turning-point variables: an independent route)."""
    for p, e in ((10.0, 0.3), (20.0, 0.6), (7.5, 0.1)):
        o = KO.KerrOrbit(0.0, p, e, 1.0)
        f = o.frequencies()
        adv = orbits.advance_from_turning((1 - e) / p, (1 + e) / p)
        tr = orbits.radial_period(o.E, o.L)["t"]
        assert abs(f["Omega_phi"] / f["Omega_r"] - (1 + adv / (2 * math.pi))) <= 1e-13
        assert abs(f["Omega_r"] - 2 * math.pi / tr) <= 1e-13 * f["Omega_r"]


def test_kepler_limit():
    """p -> infinity: Omega_r, Omega_theta, Omega_phi -> ((1 - e^2)/p)^(3/2) (Kepler's third law); the relative
    differences are O(1/p) (here p = 1e6: < 1e-5)."""
    p, e = 1e6, 0.4
    f = KO.KerrOrbit(0.6, p, e, 0.5).frequencies()
    kep = ((1 - e * e) / p) ** 1.5
    for k in ("Omega_r", "Omega_theta", "Omega_phi"):
        assert abs(f[k] / kep - 1) < 1e-5


# --- positions -----------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("orb", [ORBITS[0], ORBITS[3], ORBITS[8], ORBITS[9]])
def test_closed_form_orbit_against_the_hamiltonian_route(orb):
    chi, p, e, x = orb
    o = KO.KerrOrbit(chi, p, e, x, q_r0=0.4, q_th0=1.1)
    lams = np.array([0.3, 1.0, 2.2, 3.5])
    t, r, th, ph = o.trajectory(lams)
    x0 = [0.0, float(o.r(0.0)), float(o.theta(0.0)), 0.0]
    p0 = o.momentum(0.0)
    # the momentum's derivative by a central difference of the closed form (h = 1e-6): error <= 1e-10 relative,
    # which starts the integration on a neighbouring orbit; its constants differ by that much (checked below)
    runs = [KG.integrate(chi, x0, p0, float(lams[-1]), rtol=rt, atol=rt * 1e-2, dense=True) for rt in (1e-11, 1e-13)]
    y1 = np.array([runs[0].sol(v) for v in lams])
    y2 = np.array([runs[1].sol(v) for v in lams])
    m2, Q = KG.constants(runs[1].y[1], runs[1].y[2], runs[1].y[4], runs[1].y[5], runs[1].E, runs[1].L, chi,
                        mu2=1.0)
    dQ0 = abs(Q[0] - o.Q)
    assert abs(m2[0] - 1) < 1e-8 and dQ0 < 1e-8 * max(1.0, o.Q)
    # conservation along the Hamiltonian route (beyond the start's offset)
    assert np.max(np.abs(Q - Q[0])) <= 1e-9 * max(1.0, o.Q) and np.max(np.abs(m2 - m2[0])) <= 1e-9
    err = 2 * np.abs(y1 - y2)
    off = 1e-7  # the start offset (1e-10) propagated over a few orbits (Lyapunov-free, linear growth): <= 1e-7
    assert np.all(np.abs(y2[:, 1] - r) <= err[:, 1] + off * r)
    assert np.all(np.abs(y2[:, 0] - t) <= err[:, 0] + off * (1 + np.abs(t)))
    # the direction (sin th cos ph, sin th sin ph, cos th): Boyer-Lindquist theta of the integrator runs past the pole
    # (theta -> 2 pi - theta, phi -> phi + pi) where the closed form's arccos stays in [0, pi]
    def unit(thv, phv):
        return np.stack((np.sin(thv) * np.cos(phv), np.sin(thv) * np.sin(phv), np.cos(thv)), 1)
    du = np.linalg.norm(unit(y2[:, 2], y2[:, 3]) - unit(th, ph), axis=1)
    assert np.all(du <= err[:, 2] + err[:, 3] + off * (1 + np.abs(ph)))


@pytest.mark.parametrize("orb", ORBITS[:5])
def test_closed_form_keeps_the_constants(orb):
    """Along the closed form, (dr/dlambda)^2 = R(r) and (dcos(theta)/dlambda)^2 = Theta(cos theta) with the orbit's
    E, L, Q: the derivatives by a 4th-order central difference (h = 1e-3 of the shorter period: truncation and
    round-off <= 1e-9 of the potentials' scale)."""
    chi, p, e, x = orb
    o = KO.KerrOrbit(chi, p, e, x, q_r0=0.2, q_th0=0.7)
    per = 2 * math.pi / max(o.ups_r, o.ups_th)
    h = 1e-3 * per
    a = chi
    for lam in np.linspace(0.0, 3 * per, 13):
        d = lambda f: (-f(lam + 2 * h) + 8 * f(lam + h) - 8 * f(lam - h) + f(lam - 2 * h)) / (12 * h)  # noqa: E731
        drl = d(lambda s: float(o.r(s)))
        dcl = d(lambda s: float(o.cos_theta(s)))
        r, c = float(o.r(lam)), float(o.cos_theta(lam))
        R = KO.radial_potential(r, o.E, o.L, o.Q, chi)
        Th = o.Q - (o.Q + a * a * (1 - o.E ** 2) + o.L ** 2) * c * c + a * a * (1 - o.E ** 2) * c ** 4
        scale = (o.E * (r * r + a * a)) ** 2 + abs(r * r - 2 * r + a * a) * (r * r + (o.L - a * o.E) ** 2 + o.Q)
        assert abs(drl ** 2 - R) <= 1e-9 * scale
        assert abs(dcl ** 2 - Th) <= 1e-9 * (o.Q + a * a + o.L ** 2)
        assert r <= o.r1 * (1 + 1e-15) and r >= o.r2 * (1 - 1e-15)


def test_step_wise_advance_and_exact_state():
    o = KO.KerrOrbit(0.9, 8.0, 0.5, 0.6, q_r0=0.3, q_th0=0.2)
    t_ref, r_ref, th_ref, ph_ref = KO.KerrOrbit(0.9, 8.0, 0.5, 0.6, q_r0=0.3, q_th0=0.2).trajectory(np.array([5.0]))
    for _ in range(25):
        o.advance(0.2)
    lam, t, r, th, ph = o.lam, o.t, float(o.r(o.lam)), float(o.theta(o.lam)), o.phi
    assert abs(lam - 5.0) < 1e-14
    # the same integrals summed over 25 steps instead of one: Gauss-Legendre panels exact to ~1e-14 relative each
    assert abs(t - t_ref[0]) <= 1e-12 * abs(t_ref[0]) and abs(ph - ph_ref[0]) <= 1e-12 * abs(ph_ref[0])
    assert abs(r - r_ref[0]) <= 1e-13 * r and abs(th - th_ref[0]) <= 1e-13
    st = o.state()
    o2 = KO.KerrOrbit.from_state(st)
    a1 = [o.advance(0.37) for _ in range(3)]
    a2 = [o2.advance(0.37) for _ in range(3)]
    assert a1 == a2
