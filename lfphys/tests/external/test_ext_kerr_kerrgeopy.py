# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""``lfphys.core.gravity.kerr`` and ``kerr_orbits`` against KerrGeoPy 0.9.3 (plan items P13, P7): equatorial and
generic (eccentric, inclined) Kerr orbits.

Compared (G = c = M = 1, spin chi = a/M):
* ISCO, prograde and retrograde: the engine's Bardeen-Press-Teukolsky closed form against KerrGeoPy's separatrix
  ``separatrix(a, e=0, x=+-1)``, a root of the separatrix polynomial (Stein & Warburton 2020, Eq. 23) found by
  scipy's brentq: an independent route.
* marginally bound circular orbit: the engine's closed form against half the separatrix at e = 1 (the parabolic
  separatrix orbit has its periapsis p/(1 + e) at r_mb).
* energy and angular momentum of circular orbits: the engine's closed forms against KerrGeoPy's ``energy`` and
  ``angular_momentum`` (Schmidt 2002, Appendix B, Eqs. B.17-B.22), from r_isco(1 + 1e-6) to 1e4 r_isco.
* horizons: the engine against ``KerrSpacetime(a).outer_horizon / inner_horizon``.
* the engine's equatorial radial potential R(r) with KerrGeoPy's E, L of eccentric orbits (p, e): R must vanish at the
  turning points p/(1 - e) and p/(1 + e). This checks ``kerr.radial_potential`` (the engine's own independent route for
  its closed forms) against a library that finds E, L by another method.
* generic orbits (P7, ``kerr_orbits``): E, L, Q of (p, e, x = cos(inclination)) against KerrGeoPy's
  ``constants_of_motion`` (Schmidt 2002 App. B, the same closed form the engine starts from; the engine then polishes
  by Newton steps on the defining equations); polar orbits (x = 0) against KerrGeoPy's separate closed forms (from
  the Mathematica KerrGeodesics library); the Mino frequencies Upsilon_r, Upsilon_theta, Upsilon_phi, Gamma and
  Omega_r, Omega_theta, Omega_phi against ``mino_frequencies``/``fundamental_frequencies`` (both Fujita & Hikida
  2009 Eqs. 15 and 21; the engine writes the theta-averages without L_z and uses its own elliptic routines).
Not compared: the circular photon orbit (KerrGeoPy has no routine for it), the radiative efficiency (KerrGeoPy refuses
the orbit at the separatrix itself), spin chi = 1 (KerrGeoPy: "Extreme Kerr not supported"), frequencies of polar
orbits (KerrGeoPy: "Polar orbits not supported").

Exact reference: the closed forms evaluated in 50-digit mpmath for the same binary64 inputs (eng_err, lib_err).

Tolerances (derived):
* "running error": each closed form is evaluated with ``_common.Fe`` along the actual operations of each side (the
  engine's functions with their ``math`` replaced by the bounded one, KerrGeoPy's pure-Python functions called with Fe
  arguments; the Fe value must equal the float result bit for bit). Tolerance = engine bound + library bound.
* "brentq + noise": KerrGeoPy's separatrix is a root found by scipy's brentq with its defaults xtol = 2e-12 and
  rtol = 4 eps ("the computed root x0 will satisfy np.isclose(x, x0, atol=xtol, rtol=rtol)", scipy documentation,
  for an exactly evaluated function); the polynomial is evaluated in float with an error of at most dS (its running
  bound at the returned root), so the root can be anywhere in the connected set {p : |S_exact(p)| <= dS} around the
  exact root, whose half-width w is found in mpmath. Library bound = xtol + rtol |p| + w; plus the engine's running
  bound. Near chi = 1 the separatrix polynomial approaches a triple root at p = 1, so w grows as dS^(1/3): this is
  where KerrGeoPy loses digits and the engine's closed form does not.
* "residual": |R(r_turning)| <= the running bound of the engine's R evaluated with KerrGeoPy's E, L carrying their
  own running bounds (and r = p/(1 -+ e) carrying its rounding).
* "conditioning + running error" (generic E, L, Q): the engine's polished constants are within |J^-1| e_F (J the
  Jacobian of the defining equations R(r_p) = R(r_a) = 0, Theta(theta_min) = 0, e_F = gamma_16 x the absolute terms
  of their evaluation, doubled) plus 2 u; KerrGeoPy's within its first-order running bound along its own operations
  (``_common.Fe``; its stability check, the sign bookkeeping of a and numpy's sign bypassed, the formulas as
  written). The exact reference: the defining equations solved by mpmath's findroot at 40 digits.
* "sensitivity budget" (frequencies): each side's error <= B (sum over the inputs p, e, x of |v dF/dv| + sum over
  E, L, Q of |c dF/dc| + |F|) with B = 256 u (64 u each for the constants, roots, elliptic integrals, sums), the
  derivatives by central differences of the engine's function; KerrGeoPy's unpolished constants add
  sum |dF/dc| e_c with e_c their running bounds. The exact reference: 30-digit tanh-sinh quadratures of the periods
  and the Mino-phase averages (r = p/(1 + e cos chi), cos theta = sqrt(z_-) cos chi).
"""

from __future__ import annotations

import contextlib
import functools
import math

import mpmath as mp
import numpy as np
import pytest
from kerrgeopy import constants as kc
from kerrgeopy import frequencies as kf
from kerrgeopy.spacetime import KerrSpacetime

from lfphys.core.gravity import kerr, kerr_orbits as KO

from _common import FMATH, U, Fe, Row, check, params

GROUP = "Kerr (KerrGeoPy)"
BRENTQ_XTOL, BRENTQ_RTOL = 2e-12, 4 * np.finfo(float).eps  # scipy.optimize.brentq defaults (root_scalar passes none)
SPINS = (0.0, 0.1, 0.5, 0.9, 0.99, 0.999, 0.9999, 1 - 1e-6, 1 - 1e-9, 1 - 1e-12)
DPS = 50  # digits of the exact references (set per function, not globally)


@contextlib.contextmanager
def engine_bounded():
    """Run the engine's kerr functions with the bounded math (``_common.FMATH``)."""
    saved = kerr.math
    kerr.math = FMATH
    try:
        yield
    finally:
        kerr.math = saved


@contextlib.contextmanager
def library_bounded():
    """Call KerrGeoPy's energy/angular_momentum with Fe arguments: its stability check (a brentq root) and the sign
    bookkeeping of a are bypassed (both were passed by the float call of the same orbit), the formulas run as written."""
    saved = kc.is_stable, kc._standardize_params
    kc.is_stable = lambda *a: True
    kc._standardize_params = lambda a, x: (a, x)
    try:
        yield
    finally:
        kc.is_stable, kc._standardize_params = saved


def _same(fe, val):
    if fe.v != val:
        raise AssertionError(f"bounded evaluation {fe.v!r} differs from the float result {val!r}: not the same "
                             f"sequence of operations")
    return fe


# --- exact references -----------------------------------------------------------------------------------------------

def isco_exact(chi, pro):
    c = mp.mpf(chi)
    z1 = 1 + mp.cbrt(1 - c * c) * (mp.cbrt(1 + c) + mp.cbrt(1 - c))
    z2 = mp.sqrt(3 * c * c + z1 * z1)
    return 3 + z2 - (1 if pro else -1) * mp.sqrt((3 - z1) * (3 + z1 + 2 * z2))


def mb_exact(chi, pro):
    c, s = mp.mpf(chi), (1 if pro else -1)
    return 2 - s * c + 2 * mp.sqrt(1 - s * c)


def el_exact(r, chi, pro):
    s = 1 if pro else -1
    r, c = mp.mpf(r), mp.mpf(chi)
    sr = mp.sqrt(r)
    den = r ** mp.mpf(0.75) * mp.sqrt(r * sr - 3 * sr + s * 2 * c)
    return (r * sr - 2 * sr + s * c) / den, s * (r * r - s * 2 * c * sr + c * c) / den


def s_exact(p, a, e):
    """Stein & Warburton's equatorial separatrix polynomial (as in KerrGeoPy) in mpmath."""
    p, a, e = mp.mpf(p), mp.mpf(a), mp.mpf(e)
    return (a ** 4 * (-3 - 2 * e + e ** 2) ** 2 + p ** 2 * (-6 - 2 * e + p) ** 2
            - 2 * a ** 2 * (1 + e) * p * (14 + 2 * e ** 2 + 3 * p - e * p))


def noise_halfwidth(p0, a, e, dS):
    """Half-width of the connected set {p : |S_exact(p)| <= dS} around the exact root p0 (mpmath)."""
    def side(sign):
        d = mp.mpf(2) ** -60 * p0
        if abs(s_exact(p0 + sign * d, a, e)) > dS:
            return d
        while abs(s_exact(p0 + sign * d, a, e)) <= dS:
            d *= 2
            if d > 1:
                return d
        lo, hi = d / 2, d
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if abs(s_exact(p0 + sign * mid, a, e)) <= dS else (lo, mid)
        return hi
    return float(max(side(+1), side(-1)))


# --- rows -----------------------------------------------------------------------------------------------------------

def _separatrix_rows():
    out = []
    for chi in SPINS:
        for pro in (True, False):
            x = 1 if pro else -1
            for e, name, eng_fn, exact_fn, scale in ((0.0, "ISCO r_isco", kerr.isco, isco_exact, 1.0),
                                                    (1.0, "marginally bound r_mb", kerr.marginally_bound, mb_exact, 2.0)):
                eng = eng_fn(chi, pro)
                with engine_bounded():
                    b_eng = _same(eng_fn(Fe(chi), pro), eng).e
                p_lib = kc.separatrix(chi, e, x)
                exact = exact_fn(chi, pro)
                if chi == 0.0:  # KerrGeoPy returns 6 + 2e exactly
                    b_lib = 0.0
                else:
                    dS = _same(kc._S_equatorial(Fe(p_lib), Fe(chi), Fe(e)), kc._S_equatorial(p_lib, chi, e)).e
                    w = noise_halfwidth(scale * exact, chi, e, dS)
                    b_lib = BRENTQ_XTOL + BRENTQ_RTOL * abs(p_lib) + w
                lib = p_lib / scale
                out.append(Row(GROUP, f"{name} ({'pro' if pro else 'retro'}grade)", f"chi={chi!r}", eng, lib,
                               b_eng + b_lib / scale, "brentq + noise", float(abs(eng - exact)),
                               float(abs(lib - exact))))
    return out


def _circular_rows():
    out = []
    for chi in (0.0, 0.5, 0.9, 0.999, 1 - 1e-6, 1 - 1e-9, 1 - 1e-12):
        for pro in (True, False):
            x = 1 if pro else -1
            r_isco = kerr.isco(chi, pro)
            for f in (1 + 1e-6, 1.01, 1.5, 3.0, 30.0, 1e4):
                r = r_isco * f
                e_eng, l_eng = kerr.circular_e_l(r, chi, pro)
                with engine_bounded():
                    e_fe, l_fe = kerr.circular_e_l(Fe(r), Fe(chi), pro)
                e_lib = kc.energy(chi, r, 0.0, x)
                l_lib = kc.angular_momentum(chi, r, 0.0, x)
                with library_bounded():
                    E = _same(kc.energy(Fe(chi), Fe(r), Fe(0.0), x), e_lib)
                    L = _same(kc.angular_momentum(Fe(chi), Fe(r), Fe(0.0), x, E=E), l_lib)
                _same(e_fe, e_eng), _same(l_fe, l_eng)
                ex_e, ex_l = el_exact(r, chi, pro)
                lab = f"chi={chi!r}, r={f:g} r_isco"
                sense = "pro" if pro else "retro"
                out.append(Row(GROUP, f"circular orbit E ({sense}grade)", lab, e_eng, e_lib, e_fe.e + E.e,
                               "running error", float(abs(e_eng - ex_e)), float(abs(e_lib - ex_e))))
                out.append(Row(GROUP, f"circular orbit L ({sense}grade)", lab, l_eng, l_lib, l_fe.e + L.e,
                               "running error", float(abs(l_eng - ex_l)), float(abs(l_lib - ex_l))))
    return out


def _horizon_rows():
    out = []
    for chi in (0.0, 0.1, 0.5, 0.9, 0.999, 1 - 1e-9, 1.0):
        rp, rm = kerr.horizons(chi)
        with engine_bounded():
            hp, hm = kerr.horizons(Fe(chi))
        ks, ks_fe = KerrSpacetime(chi), KerrSpacetime(Fe(chi))
        s = mp.sqrt(1 - mp.mpf(chi) ** 2)
        for name, eng, fe, lib, lib_fe, ex in (("outer horizon r_+", rp, hp, ks.outer_horizon, ks_fe.outer_horizon,
                                                1 + s),
                                               ("inner horizon r_-", rm, hm, ks.inner_horizon, ks_fe.inner_horizon,
                                                1 - s)):
            _same(fe, eng), _same(lib_fe, float(lib))
            out.append(Row(GROUP, name, f"chi={chi!r}", eng, float(lib), fe.e + lib_fe.e, "running error",
                           float(abs(eng - ex)), float(abs(lib - ex))))
    return out


def _eccentric_rows():
    out = []
    for chi in (0.3, 0.9, 0.99):
        for pro in (True, False):
            x = 1 if pro else -1
            for e in (0.1, 0.5, 0.9):
                for p in (1.2 * kc.separatrix(chi, e, x), 20.0):
                    E_f = kc.energy(chi, p, e, x)
                    L_f = kc.angular_momentum(chi, p, e, x)
                    with library_bounded():
                        E = _same(kc.energy(Fe(chi), Fe(p), Fe(e), x), E_f)
                        L = _same(kc.angular_momentum(Fe(chi), Fe(p), Fe(e), x, E=E), L_f)
                    for name, r_fe in (("apoapsis p/(1-e)", Fe(p) / (1 - Fe(e))), ("periapsis p/(1+e)",
                                                                                   Fe(p) / (1 + Fe(e)))):
                        R = kerr.radial_potential(r_fe.v, E_f, L_f, chi)
                        with engine_bounded():
                            R_fe = _same(kerr.radial_potential(r_fe, E, L, Fe(chi)), R)
                        out.append(Row(GROUP, f"R(r) at the {name} with KerrGeoPy's E, L "
                                       f"({'pro' if pro else 'retro'}grade)", f"chi={chi}, p={p:.6g}, e={e}",
                                       R, 0.0, R_fe.e, "residual"))
    return out


# --- generic orbits (plan P7) ---------------------------------------------------------------------------------------

GENERIC_SPINS = (0.3, 0.7, 0.9, 0.99)
GENERIC_E = (0.1, 0.5, 0.8)
GENERIC_X = (0.9, 0.4, 0.1, -0.4, -0.9)


def _generic_orbits():
    out = []
    for a in GENERIC_SPINS:
        for e in GENERIC_E:
            for x in GENERIC_X:
                for p in (1.3 * kc.separatrix(a, e, x), 25.0):
                    out.append((a, float(p), e, x))
    return out


@contextlib.contextmanager
def library_bounded_generic():
    """KerrGeoPy's constants with Fe arguments: its stability check and the sign bookkeeping of a bypassed (passed by
    the float call of the same orbit), numpy's sign replaced by the sign of the value."""
    saved = kc.is_stable, kc._standardize_params, kc.sign
    kc.is_stable = lambda *a: True
    kc._standardize_params = lambda a, x: (a, x)
    kc.sign = lambda v: math.copysign(1.0, v.v if isinstance(v, Fe) else v)
    try:
        yield
    finally:
        kc.is_stable, kc._standardize_params, kc.sign = saved


def exact_generic_constants(chi, p, e, x, guess):
    """E, L, Q solving R(r_p) = R(r_a) = 0, Theta(theta_min) = 0 (L = 0 for x = 0) by findroot at 40 digits."""
    with mp.workdps(40):
        a, p_, e_, x_ = mp.mpf(chi), mp.mpf(p), mp.mpf(e), mp.mpf(x)
        z = 1 - x_ ** 2

        def R(r, E, L, Q):
            dl = r * r - 2 * r + a * a
            return (E * (r * r + a * a) - a * L) ** 2 - dl * (r * r + (L - a * E) ** 2 + Q)

        def eqs(E, L, Q):
            return [R(p_ / (1 + e_), E, L, Q), R(p_ / (1 - e_), E, L, Q),
                    (Q - z * (a * a * (1 - E * E) + L * L / (1 - z))) if x_ != 0 else L]
        sol = mp.findroot(eqs, [mp.mpf(g) for g in guess], tol=mp.mpf(10) ** -36, maxsteps=100)
        return [sol[i] for i in range(3)]


def _engine_constants_bound(chi, p, e, x, c):
    F, J, S = KO._residual(chi, p, e, x, *c)
    Jinv = np.linalg.inv(np.array(J))
    g16 = 16 * U / (1 - 16 * U)
    return np.abs(Jinv) @ (g16 * np.array(S)) * 2 + 2 * U * np.abs(np.array(c))


def _generic_constant_rows():
    out = []
    for a, p, e, x in _generic_orbits():
        eng = KO.constants(a, p, e, x)
        lib = kc.constants_of_motion(a, p, e, x)
        with library_bounded_generic():
            Eb = _same(kc.energy(Fe(a), Fe(p), Fe(e), Fe(x)), lib[0])
            Lb = _same(kc.angular_momentum(Fe(a), Fe(p), Fe(e), Fe(x), E=Eb), lib[1])
            Qb = _same(kc.carter_constant(Fe(a), Fe(p), Fe(e), Fe(x), E=Eb, L=Lb), lib[2])
        ex = exact_generic_constants(a, p, e, x, eng)
        bnd = _engine_constants_bound(a, p, e, x, eng)
        lab = f"chi={a}, p={p:.6g}, e={e}, x={x}"
        for i, (name, lb) in enumerate((("E", Eb), ("L_z", Lb), ("Q", Qb))):
            out.append(Row(GROUP, f"generic orbit {name}", lab, eng[i], float(lib[i]), float(bnd[i]) + lb.e,
                           "conditioning + running error", float(abs(eng[i] - ex[i])), float(abs(lib[i] - ex[i]))))
    # polar orbits: KerrGeoPy's separate closed forms (from the Mathematica KerrGeodesics library)
    for a in GENERIC_SPINS:
        for e in GENERIC_E:
            p = 1.3 * kc.separatrix(a, e, 0.0)
            eng = KO.constants(a, p, e, 0.0)
            lib = kc.constants_of_motion(a, p, e, 0.0)
            with library_bounded_generic():
                Eb = _same(kc.energy(Fe(a), Fe(p), Fe(e), 0.0), lib[0])
                Qb = _same(kc.carter_constant(Fe(a), Fe(p), Fe(e), 0.0), lib[2])
            ex = exact_generic_constants(a, p, e, 0.0, eng)
            bnd = _engine_constants_bound(a, p, e, 0.0, eng)
            lab = f"chi={a}, p={p:.6g}, e={e}, x=0 (polar)"
            for i, name, lb in ((0, "E", Eb), (2, "Q", Qb)):
                out.append(Row(GROUP, f"polar orbit {name}", lab, eng[i], float(lib[i]), float(bnd[i]) + lb.e,
                               "conditioning + running error", float(abs(eng[i] - ex[i])),
                               float(abs(lib[i] - ex[i]))))
    return out


def exact_generic_frequencies(chi, p, e, x, guess):
    E, L, Q = exact_generic_constants(chi, p, e, x, guess)
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
        zm = Q / bzp

        def r_of(c):
            return p_ / (1 + e_ * mp.cos(c))

        def dlr(c):
            r = r_of(c)
            return mp.sqrt(1 - e_ * e_) / ((1 + e_ * mp.cos(c)) * mp.sqrt(one * (r - r3) * (r - r4)))

        def dlt(c):
            return 1 / mp.sqrt(bzp - beta * zm * mp.cos(c) ** 2)
        Lr = 2 * mp.quad(dlr, [0, mp.pi])
        Lt = 4 * mp.quad(dlt, [0, mp.pi / 2])

        def P_(r):
            return E * (r * r + a * a) - a * L
        tr = 2 * mp.quad(lambda c: (r_of(c) ** 2 + a * a) / (r_of(c) ** 2 - 2 * r_of(c) + a * a) * P_(r_of(c))
                         * dlr(c), [0, mp.pi]) / Lr
        pr = 2 * mp.quad(lambda c: a / (r_of(c) ** 2 - 2 * r_of(c) + a * a) * P_(r_of(c)) * dlr(c), [0, mp.pi]) / Lr
        s2 = 4 * mp.quad(lambda c: (1 - zm * mp.cos(c) ** 2) * dlt(c), [0, mp.pi / 2]) / Lt
        cs2 = 4 * mp.quad(lambda c: dlt(c) / (1 - zm * mp.cos(c) ** 2), [0, mp.pi / 2]) / Lt
        gam = tr - a * a * E * s2 + a * L
        uphi = pr + L * cs2 - a * E
        ur, ut = 2 * mp.pi / Lr, 2 * mp.pi / Lt
        return {"Upsilon_r": ur, "Upsilon_theta": ut, "Upsilon_phi": uphi, "Gamma": gam, "Omega_r": ur / gam,
                "Omega_theta": ut / gam, "Omega_phi": uphi / gam}


FREQ_KEYS = ("Upsilon_r", "Upsilon_theta", "Upsilon_phi", "Gamma", "Omega_r", "Omega_theta", "Omega_phi")


def _freq_sensitivities(chi, p, e, x):
    """|v dF/dv| for v = p, e, x (total) and |c dF/dc|, |dF/dc| for c = E, L, Q (partial), per key."""
    o = KO.KerrOrbit(chi, p, e, x)
    base = o.frequencies()
    inp = {k: 0.0 for k in FREQ_KEYS}
    for i, v in enumerate((p, e, x)):
        h = 1e-6 * abs(v)
        lo, hi = [p, e, x], [p, e, x]
        lo[i], hi[i] = v - h, v + h
        fl, fh = KO.KerrOrbit(chi, *lo).frequencies(), KO.KerrOrbit(chi, *hi).frequencies()
        for k in FREQ_KEYS:
            inp[k] += abs(v) * abs(fh[k] - fl[k]) / (2 * h)
    dc = {k: [0.0, 0.0, 0.0] for k in FREQ_KEYS}
    c = [o.E, o.L, o.Q]
    for i, v in enumerate(c):
        h = 1e-7 * abs(v)
        lo, hi = list(c), list(c)
        lo[i], hi[i] = v - h, v + h
        fl = KO.KerrOrbit(chi, p, e, x, consts=lo).frequencies()
        fh = KO.KerrOrbit(chi, p, e, x, consts=hi).frequencies()
        for k in FREQ_KEYS:
            dc[k][i] = abs(fh[k] - fl[k]) / (2 * h)
    return o, base, inp, dc


def _generic_frequency_rows():
    out = []
    B = 256 * U
    for a in (0.3, 0.9, 0.99):
        for e in GENERIC_E:
            for x in (0.9, 0.1, -0.4):
                for p in (1.3 * kc.separatrix(a, e, x), 25.0):
                    p = float(p)
                    o, eng, inp, dc = _freq_sensitivities(a, p, e, x)
                    c = (o.E, o.L, o.Q)
                    lib_c = kc.constants_of_motion(a, p, e, x)
                    with library_bounded_generic():
                        Eb = kc.energy(Fe(a), Fe(p), Fe(e), Fe(x))
                        Lb = kc.angular_momentum(Fe(a), Fe(p), Fe(e), Fe(x), E=Eb)
                        Qb = kc.carter_constant(Fe(a), Fe(p), Fe(e), Fe(x), E=Eb, L=Lb)
                    e_lib = (Eb.e, Lb.e, Qb.e)
                    ur, uth, uphi, gam = kf.mino_frequencies(a, p, e, x)
                    om = kf.fundamental_frequencies(a, p, e, x)
                    lib = {"Upsilon_r": ur, "Upsilon_theta": uth, "Upsilon_phi": uphi, "Gamma": gam,
                           "Omega_r": om[0], "Omega_theta": om[1], "Omega_phi": om[2]}
                    ex = exact_generic_frequencies(a, p, e, x, c)
                    lab = f"chi={a}, p={p:.6g}, e={e}, x={x}"
                    for k in FREQ_KEYS:
                        rep = sum(abs(ci) * d for ci, d in zip(c, dc[k]))
                        tol_eng = B * (inp[k] + rep + abs(eng[k]))
                        tol_lib = sum(d * el for d, el in zip(dc[k], e_lib)) + B * (rep + abs(eng[k]))
                        out.append(Row(GROUP, f"generic orbit {k}", lab, eng[k], float(lib[k]), tol_eng + tol_lib,
                                       "sensitivity budget", float(abs(eng[k] - ex[k])),
                                       float(abs(float(lib[k]) - ex[k]))))
                    del lib_c
    return out


@functools.lru_cache(maxsize=None)
@mp.workdps(DPS)
def rows() -> list[Row]:
    return (_separatrix_rows() + _circular_rows() + _horizon_rows() + _eccentric_rows() + _generic_constant_rows()
            + _generic_frequency_rows())


@pytest.mark.parametrize("row", params(rows()))
def test_kerr(row):
    check(row)


@mp.workdps(DPS)
def test_exact_references_are_roots():
    """The mpmath references used for the attribution are the roots KerrGeoPy looks for: the exact ISCO and 2 r_mb are
    zeros of the separatrix polynomial (to 50 digits)."""
    for chi in (0.3, 0.9, 1 - 1e-9):
        for pro in (True, False):
            assert abs(s_exact(isco_exact(chi, pro), chi, 0)) < mp.mpf(10) ** -40
            assert abs(s_exact(2 * mb_exact(chi, pro), chi, 1)) < mp.mpf(10) ** -40
