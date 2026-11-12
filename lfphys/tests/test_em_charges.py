# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.core.em.charges: every route against a closed form or an independent method, with negative controls where
a test checks a tolerance."""

import math

import mpmath
import numpy as np
import pytest
from scipy import integrate, special

from lfphys.core.em import charges as ch

Q = 1.602176634e-19
C = ch.C


def _sphere(f, n=96):
    """int f(n) dOmega by Gauss–Legendre in cos(theta) x uniform phi (f vectorised over (..., 3))."""
    xg, wg = np.polynomial.legendre.leggauss(n)
    ph = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False)
    TH, PH = np.meshgrid(np.arccos(xg), ph, indexing="ij")
    nv = np.stack([np.sin(TH) * np.cos(PH), np.sin(TH) * np.sin(PH), np.cos(TH)], -1)
    return float(np.sum(f(nv) * wg[:, None]) * (2 * np.pi / (2 * n)))


# --- static and uniform motion --------------------------------------------------------------------------------------------
def test_static_charge_is_coulomb():
    w = ch.uniform([0.1, -0.2, 0.3], [0, 0, 0])
    x = np.random.default_rng(0).normal(size=(40, 3))
    E, B = ch.fields(ch.Charge(Q, w), x, 7.0)
    d = x - [0.1, -0.2, 0.3]
    r = np.linalg.norm(d, axis=1)
    assert np.max(np.linalg.norm(E - Q * ch.K_E * d / r[:, None] ** 3, axis=1) / (Q * ch.K_E / r ** 2)) < 1e-14
    assert np.max(np.linalg.norm(B, axis=1) * C / np.linalg.norm(E, axis=1)) < 1e-15  # n x E of parallel vectors
    phi, A = ch.potentials(ch.Charge(Q, w), x, 7.0)
    assert np.max(np.abs(phi * r / (Q * ch.K_E) - 1)) < 1e-14 and np.max(np.abs(A)) == 0


@pytest.mark.parametrize("beta", [(0.3, 0.0, 0.0), (0.3, 0.5, 0.6), (0.0, 0.0, 0.99), (0.9999, 0.0, 0.0)])
def test_uniform_motion_against_heaviside(beta):
    v = np.array(beta) * C
    w = ch.uniform([0.1, 0.0, 0.0], v)
    pts = np.random.default_rng(1).normal(size=(60, 3))
    t = 2e-9
    E, B = ch.fields(ch.Charge(Q, w), pts, t)
    Eh, Bh = ch.heaviside_field(Q, w.position(t), v, pts)
    err = np.max(np.linalg.norm(E - Eh, axis=1) / np.linalg.norm(Eh, axis=1))
    assert err < 1e-10
    assert np.max(np.linalg.norm(B - Bh, axis=1) / np.linalg.norm(Bh, axis=1)) < 1e-10
    # negative control: the Coulomb field of the PRESENT position (no relativistic flattening) misses by O(beta^2)
    d = pts - w.position(t)
    Ec = Q * ch.K_E * d / np.linalg.norm(d, axis=1)[:, None] ** 3
    assert np.max(np.linalg.norm(Ec - Eh, axis=1) / np.linalg.norm(Eh, axis=1)) > 1e3 * max(err, 1e-14)


def test_velocity_and_acceleration_parts_split():
    """The acceleration part vanishes for uniform motion; for an accelerated charge it falls as 1/R and the velocity
    part as 1/R^2 (the field at 10x the distance along a ray)."""
    w = ch.uniform([0, 0, 0], [0.5 * C, 0, 0])
    p = ch.fields(ch.Charge(Q, w), np.array([[1.0, 2.0, 0.5]]), 1e-9, parts=True)
    assert np.max(np.abs(p["E_acc"])) == 0
    wc = ch.circular(1.0, 0.6 * C)
    n = np.array([0.3, 0.4, np.sqrt(0.75)])
    r1, r2 = 1e3, 1e4
    p1 = ch.fields(ch.Charge(Q, wc), (r1 * n)[None], r1 / C + 1e-9, parts=True)
    p2 = ch.fields(ch.Charge(Q, wc), (r2 * n)[None], r2 / C + 1e-9, parts=True)
    a1, a2 = np.linalg.norm(p1["E_acc"]), np.linalg.norm(p2["E_acc"])
    v1, v2 = np.linalg.norm(p1["E_vel"]), np.linalg.norm(p2["E_vel"])
    assert a1 / a2 == pytest.approx(10, rel=2e-2) and v1 / v2 == pytest.approx(100, rel=4e-2)


# --- retarded time ------------------------------------------------------------------------------------------------------
def test_retarded_time_solves_the_light_cone_condition_uniquely():
    w = ch.hyperbolic(3e15, direction=(1, 1, 0))  # c^2/g = 30 m: points within metres at t >= 0 see the charge
    x = np.random.default_rng(2).normal(size=(500, 3)) * 3.0
    t = np.random.default_rng(3).uniform(0, 1e-7, 500)
    tr = ch.retarded_time(w, x, t)
    R = np.linalg.norm(x - w.position(tr), axis=1)
    assert np.max(np.abs(C * (t - tr) - R) / R) < 1e-14
    # uniqueness: g(tau) = c tau - |x - r(t - tau)| is increasing (g' = c - n.v > 0) — sampled on a grid
    tau = np.linspace(0, 2e-7, 4001)
    g = C * tau[:, None] - np.linalg.norm(x[None, :50] - w.position(t[None, :50] - tau[:, None]), axis=-1)
    assert np.all(np.diff(g, axis=0) > 0)
    # beyond the horizon of hyperbolic motion there is no retarded time: reported, not guessed
    for cf in (True, False):
        with pytest.raises(ValueError):
            ch.retarded_time(w, np.array([[-70.0, -70.0, 0.0]]), 0.0, closed_form=cf)  # x.e + c^2/g < -c t


def test_large_times_resolve_the_delay_to_the_rounding_of_g():
    """At t = 1e6 s the worldline is evaluated at t' = t - tau, rounded to ulp(t) = 1.2e-10 s: the charge's position is
    known only to |v| ulp(t) (1.7 cm here), and no solver can do better (review B8 C4, C16: the former name "lose no
    digits" was wrong). What holds: |g| at the returned time is within its rounding bound B, and the returned error bound
    includes ulp(t)."""
    w = ch.circular(1.0, 0.5 * C)
    x = np.array([[3.0, 1.0, 2.0]])
    for t0 in (0.0, 1e6):
        tr, err = ch.retarded_time(w, x, t0, full=True)
        gv, dg, B, _ = ch._g_eval(w, x, np.array([t0]), np.array([t0]) - tr)
        assert abs(gv[0]) <= B[0] and err[0] >= np.spacing(t0) and err[0] <= 2 * B[0] / dg[0] + 2 * np.spacing(max(t0, 1e-300))
        if t0:
            assert 0.5 * C * err[0] > 1e-3  # the position uncertainty |v| err is centimetres at t = 1e6 s: reported
    ts = np.linspace(0, 1e-8, 200)
    sw = ch.SampledWorldline(ts, w.position(ts), *w.state(ts)[1:])
    with pytest.raises(ValueError):
        ch.retarded_time(sw, np.array([[100.0, 0, 0]]), 5e-9)  # needs t' < 0: outside the samples


# --- retarded time: the review B8 cases (C1 horizon, C4 far from the origin, C5 sampled domain) ---------------------------
def _hyp_reference(w, x, t):
    """50-digit retarded time of the same float worldline (its float c^2/g, r0, e, t0), by bisection in the rapidity of
    the retarded point: an independent route to the closed form."""
    mpmath.mp.dps = 50
    a = mpmath.mpf(float(C * C / w.g))
    X = [mpmath.mpf(float(xi)) - mpmath.mpf(float(ri)) for xi, ri in zip(x, w.r0)]
    e = [mpmath.mpf(float(v)) for v in w.e]
    Z = sum(X[i] * e[i] for i in range(3))
    rho2 = sum((X[i] - Z * e[i]) ** 2 for i in range(3))
    T = mpmath.mpf(float(t)) - mpmath.mpf(w.t0)
    cc = mpmath.mpf(C)

    def F(eta):  # g(tau(eta)), decreasing in eta
        return cc * (T - a * mpmath.sinh(eta) / cc) - mpmath.sqrt(rho2 + (Z - a * (mpmath.cosh(eta) - 1)) ** 2)
    hi = mpmath.asinh(cc * T / a)
    lo = hi - 1
    while F(lo) < 0:
        lo -= 2 * (hi - lo)
    for _ in range(300):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if F(mid) > 0 else (lo, mid)
    return float(mpmath.mpf(w.t0) + a * mpmath.sinh((lo + hi) / 2) / cc)


@pytest.mark.parametrize("T", [0.0, 5e-8])
def test_hyperbolic_retarded_time_near_the_horizon(T):
    """Review B8 C1: the general solver returned retarded times beyond the horizon of hyperbolic motion (56-59 of 60
    points at depths 1 mm - 1 m) and 100 % wrong ones just inside it. Now: the closed form agrees with 50 digits within
    its bound down to 1e-9 m inside; the general solver either agrees within its bound or refuses; beyond the horizon
    both refuse every point."""
    w = ch.hyperbolic(3e15, direction=(1, 0, 0))  # c^2/g = 30 m
    a = C * C / w.g
    for rho in (0.0, 5.0, 20.0):
        for depth in (1.0, 1e-1, 1e-2, 1e-3, 1e-4, 1e-6, 1e-9):
            x = np.array([-a - C * T + depth, rho, 0.0])
            ref = _hyp_reference(w, x, T)
            tc, ec = ch.retarded_time(w, x[None], T, full=True)
            assert abs(tc[0] - ref) <= ec[0], (rho, depth)
            # not vacuous: the bound is the rounding of the horizon distance, 2 eps (|Z| + c^2/g + c|t|) ~ 3e-14 m, over the
            # depth (and a few eps), in units of the delay
            assert ec[0] <= (1e-13 / depth + 1e-12) * abs(ref)
            tg, eg = ch.retarded_time(w, x[None], T, full=True, closed_form=False, on_fail="nan")
            if depth >= 1e-3:
                assert np.isfinite(tg[0]) and eg[0] < 1e-5 * abs(ref)  # resolvable: solved
            if np.isfinite(tg[0]):
                assert abs(tg[0] - ref) <= eg[0], (rho, depth)
    rng = np.random.default_rng(0)
    for depth in (1e-9, 1e-6, 1e-3, 0.1, 1.0, 10.0):
        x = np.stack([np.full(60, -a - C * T - depth), rng.uniform(-20, 20, 60), rng.uniform(-20, 20, 60)], 1)
        for cf in (True, False):
            assert np.all(np.isnan(ch.retarded_time(w, x, T, on_fail="nan", closed_form=cf)))
    # negative control: the root the former solver returned 1 m beyond the horizon on the axis (t_ret = -5.813385e7 s,
    # REVIEW c02 C) is a sign change of g far below its rounding bound — rounding, not a root
    gv, _, B, _ = ch._g_eval(w, np.array([[-a - 1.0, 0.0, 0.0]]), np.array([0.0]), np.array([5.813385e7]))
    assert abs(gv[0]) < 1e-3 * B[0] and B[0] > 10.0


def test_far_from_the_origin_every_point_converges_within_its_bound():
    """Review B8 C4: at t = 1 s (the charge 3e8 m from the origin, beta = 0.99) one of 400 points never converged and
    aborted the whole call. Now all converge; the exact retarded time of uniform motion (a quadratic, 50 digits) lies
    within the returned bound, which is the rounding of g over its slope."""
    v = np.array([0.99 * C, 0, 0])
    w = ch.uniform([0, 0, 0], v)
    t = 1.0
    rp = w.position(np.array(t))
    pts = rp + np.random.default_rng(5).normal(size=(400, 3))
    tr, err = ch.retarded_time(w, pts, t, full=True)
    mpmath.mp.dps = 50
    cc, T = mpmath.mpf(C), mpmath.mpf(t)
    V = [mpmath.mpf(float(c)) for c in v]
    dev = []
    for p, tri in zip(pts, tr):
        X = [mpmath.mpf(float(c)) for c in p]
        A2 = sum(c * c for c in V) - cc * cc
        B2 = -2 * sum(X[i] * V[i] for i in range(3)) + 2 * cc * cc * T
        C2 = sum(c * c for c in X) - cc * cc * T * T
        roots = [(-B2 + s * mpmath.sqrt(B2 * B2 - 4 * A2 * C2)) / (2 * A2) for s in (1, -1)]
        dev.append(abs(tri - float([r for r in roots if r < T][0])))
    dev = np.array(dev)
    assert np.all(dev <= err)
    assert np.max(err) < 1e-12 and np.max(dev) < 1e-13  # measured 4e-13 and 1.3e-14 s (delays ~3 ns)
    E, _ = ch.fields(ch.Charge(Q, w), pts, t)
    Eh, _ = ch.heaviside_field(Q, rp, v, pts)
    assert np.max(np.linalg.norm(E - Eh, axis=1) / np.linalg.norm(Eh, axis=1)) < 1e-5  # measured 1.2e-6


def test_one_point_does_not_abort_the_others():
    w = ch.hyperbolic(3e15, direction=(1, 0, 0))
    a = C * C / w.g
    x = np.array([[0.0, 1.0, 0.0], [-a - 1.0, 0.0, 0.0], [2.0, 0.0, 1.0]])  # the middle one is beyond the horizon
    tr = ch.retarded_time(w, x, 0.0, on_fail="nan")
    assert np.isfinite(tr[0]) and np.isnan(tr[1]) and np.isfinite(tr[2])
    with pytest.raises(ValueError, match="1 of 3 points refused"):
        ch.retarded_time(w, x, 0.0)
    E, _ = ch.fields(ch.Charge(Q, w), x, 0.0, on_fail="nan")
    assert np.all(np.isfinite(E[[0, 2]])) and np.all(np.isnan(E[1]))


def test_sampled_worldline_retarded_time_inside_the_domain():
    """Review B8 C5: a sampled worldline refused retarded times inside its domain when the present distance / c reached
    before it (the bracket's upper end was tested against the domain before g was evaluated). Now the bracket is clamped
    to the domain; a field time after the domain's end is also served when the retarded time is inside."""
    w = ch.uniform([0, 0, 0], [0.9 * C, 0, 0])
    ts = np.linspace(0, 1e-8, 200)
    sw = ch.SampledWorldline(ts, w.position(ts), *w.state(ts)[1:])
    for x, t in (([-1.5, 0, 0], 8e-9), ([-2.3, 0, 0], 9.9e-9), ([-0.2, 0, 0], 9e-9), ([-3.0, 0, 0], 1.2e-8)):
        a = ch.retarded_time(sw, np.array([x]), t)[0]
        b = ch.retarded_time(w, np.array([x]), t)[0]
        assert 0 < b < 1e-8 and abs(a - b) < 1e-20
    for x, t in (([100.0, 0, 0], 5e-9), ([5.0, 0, 0], 1.2e-8)):  # the retarded times lie before the samples
        with pytest.raises(ValueError, match="before the worldline's domain"):
            ch.retarded_time(sw, np.array([x]), t)


def test_positions_only_worldline_needs_a_step_and_reports_its_error():
    """Review B8 C2: positions only, the former default step 1e-3 s was 100 % wrong for an orbit of period 42 ns, without
    a warning. Now a step or time scale is required; the estimate (truncation and rounding) covers the true error; the
    field is refused when the derivative error would change it by more than rtol."""
    ref = ch.circular(1.0, 0.5 * C)
    om = 0.5 * C
    with pytest.raises(ValueError):
        ch.FunctionWorldline(ref.r)
    tq = np.array([1e-9, 2e-9, 5e-9])
    r0, v0, a0 = ref.state(tq)
    x = np.array([[3.0, 1.0, 2.0], [0.5, -4.0, 1.0]])
    E0, _ = ch.fields(ch.Charge(Q, ref), x, 2e-8)
    for kw in ({"timescale": 1 / om}, {"h": 1e-12}):
        fw = ch.FunctionWorldline(ref.r, None, None, **kw)
        _, v1, a1 = fw.state(tq)
        ev, ea = fw.derivative_errors(tq)
        tv, ta = np.linalg.norm(v1 - v0, axis=1), np.linalg.norm(a1 - a0, axis=1)
        assert np.all(ev >= tv) and np.all(ea >= ta) and np.all(ev < 100 * tv + 1e-3) and np.all(ea < 100 * ta)
        E1, _ = ch.fields(ch.Charge(Q, fw), x, 2e-8)
        assert np.max(np.linalg.norm(E1 - E0, axis=1) / np.linalg.norm(E0, axis=1)) < 1e-8  # measured 1e-11, 6e-9
    # negative control: a step of a tenth of the time scale (v off by 3e-6) is estimated and refused by fields
    fw = ch.FunctionWorldline(ref.r, None, None, h=0.1 / om)
    _, v1, _ = fw.state(tq)
    assert np.max(fw.derivative_errors(tq)[0]) >= 0.9 * np.max(np.linalg.norm(v1 - v0, axis=1)) > 100.0
    with pytest.raises(ValueError, match="finite-difference"):
        ch.fields(ch.Charge(Q, fw), x, 2e-8)
    # ... and at t = 1 s the argument t +- h is rounded to ulp(1 s): the rounding term refuses it
    with pytest.raises(ValueError, match="finite-difference"):
        ch.fields(ch.Charge(Q, ch.FunctionWorldline(ref.r, timescale=1 / om)), x[:1], 1.0)


def test_double_precision_loses_gamma_squared_eps():
    """Review B8 C11: beta enters as a float, so 1 - beta^2 and 1 - n.beta lose digits: the field of uniform motion
    against Heaviside's in 50 digits (the same float inputs) errs by about 1e-16 gamma^2 (the validity's statement)."""
    mpmath.mp.dps = 50
    errs = {}
    for gam in (1e2, 1e4, 1e6):
        b = math.sqrt(1 - 1 / gam ** 2)
        v = np.array([b * C, 0.0, 0.0])
        w = ch.uniform([0, 0, 0], v)
        pts = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.7, 0.4, -0.2]])
        E, _ = ch.fields(ch.Charge(Q, w), pts, 0.0)
        worst = 0.0
        for p, e in zip(pts, E):
            d = [mpmath.mpf(float(c)) for c in p]
            vv = [mpmath.mpf(float(c)) for c in v]
            b2 = sum(c * c for c in vv) / mpmath.mpf(C) ** 2
            R = mpmath.sqrt(sum(c * c for c in d))
            cos = sum(d[i] * vv[i] for i in range(3)) / (R * mpmath.sqrt(sum(c * c for c in vv)))
            f = mpmath.mpf(Q) * mpmath.mpf(ch.K_E) * (1 - b2) / (R ** 3 * (1 - b2 * (1 - cos ** 2)) ** 1.5)
            ref = np.array([float(f * c) for c in d])
            worst = max(worst, float(np.linalg.norm(e - ref) / np.linalg.norm(ref)))
        errs[gam] = worst
    assert errs[1e2] < 1e-11 and errs[1e4] < 100 * ch.EPS * 1e8 and errs[1e6] < 100 * ch.EPS * 1e12
    assert errs[1e6] > 1e-8  # the loss is real (measured ~1e-4 by the review), not an artefact of the bound


def test_sampled_worldline_interpolation_and_its_error_estimate():
    # quintic Hermite is exact for a quintic polynomial
    ts = np.linspace(0, 1e-8, 13)
    cf = np.array([[0.1, 2e7, -3e14, 1e22, -2e29, 4e36], [0.0, 1e7, 2e14, 0, 3e29, 0], [1.0, 0, 0, 0, 0, 1e37]])

    def poly(t, d=0):
        t = np.asarray(t, float)
        out = np.zeros(t.shape + (3,))
        for i in range(d, 6):
            out += cf[:, i] * (math.factorial(i) / math.factorial(i - d)) * t[..., None] ** (i - d)
        return out
    sw = ch.SampledWorldline(ts, poly(ts), poly(ts, 1), poly(ts, 2))
    tt = np.linspace(0, 1e-8, 97)
    r, v, a = sw.state(tt)
    assert np.max(np.abs(r - poly(tt))) < 1e-12 and np.max(np.abs(a - poly(tt, 2)) / np.max(np.abs(poly(tt, 2)))) < 1e-9
    # circular motion sampled: the estimated error is the measured one to within a factor 4 (r, v, a)
    w = ch.circular(1.0, 0.5 * C)
    T = 2 * np.pi / (0.5 * C)
    for kind in ("rva", "r"):
        ts = np.linspace(0, T, 81)
        rr, vv, aa = w.state(ts)
        sw = ch.SampledWorldline(ts, rr, vv if kind == "rva" else None, aa if kind == "rva" else None)
        est = sw.interpolation_error()["estimate"]
        tt = np.linspace(ts[0], ts[-1], 4001)
        r1, v1, a1 = sw.state(tt)
        r0, v0, a0 = w.state(tt)
        true = {"r": np.max(np.linalg.norm(r1 - r0, axis=1)), "v": np.max(np.linalg.norm(v1 - v0, axis=1)),
                "a": np.max(np.linalg.norm(a1 - a0, axis=1))}
        for key, e in est.items():
            assert true[key] / 4 < e < 4 * true[key], (kind, key, e, true[key])


# --- Maxwell's equations by finite differences ---------------------------------------------------------------------------
def _maxwell_residuals(charge, pts, t, h, use=("E", "B")):
    """Fourth-order central differences: div E, div B, curl E + dB/dt, curl B - dE/dt / c^2 at the points, each
    relative to the size of the terms (|E|/h scale replaced by the norms of the derivatives)."""
    def F(x, tt):
        p = ch.fields(charge, x, tt, parts=True)
        return p[use[0]], p[use[1]]
    c4 = np.array([1, -8, 0, 8, -1]) / 12.0
    offs = np.array([-2, -1, 0, 1, 2])
    J = {}
    for name, idx in (("E", 0), ("B", 1)):
        J[name] = np.zeros(pts.shape + (3,))
    for ax in range(3):
        acc_E = acc_B = 0
        for o, cc in zip(offs, c4):
            if cc == 0:
                continue
            x = pts.copy()
            x[:, ax] += o * h
            E, B = F(x, t)
            acc_E = acc_E + cc * E
            acc_B = acc_B + cc * B
        J["E"][:, :, ax] = acc_E / h  # dE_i/dx_ax
        J["B"][:, :, ax] = acc_B / h
    dt = h / C
    dEt = dBt = 0
    for o, cc in zip(offs, c4):
        if cc == 0:
            continue
        E, B = F(pts, t + o * dt)
        dEt = dEt + cc * E / dt
        dBt = dBt + cc * B / dt

    def curl(Jm):
        return np.stack([Jm[:, 2, 1] - Jm[:, 1, 2], Jm[:, 0, 2] - Jm[:, 2, 0], Jm[:, 1, 0] - Jm[:, 0, 1]], -1)
    divE = np.einsum("pii->p", J["E"])
    divB = np.einsum("pii->p", J["B"])
    sE = np.linalg.norm(J["E"].reshape(len(pts), -1), axis=1)
    sB = np.linalg.norm(J["B"].reshape(len(pts), -1), axis=1)
    far = np.linalg.norm(curl(J["E"]) + dBt, axis=1) / (sE + np.linalg.norm(dBt, axis=1))
    amp = np.linalg.norm(curl(J["B"]) - dEt / C ** 2, axis=1) / (sB + np.linalg.norm(dEt, axis=1) / C ** 2)
    return np.abs(divE) / sE, np.abs(divB) / sB, far, amp


def test_fields_satisfy_maxwell_equations_away_from_the_charge():
    w = ch.circular(1.0, 0.7 * C)  # beta = 0.7: both parts of the field matter
    rng = np.random.default_rng(4)
    pts = rng.normal(size=(12, 3)) * 4
    pts = pts[np.linalg.norm(pts, axis=1) > 2.5]
    res = _maxwell_residuals(ch.Charge(Q, w), pts, 3e-9, 2e-3)
    for r in res:
        assert np.max(r) < 1e-8, [float(np.max(x)) for x in res]
    # negative control: the radiation part of B left out (B_vel with E) breaks Faraday's and Ampere's laws
    neg = _maxwell_residuals(ch.Charge(Q, w), pts, 3e-9, 2e-3, use=("E", "B_vel"))
    assert np.max(neg[2]) > 1e-2


# --- radiated power ------------------------------------------------------------------------------------------------------
def test_larmor_is_the_integral_of_the_dipole_pattern():
    a = np.array([1e17, -2e17, 3e16])
    P = ch.larmor_power(Q, a)
    Pi = _sphere(lambda n: ch.angular_power(Q, np.zeros(3), a, n))
    assert Pi / P - 1 == pytest.approx(0, abs=1e-13)
    assert ch.lienard_power(Q, np.zeros(3), a) == pytest.approx(P, rel=1e-15)


@pytest.mark.parametrize("case", ["linear", "circular", "general"])
def test_lienard_is_the_integral_over_retarded_time(case):
    b = 0.9
    if case == "linear":
        v, a = np.array([0, 0, b * C]), np.array([0, 0, 1e18])
        ref = Q * Q * (1 / (1 - b * b)) ** 3 * 1e36 / (6 * math.pi * ch.EPS0 * C ** 3)  # gamma^6 a^2
    elif case == "circular":
        v, a = np.array([b * C, 0, 0]), np.array([0, 1e18, 0])
        ref = Q * Q * (1 / (1 - b * b)) ** 2 * 1e36 / (6 * math.pi * ch.EPS0 * C ** 3)  # gamma^4 a^2
    else:
        v, a = np.array([0.5, 0.2, -0.3]) * C, np.array([3e17, -1e17, 2e17])
        ref = ch.lienard_power(Q, v, a)
    P = ch.lienard_power(Q, v, a)
    assert P == pytest.approx(ref, rel=1e-14)
    Pi = _sphere(lambda n: ch.angular_power(Q, v, a, n, per="retarded"), n=400)
    assert Pi / P - 1 == pytest.approx(0, abs=1e-10)
    # negative control: the pattern per unit OBSERVER time does not integrate to Liénard's power
    Po = _sphere(lambda n: ch.angular_power(Q, v, a, n, per="observer"), n=400)
    assert abs(Po / P - 1) > 0.1


def test_energy_flux_through_a_large_sphere_is_the_power_at_the_retarded_time():
    """The sphere of radius R about r(t'), at t = t' + R/c, lies on the light cone of the event t': every point has the
    retarded time t'. R^2 S.n (1 - n.beta) integrated over it -> Liénard's P(t') as R grows (the velocity field adds
    O(c^2 / (a R))); the unweighted flux is the power per unit observer time."""
    w = ch.circular(1.0, 0.6 * C)
    tp = 1.3e-9
    r0, v0, a0 = w.state(np.array(tp))
    P = ch.lienard_power(Q, v0, a0)
    errs = []
    for R in (1e3, 1e4):
        def flux(n, weight=True):
            x = r0 + R * n
            E, B = ch.fields(ch.Charge(Q, w), x, tp + R / C)
            S = np.cross(E, B) / ch.MU0
            f = R * R * np.einsum("...i,...i->...", S, n)
            return f * (1 - np.einsum("...i,...i->...", n, v0 / C)) if weight else f
        errs.append(abs(_sphere(flux, n=200) / P - 1))
    assert errs[1] < 2e-4 and errs[1] < errs[0] / 5  # ~1/R
    Po = _sphere(lambda n: ch.angular_power(Q, v0, a0, n, per="observer"), n=200)
    R = 1e4
    unweighted = _sphere(lambda n: R * R * np.einsum("...i,...i->...", np.cross(*ch.fields(ch.Charge(Q, w), r0 + R * n,
                                                                                          tp + R / C)) / ch.MU0, n),
                         n=200)
    assert unweighted / Po - 1 == pytest.approx(0, abs=2e-4)
    assert abs(unweighted / P - 1) > 0.05  # negative control: it is not Liénard's power


def test_superposition_of_charges():
    w = ch.circular(1.0, 0.5 * C)
    x = np.random.default_rng(5).normal(size=(10, 3)) * 5
    E, B = ch.fields([ch.Charge(Q, w), ch.Charge(-Q, w)], x, 2e-9)
    assert np.max(np.abs(E)) == 0 and np.max(np.abs(B)) == 0
    E1, _ = ch.fields(ch.Charge(Q, w), x, 2e-9)
    E2, _ = ch.fields([ch.Charge(Q, w), ch.Charge(2 * Q, w)], x, 2e-9)
    assert np.max(np.abs(E2 - 3 * E1)) <= 1e-15 * np.max(np.abs(E1))


# --- synchrotron radiation ----------------------------------------------------------------------------------------------
def test_F_against_mpmath_and_its_integral():
    mpmath.mp.dps = 30
    for x in (1e-6, 1e-3, 0.1, 1.0, 3.0, 10.0, 40.0):
        ref = x * mpmath.quad(lambda s: mpmath.besselk(mpmath.mpf(5) / 3, s), [x, x + 0.5, x + 2, x + 8, mpmath.inf])
        assert float(ch.synchrotron_F(x)) == pytest.approx(float(ref), rel=1e-13)
    I = integrate.quad(ch.synchrotron_F, 0, 1, limit=200, epsabs=0, epsrel=1e-12)[0] + \
        integrate.quad(ch.synchrotron_F, 1, 60, limit=200, epsabs=0, epsrel=1e-12)[0]
    assert I == pytest.approx(8 * math.pi / (9 * math.sqrt(3)), rel=1e-10)
    IG = integrate.quad(ch.synchrotron_G, 0, 60, limit=200, epsrel=1e-12)[0]
    assert IG == pytest.approx(2 * math.pi / (3 * math.sqrt(3)), rel=1e-10)  # int x K_{2/3} = Gamma(2/3) Gamma(4/3)


def test_F_asymptotes():
    for x in (1e-8, 1e-6):  # F ~ (4 pi / (sqrt 3 Gamma(1/3))) (x/2)^(1/3)
        small = 4 * math.pi / (math.sqrt(3) * special.gamma(1 / 3)) * (x / 2) ** (1 / 3)
        assert float(ch.synchrotron_F(x)) / small - 1 == pytest.approx(0, abs=5 * x ** (2 / 3))
    errs = []
    for x in (20.0, 80.0):  # F ~ sqrt(pi x / 2) exp(-x) (1 + O(1/x))
        big = math.sqrt(math.pi * x / 2) * math.exp(-x)
        errs.append(abs(float(ch.synchrotron_F(x)) / big - 1))
    assert errs[0] < 0.1 and errs[1] < errs[0] / 3.5
    # negative control: the small-x form is wrong at x = 1
    assert abs(float(ch.synchrotron_F(1.0)) / (4 * math.pi / (math.sqrt(3) * special.gamma(1 / 3)) * 0.5 ** (1 / 3))
               - 1) > 0.3


def test_synchrotron_spectrum_integrates_to_lienard_power_and_splits_seven_to_one():
    gam, rho = 2000.0, 10.0
    wc = ch.critical_frequency(gam, rho)
    assert wc == pytest.approx(1.5 * gam ** 3 * C / rho, rel=1e-15)
    f = lambda y, comp: ch.synchrotron_spectrum(Q, gam, rho, y * wc, comp) * wc  # noqa: E731
    tot = sum(integrate.quad(lambda y: f(y, "total"), a, b, limit=200, epsabs=0, epsrel=1e-12)[0] for a, b in ((0, 1), (1, 60)))
    beta = math.sqrt(1 - 1 / gam ** 2)
    a = beta * beta * C * C / rho
    PL = ch.lienard_power(Q, np.array([beta * C, 0, 0]), np.array([0, a, 0]))
    assert tot / PL - 1 == pytest.approx(0, abs=1e-9)
    sig = sum(integrate.quad(lambda y: f(y, "sigma"), a_, b_, limit=200, epsabs=0, epsrel=1e-12)[0] for a_, b_ in ((0, 1), (1, 60)))
    pi_ = sum(integrate.quad(lambda y: f(y, "pi"), a_, b_, limit=200, epsabs=0, epsrel=1e-12)[0] for a_, b_ in ((0, 1), (1, 60)))
    assert sig / pi_ == pytest.approx(7.0, rel=1e-8) and (sig + pi_) / tot == pytest.approx(1, rel=1e-12)
    # half the power below omega_c (the definition of the critical frequency)
    below = integrate.quad(lambda y: f(y, "total"), 0, 1, limit=200, epsabs=0, epsrel=1e-12)[0]
    assert below / tot == pytest.approx(0.5, abs=1e-5)  # measured 0.5000053 (the halving is not exact)


@pytest.mark.parametrize("y", [0.3, 1.0, 3.0])
def test_angular_spectral_distribution_integrates_to_the_spectrum(y):
    """The booklet's K_{2/3}, K_{1/3} form integrated over the vertical angle against the (F +- G) forms: two routes.
    Both are ultrarelativistic; their beta factors differ by O(1/gamma^2) (measured 1.5e-6 at gamma = 1000), so the
    comparison is made at gamma = 1e5."""
    gam, rho = 1e5, 10.0
    om = y * ch.critical_frequency(gam, rho)
    for comp, idx in (("sigma", 0), ("pi", 1)):
        val = 2 * integrate.quad(lambda X: ch.synchrotron_angular_spectrum(Q, gam, rho, om, X / gam)[idx] / gam, 0,
                                 np.inf, limit=400, epsabs=0, epsrel=1e-11)[0]
        assert val / ch.synchrotron_spectrum(Q, gam, rho, om, comp) - 1 == pytest.approx(0, abs=1e-9)


# --- cyclotron harmonics (Schott) ---------------------------------------------------------------------------------------
@pytest.mark.parametrize("beta", [0.05, 0.5, 0.9])
def test_schott_harmonics_sum_to_lienard_and_integrate_from_the_pattern(beta):
    rho = 1.0
    w0 = beta * C / rho
    PL = ch.lienard_power(Q, np.array([beta * C, 0, 0]), np.array([0, beta * C * w0, 0]))
    Ps = [ch.harmonic_power(Q, beta, rho, m) for m in range(1, 400)]
    assert sum(Ps) / PL - 1 == pytest.approx(0, abs=1e-9 if beta < 0.9 else 1e-6)
    for m in (1, 2, 5):
        Pi = 2 * math.pi * integrate.quad(lambda th: ch.harmonic_angular_power(Q, beta, rho, m, th) * math.sin(th), 0,
                                          math.pi, limit=400, epsabs=0, epsrel=1e-12)[0]
        assert Pi / Ps[m - 1] - 1 == pytest.approx(0, abs=1e-9)
    if beta == 0.05:  # non-relativistic: the first harmonic is Larmor's dipole radiation
        assert Ps[0] / ch.larmor_power(Q, np.array([0, beta * C * w0, 0])) == pytest.approx(1, abs=5e-3)


def test_harmonics_against_the_fourier_transform_of_the_computed_field():
    """Independent route: the Liénard–Wiechert field of the circular orbit at a far point, Fourier-analysed over one
    period of observer time, gives the power per solid angle of each harmonic (Schott's eq. 128)."""
    beta, rho = 0.5, 1.0
    w0 = beta * C / rho
    wl = ch.circular(rho, w0)
    r, N = 1e6, 256
    T0 = 2 * math.pi / w0
    t = r / C + np.arange(N) * T0 / N
    for th in (0.3, 1.2):
        x = np.array([r * math.sin(th), 0, r * math.cos(th)])
        E, _ = ch.fields(ch.Charge(Q, wl), x[None, :], t)
        c = np.fft.fft(E, axis=0) / N
        for m in (1, 2, 3):
            Pm = r * r * 2 * np.sum(np.abs(c[m]) ** 2) / (ch.MU0 * C)
            assert Pm / ch.harmonic_angular_power(Q, beta, rho, m, th) - 1 == pytest.approx(0, abs=1e-5)


def test_synchrotron_spectrum_is_the_large_gamma_limit_of_schotts_harmonics():
    """Review B8 C12: the relation named in ABOUT's conflicts. The harmonic power P_m / omega0 (Schott, exact at any
    beta) at omega = m omega0 tends to the F-function spectrum as 1/gamma^2: measured +4.0e-3 (gamma = 10) and +1.0e-3
    (gamma = 20) at omega = omega_c, a factor 4.0 per doubling at omega / omega_c = 0.3, 1 and 3."""
    rho = 1.0
    dev = {}
    for gam in (10.0, 20.0):
        beta = math.sqrt(1 - 1 / gam ** 2)
        w0 = beta * C / rho
        wc = ch.critical_frequency(gam, rho)
        for y in (0.3, 1.0, 3.0):
            m = round(y * wc / w0)
            dev[gam, y] = ch.harmonic_power(Q, beta, rho, m) / w0 / ch.synchrotron_spectrum(Q, gam, rho, m * w0) - 1
    for y in (0.3, 1.0, 3.0):
        assert dev[20.0, y] / dev[10.0, y] == pytest.approx(0.25, rel=0.05)  # O(1/gamma^2)
        assert abs(dev[20.0, y]) < 5e-3
    assert abs(dev[10.0, 3.0]) > 1e-2  # negative control: at gamma = 10 the limit is not yet reached
