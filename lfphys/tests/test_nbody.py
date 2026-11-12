# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Newtonian N bodies (lfphys.core.gravity.nbody, plan P15.1) against closed forms, an independent integrator and
published solutions.

Tolerances. The global error of a run is estimated by a companion run with eta/16 (the time-symmetric Hermite scheme
is fourth order in dt and dt is proportional to sqrt(eta), so the companion is 256 times more accurate): the
difference of the two bounds the error of the looser run, |x - x_true| <= |x - x_c| (1 + 1/255) < 2 |x - x_c| (the
codebase's "x2" rule); the order itself is checked (a scheme of the wrong order would pass the x2 rule). Round-off
terms are written out where they matter (the closed forms' own rounding, the accumulated time, the positions' ulp at
close encounters). Independent routes: Kepler's equation (two bodies), SciPy's DOP853 at 1e-13 (figure eight),
Szebehely & Peters (1967) Table I (the Pythagorean problem's close approaches).

Negative controls: a force law changed by 1e-6 fails the Kepler comparison; symmetric steps without iterated
correctors, and iterated correctors without symmetric steps, each drift in energy where the time-symmetric scheme does
not (review B6-G9); the former symmetrization tolerance 1e-3 drifts past the bound the default keeps (B6-G8); a
non-iterated scheme is not reversible.
"""

import json
import math

import numpy as np
import pytest

from lfphys.core.gravity import nbody as NB

U = 2.0 ** -53


# --- helpers ---------------------------------------------------------------------------------------------------------
def kepler_relative(t, a, e, mu):
    """Relative orbit starting at periapsis on +x at t = 0, moving towards +y: (x (3,), v (3,)) by Kepler's equation
    E - e sin E = n t (Newton to round-off)."""
    n = math.sqrt(mu / a ** 3)
    M = math.remainder(n * t, 2.0 * math.pi)
    E = M + e * math.sin(M) if e < 0.8 else math.copysign(math.pi, M) if M != 0 else 0.0
    for _ in range(60):
        dE = (E - e * math.sin(E) - M) / (1.0 - e * math.cos(E))
        E -= dE
        if abs(dE) < 1e-16:
            break
    b = a * math.sqrt(1.0 - e * e)
    den = 1.0 - e * math.cos(E)
    x = np.array([a * (math.cos(E) - e), b * math.sin(E), 0.0])
    v = np.array([-a * n * math.sin(E) / den, b * n * math.cos(E) / den, 0.0])
    return x, v


def binary(e=0.9, a=1.0, m1=1.0, m2=1e-3, **kw):
    nb = NB.NBody(**kw)
    M = m1 + m2
    x, v = kepler_relative(0.0, a, e, M)
    nb.add(-m2 / M * x, -m2 / M * v, m1, key="star")
    nb.add(m1 / M * x, m1 / M * v, m2, key="planet")
    return nb, 2.0 * math.pi * math.sqrt(a ** 3 / M)


def relative(nb):
    x, v = nb.positions(), nb.velocities()
    return x[1] - x[0], v[1] - v[0]


FIG8_X1 = np.array([0.97000436, -0.24308753, 0.0])  # Chenciner & Montgomery 2000, Fig. 1 (Simo's initial conditions)
FIG8_V = np.array([-0.93240737, -0.86473146, 0.0])
FIG8_T = 6.32591398


def figure_eight(**kw):
    nb = NB.NBody(**kw)
    nb.add(FIG8_X1, -0.5 * FIG8_V, 1.0)
    nb.add(-FIG8_X1, -0.5 * FIG8_V, 1.0)
    nb.add([0.0, 0.0, 0.0], FIG8_V, 1.0)
    return nb


def pythagorean(**kw):
    """Szebehely & Peters 1967, Fig. 1: m1 = 3 at (1, 3), m2 = 4 at (-2, -1), m3 = 5 at (1, -1), at rest, G = 1."""
    nb = NB.NBody(**kw)
    nb.add([1.0, 3.0, 0.0], m=3.0, key=1)
    nb.add([-2.0, -1.0, 0.0], m=4.0, key=2)
    nb.add([1.0, -1.0, 0.0], m=5.0, key=3)
    return nb


# --- the field -------------------------------------------------------------------------------------------------------
def test_jerk_is_the_time_derivative_of_the_acceleration():
    """NM08 Eq. (2) against a central difference of Eq. (1) along x + v s (step h = 1e-4: truncation h^2 |a'''|/6,
    round-off u |a| / h)."""
    rng = np.random.default_rng(3)
    x, v, m = rng.normal(size=(6, 3)), rng.normal(size=(6, 3)), np.array([1.0, 2.0, 0.0, 0.5, 0.0, 3.0])
    a, j = NB.acc_jerk(x, v, m, 1.3)
    h = 1e-4
    ap = NB.acc_jerk(x + h * v, v, m, 1.3, jerk=False)
    am = NB.acc_jerk(x - h * v, v, m, 1.3, jerk=False)
    fd = (ap - am) / (2 * h)
    a3 = (NB.acc_jerk(x + 2 * h * v, v, m, 1.3, jerk=False) - 2 * ap + 2 * am
          - NB.acc_jerk(x - 2 * h * v, v, m, 1.3, jerk=False)) / (2 * h ** 3)
    tol = h * h * np.abs(a3) / 6 * 2 + 4 * U * np.max(np.abs(a)) / h + 64 * U * np.abs(j)
    assert np.all(np.abs(fd - j) <= tol)


def test_tidal_tensor_against_differences_of_the_acceleration():
    """-d^2 Phi/dx dx = d a / d x: central differences of acceleration_at (h = 1e-5 of the distance: truncation
    h^2 |a'''|/6 bounded by the next difference, round-off 2 u |a| / h); symmetric, traceless off the bodies; and
    the potential's gradient is the acceleration."""
    nb = NB.NBody(G=2.0)
    nb.add([0.0, 0.0, 0.0], m=1.0, key="a")
    nb.add([1.5, -0.3, 0.4], m=0.3, key="b")
    nb.add([-2.0, 1.0, 0.0], m=0.0, key="tp")
    pts = np.array([[0.7, 0.9, -0.2], [3.0, 2.0, 1.0], [-1.2, 0.1, 0.5]])
    T = nb.tidal_tensor_at(pts)
    a0 = nb.acceleration_at(pts)
    for p, Tp, ap in zip(pts, T, a0):
        h = 1e-5 * np.linalg.norm(p - nb.positions()[0])
        D = np.empty((3, 3))
        D2 = np.empty((3, 3))
        for k in range(3):
            e = np.zeros(3)
            e[k] = h
            D[:, k] = (nb.acceleration_at([p + e])[0] - nb.acceleration_at([p - e])[0]) / (2 * h)
            D2[:, k] = (nb.acceleration_at([p + 2 * e])[0] - nb.acceleration_at([p - 2 * e])[0]) / (4 * h)
        tol = np.abs(D2 - D) * 4 / 3 + 4 * U * np.linalg.norm(ap) / h + 16 * U * np.abs(Tp)
        assert np.all(np.abs(D - Tp) <= tol + 1e-300)
        assert np.max(np.abs(Tp - Tp.T)) <= 8 * U * np.max(np.abs(Tp))
        assert abs(np.trace(Tp)) <= 16 * U * np.max(np.abs(Tp))
        g = np.array([(nb.potential_at([p + e]) - nb.potential_at([p - e]))[0] / (2 * h) for e in np.eye(3) * h])
        assert np.all(np.abs(-g - ap) <= np.abs(D) @ np.full(3, h) + 4 * U * abs(nb.potential_at([p])[0]) / h)
    # excluding a body removes exactly its field
    only_b = nb.acceleration_at(pts, exclude=["a"])
    d = nb.positions()[1] - pts
    ref = 2.0 * 0.3 * d / np.linalg.norm(d, axis=1)[:, None] ** 3
    assert np.max(np.abs(only_b - ref)) <= 8 * U * np.max(np.abs(ref))


# --- two bodies: Kepler ----------------------------------------------------------------------------------------------
def test_kepler_closed_form_helper_is_exact():
    """The reference itself: energy and angular momentum of kepler_relative to round-off along 3 orbits."""
    a, e, mu = 1.0, 0.9, 1.001
    for t in np.linspace(0, 3 * 2 * math.pi, 37):
        x, v = kepler_relative(t, a, e, mu)
        assert abs(0.5 * v @ v - mu / np.linalg.norm(x) + mu / (2 * a)) <= 64 * U * mu / (a * (1 - e))
        assert abs(np.cross(x, v)[2] - math.sqrt(mu * a * (1 - e * e))) <= 64 * U * math.sqrt(mu * a)


@pytest.mark.parametrize("integrator", ["hermite", "yoshida4"])
def test_kepler_eccentric_orbit_after_many_orbits(integrator):
    """e = 0.9 (periapsis 0.1 a; yoshida4: 0.5), 20 orbits, against Kepler's equation; error bound: the x2 rule with a companion 256
    times more accurate (eta/16, or dt/4 for yoshida4), plus the closed form's rounding 16 u (|x| + t |v|) and the
    accumulated time's rounding N u t |v|. The observed order (error ratio between the run and the companion) is 4
    within half an order (ratio in [4^3.5, 4^4.5]); measured: see the assertion message."""
    if integrator == "hermite":
        e, kw, kw_c = 0.9, dict(eta=0.02), dict(eta=0.02 / 16)
    else:  # the fixed step is for quiet systems: e = 0.5
        e, kw, kw_c = 0.5, dict(integrator="yoshida4", dt=2 * math.pi / 400), dict(integrator="yoshida4",
                                                                                     dt=2 * math.pi / 1600)
    nb, P = binary(e=e, **kw)
    nc, _ = binary(e=e, **kw_c)
    M = 1.001
    for t in (0.37 * P, 10.0 * P, 19.5 * P, 20.0 * P + 0.01):
        nb.advance(t)
        nc.advance(t)
        x, v = relative(nb)
        xc, _ = relative(nc)
        xk, vk = kepler_relative(t, 1.0, e, M)
        err_est = np.linalg.norm(x - xc)
        steps = nb.diagnostics()["steps"]
        rnd = 16 * U * (np.linalg.norm(xk) + t * np.linalg.norm(vk)) + steps * U * t * np.linalg.norm(vk)
        err = np.linalg.norm(x - xk)
        assert err <= 2 * err_est + rnd, (t, err, err_est)
        if t > 5 * P:
            err_c = np.linalg.norm(xc - xk)
            ratio = err / max(err_c, 1e-300)
            assert 4 ** 3.5 <= ratio <= 4 ** 4.5, (t, err, err_c, ratio)


def test_kepler_negative_control_wrong_force_law():
    """G changed by 1e-6 (an inconsistent force) is caught: the error no longer shrinks with eta."""
    nb, P = binary(eta=0.005, G=1.0 + 1e-6)
    nc, _ = binary(eta=0.005 / 16, G=1.0 + 1e-6)
    t = 10.0 * P
    nb.advance(t)
    nc.advance(t)
    x, _ = relative(nb)
    xc, _ = relative(nc)
    xk, _ = kepler_relative(t, 1.0, 0.9, 1.001)
    assert np.linalg.norm(x - xk) > 2 * np.linalg.norm(x - xc)


def test_periodic_energy_without_secular_drift_and_its_two_negative_controls():
    """The time-symmetric Hermite scheme (symmetric steps, P(EC)^3): the energy error at apoapsis stays at its level
    from the first orbits (no secular growth): |dE(100 P)| <= 2 max |dE(k P)| over the first 10 orbits (KYM98, HMM95).
    Both ingredients are needed (KYM98: "the time-symmetry of the scheme achieved by the iteration of EC steps", with
    "time-symmetric time-steps"; review B6-G9), so two negative controls, each past that bound: symmetric steps
    without iteration (n_iter = 1: PEC; review measured x18.7 in 100 orbits) and iteration without symmetric steps
    (max_passes = 1: the extrapolated step, P(EC)^3; x8.2). max_passes = 1 honours n_iter (before the review it
    silently ran one corrector): P(EC)^3 and PEC differ."""
    def run(**kw):
        nb, P = binary(eta=0.02, **kw)
        E0 = nb.energy()
        early, late = [], None
        for k in (1, 3, 10):
            nb.advance((k + 0.5) * P)
            early.append(abs(nb.energy() - E0))
        nb.advance(100.5 * P)
        late = abs(nb.energy() - E0)
        return max(early), late
    early, late = run()
    assert late <= 2 * early, (early, late)
    for kw in (dict(n_iter=1), dict(max_passes=1)):
        early_n, late_n = run(**kw)
        assert late_n > 2 * early_n, (kw, early_n, late_n)
    a, P = binary(eta=0.02, n_iter=3, max_passes=1)
    b, _ = binary(eta=0.02, n_iter=1, max_passes=1)
    a.advance(5 * P)
    b.advance(5 * P)
    assert not np.array_equal(a.positions(), b.positions())
    assert a.diagnostics()["force_evals"] > 2 * b.diagnostics()["force_evals"]


def test_secular_drift_is_set_by_the_symmetrization_tolerance():
    """Review B6-G8: the step is symmetric only to dt_rtol, which leaves a residual secular energy drift. e = 0.999,
    eta = 0.02 (the HMM95 / KYM98 regime): with the default (1e-4) the drift fitted between orbits 10 and 60, carried
    over 1000 orbits, stays below half the energy error's own level at apoapsis (measured: 7e-8 per orbit against the
    level 4.5e-4, so ~0.16 of it). Negative control: the former default 1e-3 drifts ~30 times faster (2e-6 per orbit)
    and breaks the same bound."""
    def slope(**kw):
        nb, P = binary(e=0.999, eta=0.02, **kw)
        E0 = nb.energy()
        nb.advance(10.5 * P)
        d10 = (nb.energy() - E0) / abs(E0)
        nb.advance(60.5 * P)
        d60 = (nb.energy() - E0) / abs(E0)
        return (d60 - d10) / 50.0, abs(d10)
    s, level = slope()
    assert abs(s) * 1000 <= 0.5 * level, (s, level)
    s_old, level_old = slope(dt_rtol=1e-3)
    assert abs(s_old) * 1000 > 0.5 * level_old, (s_old, level_old)


def test_halving_eta_quarters_the_error():
    """Review B6-G10 (the playground's companion runs with eta/2): Aarseth's step is proportional to sqrt(eta) and the
    scheme is fourth order, so eta/2 shortens the step by sqrt(2) and divides the error by 4 (not 16): the ratio of
    the errors against Kepler's equation (e = 0.5, 10 orbits) lies within half an order of 4 ([4^0.75, 4^1.25], the
    window of the order test above; measured 4.05-4.11), and so excludes 16."""
    for eta in (0.02, 0.005):
        errs = []
        for k in (1, 2):
            nb, P = binary(e=0.5, eta=eta / k)
            t = 10.0 * P
            nb.advance(t)
            x, _ = relative(nb)
            errs.append(np.linalg.norm(x - kepler_relative(t, 1.0, 0.5, 1.001)[0]))
        ratio = errs[0] / errs[1]
        assert 4 ** 0.75 <= ratio <= 4 ** 1.25, (eta, ratio)


def test_symplectic_energy_bounded_over_ten_thousand_orbits():
    """yoshida4, e = 0.3, 24 steps per orbit, 1e4 orbits: the energy error stays within twice the largest error seen
    in the first 10 orbits plus the round-off random walk 4 u |E| sqrt(steps) (a symplectic map conserves a nearby
    Hamiltonian). Negative control: the PEC Hermite scheme with the same fixed step drifts out of that band within
    1e3 orbits."""
    P = 2 * math.pi * math.sqrt(1.0 / 1.001)
    nb, _ = binary(e=0.3, integrator="yoshida4", dt=P / 24)
    E0 = nb.energy()
    first = 0.0
    for k in range(1, 11):
        nb.advance(k * P + 0.3 * P)
        first = max(first, abs(nb.energy() - E0))
    worst = first
    for k in np.linspace(11, 10000, 25):
        nb.advance(k * P + 0.3 * P)
        worst = max(worst, abs(nb.energy() - E0))
    steps = nb.diagnostics()["steps"]
    assert worst <= 2 * first + 4 * U * abs(E0) * math.sqrt(steps), (first, worst)
    # negative control: PEC Hermite, fixed step (dt_max = P/24, eta so large that dt_max always applies)
    nh, _ = binary(e=0.3, n_iter=1, max_passes=1, eta=1e6, dt_max=P / 24)
    E0 = nh.energy()
    first = 0.0
    for k in range(1, 11):
        nh.advance(k * P + 0.3 * P)
        first = max(first, abs(nh.energy() - E0))
    nh.advance(1000.3 * P)
    assert abs(nh.energy() - E0) > 2 * first


# --- three bodies ----------------------------------------------------------------------------------------------------
def _dop853_three_body(state0, T, rtol):
    from scipy.integrate import solve_ivp
    m = np.ones(3)

    def f(t, y):
        x = y[:9].reshape(3, 3)
        return np.concatenate([y[9:], NB.acc_jerk(x, x, m, 1.0, jerk=False).ravel()])
    sol = solve_ivp(f, (0.0, T), state0, method="DOP853", rtol=rtol, atol=rtol * 1e-2)
    return sol.y[:, -1]


def test_figure_eight_returns_after_one_period():
    """Chenciner & Montgomery (2000), Fig. 1 (Simo's initial conditions, 8 decimals; T = 6.32591398): (1) the engine
    against SciPy's DOP853 at 1e-13 (independent route) within the engine's x2 error estimate and the reference's
    (a 1e-11 run); (2) the published orbit closes: |s(T) - s(0)| of the reference is within the effect of rounding
    the published digits, sum_k |(Phi - I)_{:,k}| 5e-9 + |ds/dt| 5e-9 (Phi the monodromy matrix by central
    differences of DOP853 runs, the half-unit 5e-9 of the 8th decimal), and the engine's within that plus its error."""
    nb = figure_eight(eta=1e-3)
    nc = figure_eight(eta=1e-3 / 16)
    s0 = np.concatenate([nb.positions().ravel(), nb.velocities().ravel()])
    assert np.max(np.abs(nb.momentum())) == 0.0 and np.max(np.abs(nb.angular_momentum())) == 0.0
    nb.advance(FIG8_T)
    nc.advance(FIG8_T)
    s1 = np.concatenate([nb.positions().ravel(), nb.velocities().ravel()])
    sc = np.concatenate([nc.positions().ravel(), nc.velocities().ravel()])
    ref = _dop853_three_body(s0, FIG8_T, 1e-13)
    ref_l = _dop853_three_body(s0, FIG8_T, 1e-11)
    e_eng = 2 * np.abs(s1 - sc)
    e_ref = 2 * np.abs(ref - ref_l)
    assert np.all(np.abs(s1 - ref) <= e_eng + e_ref + 64 * U), np.max(np.abs(s1 - ref))
    # closing of the published orbit
    h = 1e-6
    Phi = np.empty((18, 18))
    for k in range(18):
        d = np.zeros(18)
        d[k] = h
        Phi[:, k] = (_dop853_three_body(s0 + d, FIG8_T, 1e-12) - _dop853_three_body(s0 - d, FIG8_T, 1e-12)) / (2 * h)
    sdot = np.concatenate([s0[9:], NB.acc_jerk(s0[:9].reshape(3, 3), s0[:9].reshape(3, 3), np.ones(3), 1.0,
                                               jerk=False).ravel()])
    bound = np.abs(Phi - np.eye(18)) @ np.full(18, 5e-9) + np.abs(sdot) * 5e-9
    gap = np.abs(ref - s0)
    assert np.all(gap <= bound + e_ref), (gap.max(), bound.max())
    assert np.all(np.abs(s1 - s0) <= bound + e_ref + e_eng + 64 * U)
    assert gap.max() > 1e-9  # the published digits are not exact: the closing gap is seen (measured 1.8e-7)


def _record_steps(nb, t_end):
    recs = []
    while nb.t < t_end:
        nb.step(1)
        recs.append((nb.t, nb.positions(), nb.velocities()))
    return recs


def _minima(recs, i, j):
    """Local minima of |x_j - x_i| over the steps: (t, r, r''): t by linear interpolation of g = d.w = 0 between the
    bracketing steps, r'' = (dg/dt) / r there (dg/dt = |w|^2 + d.a_rel = r r'' at a minimum)."""
    out = []
    g_prev = None
    for k, (t, x, v) in enumerate(recs):
        d, w = x[j] - x[i], v[j] - v[i]
        g = float(d @ w)
        if g_prev is not None and g_prev < 0.0 <= g:
            t0 = recs[k - 1][0]
            tm = t0 + (t - t0) * (-g_prev) / (g - g_prev)
            r = min(np.linalg.norm(recs[k - 1][1][j] - recs[k - 1][1][i]), np.linalg.norm(d))
            out.append((tm, r, (g - g_prev) / (t - t0) / r))
        g_prev = g
    return out


# Szebehely & Peters (1967), Table I (read on the rendered page 881): time, approximate distance, pair (masses)
SP_TABLE = [(1.879, 1e-2, (4, 5)), (3.026, 0.6, (3, 5)), (3.801, 6e-2, (4, 5)), (6.898, 0.1, (3, 5)),
            (8.760, 8e-3, (4, 5)), (9.962, 0.5, (3, 5)), (11.611, 0.2, (4, 5)), (14.618, 0.2, (3, 5)),
            (15.830, 4e-4, (4, 5)), (17.001, 0.3, (3, 5)), (19.807, 0.2, (4, 5)), (21.791, 0.4, (3, 5)),
            (22.966, 2e-2, (4, 5)), (24.537, 0.1, (3, 5)), (27.780, 5e-2, (4, 5)), (28.679, 0.5, (3, 5)),
            (29.802, 3e-3, (4, 5))]


def _t10_reference():
    """Time of the closest m2-m3 approach near t = 15.83 by SciPy's DOP853 at rtol 1e-13 (independent route)."""
    from scipy.integrate import solve_ivp
    m = np.array([3.0, 4.0, 5.0])

    def f(t, y):
        x = y[:9].reshape(3, 3)
        return np.concatenate([y[9:], NB.acc_jerk(x, x, m, 1.0, jerk=False).ravel()])

    def ev(t, y):
        return float((y[6:9] - y[3:6]) @ (y[15:18] - y[12:15]))
    ev.direction = 1
    y0 = np.zeros(18)
    y0[:9] = [1, 3, 0, -2, -1, 0, 1, -1, 0]
    sol = solve_ivp(f, (0, 15.84), y0, method="DOP853", rtol=1e-13, atol=1e-16, events=[ev])
    return [t for t in sol.t_events[0] if 15.82 < t < 15.84][0]


def test_pythagorean_close_approaches_against_szebehely_peters():
    """Burrau's problem to t = 30 against Szebehely & Peters (1967) Table I: every listed close approach is found
    (same pair, one local minimum within 0.05 of the listed time) and none of these pairs comes closer than 0.1
    elsewhere; the distance agrees with the table's one significant digit (within a factor 1.5); the time: a sharp
    minimum rounds to the table's three decimals; a flat one fixes its time only through the distance, so S&P's time
    must lie where our distance is within 1e-3 (relative) of its minimum, r_min + r'' (t_SP - t)^2 / 2 (measured:
    sharp ones all round correctly; flat ones (r ~ 0.2 - 0.6, r'' ~ 30) differ by up to 1.8e-3 in time and 7.3e-4 in
    distance). The closest approach t10: the run against DOP853 at 1e-13 within the x2 rule (companion eta/4); the
    printed 15.8299236 differs from it by 3.3e-6 (the 1967 integration's own error: [measured] 15.82992027).
    Energy and angular momentum: |dE| <= 2 |E - E_c| + B, B = sum over steps and pairs of G m_i m_j u (|x_i| +
    |x_j|) / r_ij^2 (the rounding of the stored positions, relative u|x|/r of each separation - the floor that
    dominates at the 4e-4 approach and does not shrink with eta); L_z (zero) likewise with the round-off of the
    sums."""
    nb = pythagorean(eta=1e-3)
    nc = pythagorean(eta=1e-3 / 4)
    E0 = nb.energy()
    recs = _record_steps(nb, 30.0)
    recc = _record_steps(nc, 30.0)
    m = {1: 3.0, 2: 4.0, 3: 5.0}
    rows = {(4, 5): (1, 2), (3, 5): (0, 2)}
    found = {p: _minima(recs, *rows[p]) for p in rows}
    found_c = {p: _minima(recc, *rows[p]) for p in rows}
    for t_sp, r_sp, pair in SP_TABLE:
        cand = [(t, r, rpp, tc) for (t, r, rpp), (tc, _, _) in zip(found[pair], found_c[pair])
                if abs(t - t_sp) < 0.05]
        assert len(cand) == 1, (t_sp, pair, found[pair])
        t, r, rpp, tc = cand[0]
        assert abs(math.log(r / r_sp)) <= math.log(1.5), (t_sp, r, r_sp)
        sharp = round(t, 3) == t_sp
        flat = 0.5 * rpp * (t_sp - t) ** 2 <= 1e-3 * r
        assert sharp or flat, (t_sp, t, r, rpp)
        if t_sp == 15.830:
            t_ref = _t10_reference()
            assert abs(t - t_ref) <= 2 * abs(t - tc) + 64 * U * t, (t, tc, t_ref)
            assert 3.0e-6 < abs(t_ref - 15.8299236) < 3.6e-6, t_ref
    for pair, lst in found.items():
        for t, r, _ in lst:
            if r < 0.1:
                assert any(abs(t - ts) < 0.05 for ts, _, p in SP_TABLE if p == pair), (pair, t, r)
    B = 0.0
    for _, x, _ in recs:
        for i in range(3):
            for j in range(i + 1, 3):
                r = np.linalg.norm(x[j] - x[i])
                B += m[i + 1] * m[j + 1] * U * (np.linalg.norm(x[i]) + np.linalg.norm(x[j])) / r ** 2
    nb_E, nc_E = nb.energy(), nc.energy()
    assert abs(nb_E - E0) <= 2 * abs(nb_E - nc_E) + B, (nb_E - E0, nc_E - E0, B)
    Lz, Lzc = nb.angular_momentum()[2], nc.angular_momentum()[2]
    BL = 64 * U * len(recs) * sum(m[k + 1] * np.linalg.norm(recs[-1][1][k]) * np.linalg.norm(recs[-1][2][k])
                                  for k in range(3))
    assert abs(Lz) <= 2 * abs(Lz - Lzc) + BL, (Lz, Lzc, BL)


def _outcome(nb):
    x, v, m = nb.positions(), nb.velocities(), nb.masses()
    best = None
    for i, j, k in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
        mu = m[i] * m[j] / (m[i] + m[j])
        d, w = x[j] - x[i], v[j] - v[i]
        Eb = 0.5 * mu * (w @ w) - m[i] * m[j] / np.linalg.norm(d)
        if Eb < 0 and (best is None or Eb < best[2]):
            M = m[i] + m[j]
            xc, vc = (m[i] * x[i] + m[j] * x[j]) / M, (m[i] * v[i] + m[j] * v[j]) / M
            mu3 = M * m[k] / (M + m[k])
            D, W = x[k] - xc, v[k] - vc
            Eo = 0.5 * mu3 * (W @ W) - M * m[k] / np.linalg.norm(D)
            best = ((nb.keys[i], nb.keys[j]), nb.keys[k], Eb, Eo, float(D @ W))
    return best


def test_pythagorean_outcome_binary_and_escape():
    """Szebehely & Peters (1967): "two of the three participating bodies form a permanent binary while the third body
    is rejected to infinity"; "Figure 7 shows the final formation of a binary by m2 and m3"; "The binary and the body
    with mass m1 depart with hyperbolic velocities". At t = 80: bodies 2 and 3 bound, body 1 unbound from their centre
    of mass (E_outer > 0) and receding. Not a converged trajectory: after the 4e-4 approach (t = 15.83) the runs
    agree only to the round-off floor ~1e-7 (it does not shrink with eta), and chaos amplifies it ~1e6 by t = 60, so
    the escape time and the binary's period (0.72 .. 1.36 over eta = 1e-3 .. 2.5e-5, S&P: "approximately 0.9")
    vary; the outcome class was the same in all six runs with eta <= 1e-3 (eta = 5e-3 gives a wrong pair: a
    reminder that a coarse run is not the solution). Energy within the floor bound of the test above."""
    nb = pythagorean(eta=5e-4)
    E0 = nb.energy()
    nb.advance(80.0)
    pair, third, Eb, Eo, recede = _outcome(nb)
    assert set(pair) == {2, 3} and third == 1
    assert Eo > 0.0 and recede > 0.0
    assert abs(nb.energy() - E0) <= 1e-6 * abs(E0)


# --- conservation and symmetry ---------------------------------------------------------------------------------------
def _cluster(n=6, seed=7, **kw):
    rng = np.random.default_rng(seed)
    nb = NB.NBody(**kw)
    for k in range(n):
        nb.add(rng.normal(size=3), 0.3 * rng.normal(size=3), m=float(rng.uniform(0.5, 2.0)))
    nb.add(rng.normal(size=3), 0.3 * rng.normal(size=3), m=0.0, key="tp")
    return nb


@pytest.mark.parametrize("integrator", ["hermite", "yoshida4"])
def test_momentum_and_angular_momentum(integrator):
    """Linear momentum to round-off for both schemes (sum_i m_i a_i = 0 and sum m_i j_i = 0 pair by pair); angular
    momentum to round-off for yoshida4 (drifts and central kicks conserve it) and only to truncation for the Hermite
    corrector (checked: it shrinks with eta, while the momentum error does not). Round-off bound per step:
    sum_i m_i u (8 |v_i| + 16 dt sum_j G m_j / r_ij^2) for P, and the same with |x_i| |v_i| and |x_i| sum_j ...
    for L."""
    kw = dict(integrator=integrator, collisions="pass")
    if integrator == "yoshida4":
        kw["dt"] = 1e-3
    nb = _cluster(**kw)
    P0, L0 = nb.momentum(), nb.angular_momentum()
    BP = BL = 0.0
    m = nb.masses()
    for _ in range(300):
        x, v = nb.positions(), nb.velocities()
        nb.step(1)
        dt = nb.diagnostics()["last_dt"]
        d = x[None, :, :] - x[:, None, :]
        r2 = np.einsum("ijk,ijk->ij", d, d) + np.eye(len(m))
        s = np.sum(np.where(np.eye(len(m)) > 0, 0.0, m[None, :] / r2), axis=1)
        BP += float(np.sum(m * U * (8 * np.linalg.norm(v, axis=1) + 16 * dt * s)))
        BL += float(np.sum(m * U * np.linalg.norm(x, axis=1) * (8 * np.linalg.norm(v, axis=1) + 16 * dt * s)))
    assert np.max(np.abs(nb.momentum() - P0)) <= BP
    dL = np.max(np.abs(nb.angular_momentum() - L0))
    if integrator == "yoshida4":
        assert dL <= BL
    else:
        assert dL > BL  # truncation, not round-off
        n2 = _cluster(integrator="hermite", collisions="pass", eta=0.02 / 16)
        n2.advance(nb.t)
        assert np.max(np.abs(n2.angular_momentum() - L0)) < dL / 16


def test_time_reversibility():
    """Forward n steps, v -> -v, n steps, v -> -v returns to the start: the converged time-symmetric Hermite scheme
    (n_iter = 10, dt_rtol 1e-13) and yoshida4 to round-off growth (bound: steps x 64 u x |state| x 10 of
    amplification over one orbit, measured below 1e-12); the PEC scheme (one corrector, unsymmetrized step) only to
    its truncation error (negative control)."""
    def roundtrip(nb, n):
        s0 = np.concatenate([nb.positions().ravel(), nb.velocities().ravel()])
        nb.step(n)
        nb.reverse()
        nb.step(n)
        nb.reverse()
        return np.max(np.abs(np.concatenate([nb.positions().ravel(), nb.velocities().ravel()]) - s0))
    bound = 200 * 64 * U * 10 * 10.0
    nb, _ = binary(e=0.5, n_iter=10, dt_rtol=1e-13, max_passes=40)
    assert roundtrip(nb, 200) <= bound
    ny, P = binary(e=0.5, integrator="yoshida4", dt=2 * math.pi / 200)
    assert roundtrip(ny, 200) <= bound
    npec, _ = binary(e=0.5, n_iter=1, max_passes=1)
    assert roundtrip(npec, 200) > 1e3 * bound


# --- edits, events, state ---------------------------------------------------------------------------------------------
def test_add_remove_and_set_keep_the_others():
    """An edit at time t leaves every other body exactly (bit for bit) as shown at t; keys are stable."""
    nb = _cluster(collisions="pass")
    nb.advance(0.37)
    keys = nb.keys
    x0, v0 = nb.positions(), nb.velocities()
    k = nb.add([5.0, 5.0, 5.0], [0.0, 0.1, 0.0], m=0.2)
    assert nb.keys == keys + [k] and nb.t == 0.37
    assert np.array_equal(nb.positions()[:-1], x0) and np.array_equal(nb.velocities()[:-1], v0)
    nb.advance(0.5)
    x1, v1 = nb.positions(), nb.velocities()
    nb.remove(k)
    assert nb.keys == keys
    assert np.array_equal(nb.positions(), x1[:-1]) and np.array_equal(nb.velocities(), v1[:-1])
    nb.set("tp", v=[0.0, 0.0, 1.0])
    nb.set(0, m=3.0)
    assert np.array_equal(nb.positions(), x1[:-1])
    assert np.array_equal(np.delete(nb.velocities(), keys.index("tp"), 0), np.delete(v1[:-1], keys.index("tp"), 0))
    assert nb.body(0)["m"] == 3.0
    with pytest.raises(KeyError):
        nb.add([0, 0, 0], key=0)
    with pytest.raises(ValueError):
        nb.advance(0.1)


def test_a_refused_edit_leaves_everything_as_it_was():
    """Review B6-G2: a body added exactly on a massive body (or moved onto one) is refused with ValueError (the
    playground's refusal) and the object is left bit for bit as it was: its plain-data state equals an untouched twin's,
    and both continue identically. A test particle may share a point with another test particle (no force between
    them). set_many is all or nothing."""
    a, b = _cluster(collisions="pass"), _cluster(collisions="pass")
    a.advance(0.37)
    b.advance(0.37)
    k0, k1 = a.keys[0], a.keys[1]
    on0 = a.body(k0)["x"]
    with pytest.raises(ValueError, match="same point"):
        a.add(on0, m=0.5, key="new")
    with pytest.raises(ValueError, match="same point"):
        a.add(on0, m=0.0, key="tp-on-mass")
    with pytest.raises(ValueError, match="same point"):
        a.set(k1, x=on0)
    with pytest.raises(ValueError, match="same point"):
        a.set_many({k1: {"v": [0.0, 0.0, 0.1]}, "tp": {"x": on0}})
    with pytest.raises(KeyError):
        a.set_many({k1: {"v": [0.0, 0.0, 0.1]}, "missing": {"v": [0.0, 0.0, 0.0]}})
    assert json.dumps(a.state_dict()) == json.dumps(b.state_dict())
    a.advance(1.0)
    b.advance(1.0)
    assert np.array_equal(a.positions(), b.positions()) and np.array_equal(a.velocities(), b.velocities())
    tp = a.body("tp")
    a.add(tp["x"], tp["v"], m=0.0, key="tp2")  # allowed: test particles exert nothing
    assert a.has("tp2")


def test_set_many_equals_the_same_changes_one_by_one():
    """set_many (one sync, one force evaluation) gives the state that the same set calls one after another give, and
    the same future, bit for bit."""
    a, b = _cluster(collisions="pass"), _cluster(collisions="pass")
    a.advance(0.2)
    b.advance(0.2)
    k0, k1 = a.keys[0], a.keys[1]
    a.set_many({k0: {"v": [0.01, 0.0, 0.0]}, k1: {"v": [0.0, -0.02, 0.0], "m": 0.7}})
    b.set(k0, v=[0.01, 0.0, 0.0])
    b.set(k1, v=[0.0, -0.02, 0.0], m=0.7)
    a.advance(0.9)
    b.advance(0.9)
    assert np.array_equal(a.positions(), b.positions()) and np.array_equal(a.velocities(), b.velocities())


def test_a_compact_body_keeps_its_radius_rule_and_absorbs_what_it_meets():
    """Review B6-G5: a body with radius_per_mass k (a black hole's capture radius 2Gm/c^2) has R = k m after a merger
    (the equal-density rule gave the hole a swallowed star's radius) and after a change of its mass; a merger with it
    keeps its key even when the other body is heavier; of two compact bodies the heavier key is kept. Mass and
    momentum are kept as in any merger; the rule survives a state_dict round trip."""
    k = 1e-3
    nb = NB.NBody()
    nb.add([0.0, 0.0, 0.0], m=10.0, radius_per_mass=k, key="hole")
    nb.add([0.3, 0.0, 0.0], [0.0, 0.0, 0.0], m=1.0, radius=0.1, key="star")
    assert nb.body("hole")["radius"] == 10.0 * k
    ev = nb.advance(1.0)
    assert [e["kind"] for e in ev] == ["merge"] and ev[0]["key"] == "hole" and nb.keys == ["hole"]
    assert nb.body("hole")["radius"] == 11.0 * k and nb.body("hole")["m"] == 11.0
    # a light hole meets a heavier star: the hole absorbs it
    n2 = NB.NBody()
    n2.add([0.0, 0.0, 0.0], [0.0, 0.0, 0.0], m=0.5, radius_per_mass=k, key="hole")
    n2.add([0.0, 0.05, 0.0], [0.0, 0.0, 0.0], m=2.0, radius=0.1, key="star")
    P0 = n2.momentum()
    e2 = n2.advance(0.0)
    assert e2[0]["key"] == "hole" and n2.keys == ["hole"] and n2.body("hole")["radius"] == 2.5 * k
    assert np.all(n2.momentum() == P0)
    # two compact bodies: the heavier key, R = k (m1 + m2)
    n3 = NB.NBody()
    n3.add([0.0, 0.0, 0.0], m=1.0, radius_per_mass=k, key="a")
    n3.add([0.0, 0.0015, 0.0], m=3.0, radius_per_mass=k, key="b")
    e3 = n3.advance(0.0)
    assert e3[0]["key"] == "b" and n3.body("b")["radius"] == 4.0 * k
    # the rule follows the mass; a radius cannot be forced on a compact body; the rule is in the state
    n3.set("b", m=5.0)
    assert n3.body("b")["radius"] == 5.0 * k
    with pytest.raises(ValueError):
        n3.set("b", radius=1.0)
    with pytest.raises(ValueError):
        n3.add([1.0, 0.0, 0.0], m=1.0, radius=0.2, radius_per_mass=k)
    n4 = NB.NBody.from_state_dict(json.loads(json.dumps(n3.state_dict())))
    assert n4.body("b")["radius_per_mass"] == k
    # control: without the rule the merged radius is the equal-density one
    n5 = NB.NBody()
    n5.add([0.0, 0.0, 0.0], m=10.0, radius=10.0 * k, key="hole")
    n5.add([0.3, 0.0, 0.0], m=1.0, radius=0.1, key="star")
    e5 = n5.advance(1.0)
    assert e5[0]["radius"] == pytest.approx(((10 * k) ** 3 + 0.1 ** 3) ** (1 / 3), rel=4 * U)


def test_the_passport_names_the_fuller_forms():
    """Review B6-G14: the module is in the core as the most complete form of N-body gravity the engine has
    (LAYERS.md §1); its two-body and test-body cases name the engine's fuller forms."""
    c = " ".join(NB.ABOUT["conflicts"])
    assert NB.ABOUT["layer"] == "core" and "pn_binary" in c and "kerr_newman" in c


def test_test_particle_feels_and_exerts_nothing():
    """A massless body does not change the others' motion (yoshida4: the same fixed steps with or without it, the
    massive bodies agree to round-off of the differently shaped sums, 64 u |x|), a star alone with test particles
    stays exactly at rest, and a test particle on a Kepler orbit about it follows Kepler's equation (the x2 rule)."""
    a = _cluster(integrator="yoshida4", dt=1e-3, collisions="pass")
    b = NB.NBody(integrator="yoshida4", dt=1e-3, collisions="pass")
    for k in a.keys:
        if k != "tp":
            st = a.body(k)
            b.add(st["x"], st["v"], st["m"], key=k)
    a.advance(0.8)
    b.advance(0.8)
    keep = [i for i, k in enumerate(a.keys) if k != "tp"]
    assert np.max(np.abs(a.positions()[keep] - b.positions())) <= 64 * U * np.max(np.abs(b.positions()))

    def star(eta):
        nb = NB.NBody(eta=eta)
        nb.add([0.0, 0.0, 0.0], m=1.0, key="star")
        x, v = kepler_relative(0.0, 1.0, 0.6, 1.0)
        nb.add(x, v, m=0.0, key="tp")
        return nb
    s, sc = star(0.02), star(0.02 / 16)
    s.advance(7.3)
    sc.advance(7.3)
    assert np.all(s.positions()[0] == 0.0) and np.all(s.velocities()[0] == 0.0)
    xk, vk = kepler_relative(7.3, 1.0, 0.6, 1.0)
    err = np.linalg.norm(s.positions()[1] - xk)
    assert err <= 2 * np.linalg.norm(s.positions()[1] - sc.positions()[1]) + 16 * U * 7.3 * np.linalg.norm(vk) * 10


def test_merger_conserves_mass_and_momentum_and_finds_the_contact():
    """Two bodies falling from rest at D = 2 with R_1 + R_2 = 0.3 merge at the radial Kepler time
    t(r) = sqrt(D^3 / (2 G M)) [sqrt(x (1 - x)) + arccos(sqrt(x))], x = r/D, within the x2 error estimate; mass exact,
    momentum to its roundings (bodies placed in contact: the rule alone; in flight: plus the steps' round-off), the
    merged radius (R1^3 + R2^3)^(1/3), the heavier body's key kept, the reported energy change equal to E_after -
    E_before; a test particle hitting a body is absorbed (mass and momentum of the body unchanged)."""
    def run(eta):
        nb = NB.NBody(eta=eta)
        nb.add([-0.8, 0.0, 0.0], [0.0, 0.01, 0.0], m=1.5, radius=0.2, key="A")
        nb.add([1.2, 0.0, 0.0], [0.0, -0.015, 0.0], m=1.0, radius=0.1, key="B")
        return nb
    # the rule itself: bodies placed in contact merge at once (no integration in between)
    n0 = NB.NBody()
    n0.add([0.0, 0.1, 0.0], [0.3, -0.2, 0.1], m=1.5, radius=0.2, key="A")
    n0.add([0.25, 0.0, 0.0], [-0.7, 0.4, 0.0], m=1.0, radius=0.1, key="B")
    n0.add([5.0, 0.0, 0.0], m=0.5, key="C")
    P0, M0, E0 = n0.momentum(), n0.total_mass(), n0.energy()
    ev0 = n0.advance(0.0)
    assert len(ev0) == 1 and ev0[0]["t"] == 0.0 and ev0[0]["key"] == "A" and n0.keys == ["A", "C"]
    assert n0.total_mass() == M0
    pa, pb = 1.5 * np.array([0.3, -0.2, 0.1]), 1.0 * np.array([-0.7, 0.4, 0.0])
    assert np.all(np.abs(n0.momentum() - P0) <= 4 * U * (np.abs(pa) + np.abs(pb)))
    assert ev0[0]["radius"] == pytest.approx((0.2 ** 3 + 0.1 ** 3) ** (1 / 3), rel=4 * U)
    assert abs(n0.energy() - (E0 + ev0[0]["delta_energy"])) <= 64 * U * (abs(E0) + abs(ev0[0]["delta_energy"]))
    # in flight: the contact found by the integration
    nb, nc = run(0.01), run(0.01 / 16)
    P0, M0 = nb.momentum(), nb.total_mass()
    E0 = nb.energy()
    ev = nb.advance(5.0)
    evc = nc.advance(5.0)
    assert len(ev) == 1 and ev[0]["kind"] == "merge" and ev[0]["key"] == "A" and sorted(ev[0]["keys"]) == ["A", "B"]
    assert nb.keys == ["A"] and nb.total_mass() == M0
    vmax = max(np.linalg.norm(np.array(ev[0]["v"])), 1.0)
    assert np.all(np.abs(nb.momentum() - P0) <= 64 * U * nb.diagnostics()["steps"] * 2.5 * vmax * 10)
    # contact time: the relative motion is nearly radial (small transverse velocities): compare a purely radial
    # pair with the closed form
    def radial(eta):
        n = NB.NBody(eta=eta)
        n.add([-0.8, 0.0, 0.0], m=1.5, radius=0.2, key="A")
        n.add([1.2, 0.0, 0.0], m=1.0, radius=0.1, key="B")
        return n.advance(5.0)[0]["t"]
    D, M, r = 2.0, 2.5, 0.3
    x = r / D
    t_ref = math.sqrt(D ** 3 / (2 * M)) * (math.sqrt(x * (1 - x)) + math.acos(math.sqrt(x)))
    t1, t2 = radial(0.01), radial(0.01 / 16)
    assert abs(t1 - t_ref) <= 2 * abs(t1 - t2) + 64 * U * t_ref
    assert abs(ev[0]["t"] - evc[0]["t"]) < 1e-6
    # energy bookkeeping: E_after = E_before + delta_energy (the merger is at the step's state: E0 drifts only by
    # the integration error, x2 rule)
    assert abs(nb.energy() - (E0 + ev[0]["delta_energy"])) <= 2 * abs((nb.energy() - ev[0]["delta_energy"])
                                                                       - (nc.energy() - evc[0]["delta_energy"])) + 1e-12
    # a test particle is absorbed
    n2 = NB.NBody()
    n2.add([0.0, 0.0, 0.0], m=1.0, radius=0.5, key="star")
    n2.add([3.0, 0.0, 0.0], [-1.0, 0.0, 0.0], m=0.0, key="tp")
    e2 = n2.advance(10.0)
    assert e2[0]["key"] == "star" and n2.keys == ["star"] and n2.total_mass() == 1.0
    assert np.all(n2.momentum() == 0.0)


def test_pass_policy_reports_each_contact_once():
    """Point masses with radii pass through; one 'contact' event per entry, at the entry time from the continuous
    output (the separation there equals R1 + R2 to round-off); advancing in many small slices gives the same events
    as one call."""
    def make():
        nb = NB.NBody(collisions="pass")
        nb.add([0.0, 0.0, 0.0], m=1.0, radius=0.1, key="s")
        nb.add([2.0, 0.05, 0.0], [-0.3, 0.0, 0.0], m=0.0, radius=0.05, key="p")
        return nb
    a = make()
    ev_a = a.advance(30.0)
    b = make()
    ev_b = []
    for t in np.linspace(0.0, 30.0, 301)[1:]:
        ev_b += b.advance(t)
    # a bound orbit (E < 0, periapsis ~1e-4): one entry per periapsis passage, period 7.24
    assert [e["kind"] for e in ev_a] == ["contact"] * 4
    assert [e["t"] for e in ev_a] == [e["t"] for e in ev_b]
    for e in ev_a:
        x = np.array(e["x"])
        assert abs(np.linalg.norm(x[1] - x[0]) - 0.15) <= 64 * U * 2.0
    assert b.keys == ["s", "p"]


def test_output_does_not_depend_on_how_time_is_sliced():
    """The integrator's step sequence does not depend on the requested times: one call or 1000 calls give the same
    state bit for bit."""
    a = pythagorean(eta=0.01)
    b = pythagorean(eta=0.01)
    a.advance(5.0)
    for t in np.linspace(0, 5.0, 1001)[1:]:
        b.advance(t)
    assert np.array_equal(a.positions(), b.positions()) and np.array_equal(a.velocities(), b.velocities())


@pytest.mark.parametrize("integrator", ["hermite", "yoshida4"])
def test_state_dict_restores_bit_identically(integrator):
    """Save at an output time inside a step (through JSON), restore, continue: bit-identical to continuing without
    the save; a companion (eta/16) starts from the same shown state."""
    kw = dict(integrator=integrator, collisions="merge")
    if integrator == "yoshida4":
        kw["dt"] = 2e-3
    a = _cluster(**kw)
    a.set(0, radius=0.05)
    a.advance(0.4321)
    d = json.loads(json.dumps(a.state_dict()))
    b = NB.NBody.from_state_dict(d)
    assert np.array_equal(a.positions(), b.positions())
    ea, eb = a.advance(1.7), b.advance(1.7)
    assert ea == eb
    assert np.array_equal(a.positions(), b.positions()) and np.array_equal(a.velocities(), b.velocities())
    da, db = a.diagnostics(), b.diagnostics()
    for k in ("energy", "momentum", "angular_momentum", "com_x", "com_v", "steps", "merges", "last_dt", "t"):
        assert da[k] == db[k], k  # (force_evals differs: the restored object recomputes the pending step)
    if integrator == "hermite":
        c = a.clone(eta=a.eta / 16)
        assert np.array_equal(c.positions(), a.positions()) and c.eta == a.eta / 16


def test_free_motion_and_diagnostics():
    """No massive body: exact straight lines; diagnostics carry the running checks."""
    nb = NB.NBody()
    nb.add([0.0, 0.0, 0.0], [1.0, 2.0, 0.5], m=0.0)
    nb.add([1.0, 0.0, 0.0], [0.0, 0.0, -1.0], m=0.0)
    nb.advance(2.5)
    assert np.array_equal(nb.positions(), np.array([[2.5, 5.0, 1.25], [1.0, 0.0, -2.5]]))
    nb2, P = binary()
    nb2.advance(0.3 * P)
    d = nb2.diagnostics()
    for k in ("energy", "momentum", "angular_momentum", "com_x", "com_v", "steps", "force_evals", "last_dt",
              "local_error_v", "local_error_x", "last_residual_x"):
        assert k in d
    assert d["local_error_v"] > 0 and d["steps"] > 3


# --- drawing samples and the live collision law (reviews UX-ui U2, U12) ------------------------------------------------
def _kepler_pair():
    nb = NB.NBody(1.0, eta=0.02)
    nb.add([0.0, 0.0, 0.0], [0.0, 0.0, 0.0], 1.0, key="a")
    e = 0.6  # an eccentric orbit: the turn rate changes 16-fold between peri- and apoapsis
    nb.add([1.0 - e, 0.0, 0.0], [0.0, math.sqrt((1 + e) / (1 - e)), 0.0], 1e-9, key="b")
    return nb


def test_samples_are_the_continuous_output_and_do_not_depend_on_slicing():
    """``advance(t, samples=Samples())``: the points are the integrator's continuous output (exactly the positions the
    world shows at their times), within the stated turn of each body's direction of motion of each other, and the same
    whether the caller advances in 4 or in 200 calls (the grid belongs to the step); the motion with samples is bit for
    bit the motion without. Negative control: one point per call at 4 calls turns by far more."""
    a, b, c = _kepler_pair(), _kepler_pair(), _kepler_pair()
    sa, sb = NB.Samples(turn=math.radians(10)), NB.Samples(turn=math.radians(10))
    for k in range(1, 5):
        a.advance(k * 1.5, samples=sa)
    for k in range(1, 201):
        b.advance(k * 0.03, samples=sb)
    c.advance(6.0)
    assert a.state_dict() == c.state_dict()  # the samples do not perturb the motion
    ta, tb = [p[0] for p in sa.points], [p[0] for p in sb.points]
    assert ta == tb and all(np.array_equal(p[2], q[2]) for p, q in zip(sa.points, sb.points))
    V = np.array([p[3][1] for p in sa.points])
    ang = np.degrees(np.arctan2(np.linalg.norm(np.cross(V[:-1], V[1:]), axis=1), np.einsum("ij,ij->i", V[:-1], V[1:])))
    assert ang.max() <= 10.0 + 1e-9 and len(ang) > 3 * 360 / 10 / 2
    # each point is what the world shows at its time
    d = _kepler_pair()
    for p in sa.points[:: max(1, len(sa.points) // 15)]:
        d.advance(p[0])
        assert np.array_equal(d.positions(), p[2]) or np.max(np.abs(d.positions() - p[2])) <= 64 * U
    e = _kepler_pair()
    pts = []
    for k in range(1, 5):
        e.advance(k * 1.5)
        pts.append(e.velocities()[1])
    W = np.array(pts)
    assert np.max(np.degrees(np.arctan2(np.linalg.norm(np.cross(W[:-1], W[1:]), axis=1),
                                        np.einsum("ij,ij->i", W[:-1], W[1:])))) > 60.0


def test_a_merger_appears_in_the_samples_with_its_restart():
    """Two bodies falling together merge: the samples hold the touching state at the contact time and then the merged
    body at the same time, marked as restarted (its state jumps there)."""
    nb = NB.NBody(1.0, collisions="merge")
    nb.add([-1.0, 0.0, 0.0], [0.0, 0.1, 0.0], 1.0, 0.1, key="a")
    nb.add([1.0, 0.0, 0.0], [0.0, -0.1, 0.0], 1.0, 0.1, key="b")
    s = NB.Samples()
    ev = nb.advance(5.0, samples=s)
    m = [e for e in ev if e["kind"] == "merge"][0]
    i = next(j for j, p in enumerate(s.points) if p[4])
    assert s.points[i][0] == pytest.approx(m["t"], abs=1e-12) and s.points[i][4] == {m["key"]}
    assert s.points[i - 1][0] == pytest.approx(m["t"], abs=1e-12) and len(s.points[i - 1][1]) == 2
    assert np.linalg.norm(np.diff(s.points[i - 1][2], axis=0)) == pytest.approx(0.2, rel=1e-9)
    assert s.points[i][1] == (m["key"],)


def test_the_collision_law_changes_at_the_current_moment():
    """``set_collisions``: two bodies overlapping on a circle (pass) stay two; switched to merge they merge at that
    moment (mass and momentum kept); the motion before the switch is not rewritten (the state at the switch is what was
    shown)."""
    def pair():
        nb = NB.NBody(1.0, collisions="pass")
        nb.add([-0.05, 0.0, 0.0], [0.0, -math.sqrt(2.0 / 0.1) / 2, 0.0], 1.0, 0.2, key="a")
        nb.add([0.05, 0.0, 0.0], [0.0, math.sqrt(2.0 / 0.1) / 2, 0.0], 1.0, 0.2, key="b")
        return nb
    nb = pair()
    nb.advance(0.3)
    assert nb.n == 2
    shown = nb.positions().copy()
    p0 = nb.momentum().copy()
    nb.set_collisions("merge")
    ev = nb.advance(0.3000001)
    assert nb.n == 1 and [e["kind"] for e in ev] == ["merge"] and ev[0]["t"] == pytest.approx(0.3, abs=1e-12)
    assert np.allclose(np.mean(shown, axis=0), nb.positions()[0], atol=1e-12)  # merged at the shown positions' centre
    assert np.allclose(nb.momentum(), p0, atol=1e-14) and nb.masses()[0] == 2.0
    nb2 = pair()
    nb2.advance(0.3)
    nb2.set_collisions("pass")  # no change: nothing happens
    nb2.advance(0.6)
    assert nb2.n == 2
    with pytest.raises(ValueError):
        nb2.set_collisions("bounce")
