# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P1 (B8): the Yee grid itself — its dispersion relation, the 1-D "magic time step", the stability limit, the
exactly conserved discrete energy, and the eigenfrequencies of PEC (and PEC/PMC) cavities.

* Dispersion (Schneider, Understanding the FDTD Method, §7.4, eq. 7.34 in 1-D; "a similar dispersion relation holds
  in two and three dimensions", the same plane-wave substitution per axis):
  sin^2(omega dt/2)/(c dt)^2 = sum_u sin^2(k_u dx/2)/dx^2. A standing mode with wavevector k on a periodic grid
  oscillates at every node exactly at the grid's omega(k), so x_{n+1} + x_{n-1} = 2 cos(omega dt) x_n and the measured
  omega must equal the closed form to round-off at every angle and resolution; the continuum omega = c|k| is the
  negative control (it differs by the dispersion error, here 1e-4 to 1e-2).
* Magic time step (Schneider §7.4: "since there is no dispersion error with this Courant number, the corresponding
  time step is known as the magic time-step"): in 1-D with c dt = dx a pulse moves exactly one cell per step.
* Energy: in a closed lossless PEC box W = (1/2) sum eps |E^n|^2 + (1/2) sum mu H^{n-1/2} . H^{n+1/2} is conserved to
  round-off (the update is symplectic: the E-update uses the adjoint of the H-update's curl).
* Cavities: a PEC box a x b x d has modes k = (m pi/a, n pi/b, p pi/d); on the grid their frequencies are the grid's
  omega(k) exactly (the discrete sines satisfy the wall conditions), and tend to c|k| at second order.
"""

import math

import numpy as np
import pytest

from lfphys.core.em import fdtd as F


def _omega_from_series(x, dt):
    """omega of a pure sinusoid sampled at dt, from x_{n+1} + x_{n-1} = 2 cos(omega dt) x_n (least squares)."""
    x = np.asarray(x, float)
    c = np.sum(x[1:-1] * (x[2:] + x[:-2])) / (2.0 * np.sum(x[1:-1] ** 2))
    return math.acos(c) / dt


def _pencil(x, dt, L=None, rel=1e-10):
    """Frequencies (cycles per time unit) of a sum of undamped sinusoids by the matrix pencil method."""
    x = np.asarray(x, float)
    N = len(x)
    L = L or N // 3
    Y = np.lib.stride_tricks.sliding_window_view(x, L + 1)
    _, s, Vh = np.linalg.svd(Y, full_matrices=False)
    M = int(np.sum(s > rel * s[0]))
    V = Vh[:M].conj().T
    z = np.linalg.eigvals(np.linalg.pinv(V[:-1]) @ V[1:])
    return np.sort(np.abs(np.angle(z))) / (2 * math.pi * dt)


@pytest.mark.parametrize("N", [32, 64])
def test_dispersion_relation_at_every_angle_2d(N):
    """Measured omega of standing modes (m, n) on an N x N periodic grid against the grid's closed form."""
    rows = []
    for m, n in ((3, 0), (3, 1), (2, 2), (1, 3), (0, 4), (4, 3)):
        w = F.FDTD((1.0, 1.0), 1.0 / N, pol="tm", boundary="periodic", courant=0.6)
        k = 2 * math.pi * np.array([m, n], float)
        w.set_field("ez", lambda x, y: np.cos(k[0] * x + k[1] * y))
        pid = w.add_probe((0.3 + 0.5 / N, 0.2), ["ez"])
        pid2 = w.add_probe((0.71, 0.53), ["ez"])
        w.advance(400)
        for p in (pid, pid2):
            om = _omega_from_series(w.probe(p)["ez"], w.dt)
            om_yee = F.yee_frequency(k, w.dx, w.dt)
            om_c = np.linalg.norm(k)
            rows.append((m, n, om, om_yee, om_c))
            assert abs(om - om_yee) < 1e-10 * om_yee, (m, n, om, om_yee)
            # the negative control: the continuum relation is far outside this tolerance
            assert abs(om - om_c) > 1e-5 * om_c
    # the Yee grid is slowest along the axes and fastest along the diagonal (at equal |k|)
    kk = 2 * math.pi * 4.0
    om_axis = F.yee_frequency(np.array([kk, 0.0]), 1.0 / N, 0.6 / N)
    om_diag = F.yee_frequency(np.array([kk, kk]) / math.sqrt(2), 1.0 / N, 0.6 / N)
    assert om_diag > om_axis


def test_dispersion_relation_3d_and_phase_velocity_order():
    """3-D modes; and the phase velocity error falls as (k dx)^2 (second order): halving dx divides it by ~4."""
    errs = []
    for N in (16, 32):
        w = F.FDTD((1.0, 1.0, 1.0), 1.0 / N, boundary="periodic", courant=0.5)
        k = 2 * math.pi * np.array([2.0, 1.0, 0.0])
        w.set_field("ez", lambda x, y, z: np.cos(k[0] * x + k[1] * y) + 0 * z)  # div E = 0: E_z independent of z
        pid = w.add_probe((0.31, 0.47, 0.5), ["ez"])
        w.advance(300)
        om = _omega_from_series(w.probe(pid)["ez"], w.dt)
        assert abs(om - F.yee_frequency(k, w.dx, w.dt)) < 1e-10 * om
        errs.append(1 - om / np.linalg.norm(k))
    assert 3.6 < errs[0] / errs[1] < 4.4, errs


def test_magic_time_step_is_exact_in_1d():
    """1-D (a 2-D grid one cell wide, periodic): with c dt = dx a pulse moves exactly one cell per step."""
    N = 200
    dx = 1.0 / N
    g = lambda x: np.exp(-((x - 0.3) / 0.02) ** 2) + 0.5 * np.exp(-((x - 0.5) / 0.005) ** 2)  # noqa: E731
    out = {}
    for S in (1.0, 0.5):
        w = F.FDTD((1.0, dx), dx, pol="tm", boundary="periodic", courant=S)
        assert w.courant_limit == pytest.approx(1.0)
        w.set_field("ez", lambda x, y: g(x) + 0 * y)
        # H_y at t = -dt/2 of the right-moving wave E_z = g(x - t): H_y = -g(x + dt/2 - ... ) at x_{i+1/2}
        w.set_field("hy", lambda x, y: -g(x + 0.5 * w.dt) + 0 * y)
        n = 120 if S == 1.0 else 240
        w.advance(n)
        x = w.coords("ez")[0]
        exact = g(np.mod(x - n * w.dt, 1.0))
        out[S] = np.max(np.abs(w.field("ez")[:, 0] - exact))
    assert out[1.0] < 1e-13, out
    assert out[0.5] > 1e-3, out  # the negative control: below the magic step the pulse disperses


def test_courant_limit_is_enforced(ru):
    with pytest.raises(F.Unstable, match="the scheme is unstable in the medium background") as e:
        F.FDTD((1.0, 1.0), 0.05, courant=0.72)
    assert "схема неустойчива в среде фон (вакуум)" in ru(e.value.args[0])
    F.FDTD((1.0, 1.0), 0.05, courant=0.707)
    with pytest.raises(F.Unstable):
        F.FDTD((1.0, 1.0, 1.0), 0.05, courant=0.58)
    w = F.FDTD((1.0, 1.0), 0.05, courant=0.5)
    # a Lorentz pole beyond omega0 dt = 2 makes the explicit pole update unstable: refused, the world unchanged
    f_bad = 2.2 / (2 * math.pi * w.dt)
    with pytest.raises(F.Unstable):
        w.add_body(F.Cylinder((0.5, 0.5), 0.2), F.Medium(poles=[F.Lorentz(1.0, f_bad, 0.0)]))
    assert w.bodies() == []
    # a dielectric with eps < 1 (faster than c) is refused at S beyond 1/sqrt(2 eps)... and accepted below
    with pytest.raises(F.Unstable):
        F.FDTD((1.0, 1.0), 0.05, courant=0.6).add_body(F.Cylinder((0.5, 0.5), 0.2), F.Medium(eps=0.5))
    F.FDTD((1.0, 1.0), 0.05, courant=0.45).add_body(F.Cylinder((0.5, 0.5), 0.2), F.Medium(eps=0.5))


@pytest.mark.parametrize("dim", [2, 3])
def test_discrete_energy_is_conserved_in_a_closed_box(dim):
    rng = np.random.default_rng(1)
    if dim == 2:
        w = F.FDTD((1.0, 0.8), 0.04, pol="both", boundary="pec")
        w.add_body(F.Cylinder((0.5, 0.4), 0.2), F.Medium(eps=4.0))
        w.add_body(F.Box((0.1, 0.1), (0.3, 0.3)), F.Medium(eps=2.0, mu=1.5))
        steps = 3000
    else:
        w = F.FDTD((0.6, 0.5, 0.4), 0.04, boundary="pec")
        w.add_body(F.Sphere((0.3, 0.25, 0.2), 0.12), F.Medium(eps=3.0))
        w.add_body(F.Box((0.05, 0.05, 0.05), (0.2, 0.2, 0.15)), F.Medium(mu=2.0))
        steps = 1500
    for c in w.comps:
        w.set_field(c, rng.standard_normal(w.shape[:dim]))
    e0 = w.energy()
    naive = []
    tot = []
    for _ in range(10):
        w.advance(steps // 10)
        e = w.energy()
        tot.append(e["total"])
        naive.append(e["electric"] + e["magnetic_half_step"])
    rel = np.max(np.abs(np.array(tot) - e0["total"])) / e0["total"]
    assert rel < 1e-12, rel
    # the negative control: the energy with H at a single time level is not conserved
    assert np.max(np.abs(np.array(naive) - (e0["electric"] + e0["magnetic_half_step"]))) / e0["total"] > 1e-3


def test_pec_cavity_eigenfrequencies_3d():
    """A PEC box 1.0 x 0.6875 x 0.4375 (16 x 11 x 7 cells): the lowest modes from a probe's record by the matrix
    pencil, against the grid's exact frequencies (1e-8) and the continuum (second order, checked at two cells)."""
    errs = {}
    for N in (16, 32):
        dx = 1.0 / N
        a, b, d = 1.0, 11 * 0.0625, 7 * 0.0625
        w = F.FDTD((a, b, d), dx, boundary="pec", courant=0.5)
        prof = F.ModulatedGaussian(1.2, fwidth=0.35)
        for comp, amp in (("ex", 1.0), ("ey", 0.7), ("ez", 0.4)):
            w.add_source(F.CurrentSource(comp, prof, position=(0.23, 0.31, 0.17), amplitude=amp))
        pid = w.add_probe((0.61, 0.27, 0.29), ["ex", "ey", "ez"])
        n_end = int(math.ceil(prof.end() / w.dt)) + 2
        w.advance(n_end + 2400)
        p = w.probe(pid)
        sig = p["ex"][n_end:] + 0.8 * p["ey"][n_end:] + 0.6 * p["ez"][n_end:]
        f_est = _pencil(sig[::2], 2 * w.dt, L=500)
        modes = []
        for m in range(4):
            for n in range(4):
                for q in range(4):
                    if (m > 0) + (n > 0) + (q > 0) < 2:
                        continue  # a TE/TM mode of a box needs two non-zero indices
                    k = np.array([m * math.pi / a, n * math.pi / b, q * math.pi / d])
                    f_yee = F.yee_frequency(k, dx, w.dt) / (2 * math.pi)
                    f_c = np.linalg.norm(k) / (2 * math.pi)
                    if f_c < 1.5:
                        modes.append((f_c, f_yee, (m, n, q)))
        modes.sort()
        e = []
        for f_c, f_yee, mnq in modes[:4]:
            got = f_est[np.argmin(np.abs(f_est - f_yee))]
            assert abs(got - f_yee) < 1e-8 * f_yee, (N, mnq, got, f_yee)
            e.append(f_c - got)
        errs[N] = np.array(e)
    ratio = errs[16] / errs[32]
    assert np.all((ratio > 3.5) & (ratio < 4.5)), ratio


def test_pec_pmc_waveguide_modes_2d():
    """TM in a 2-D box with PEC on x and PEC (bottom) / PMC (top) on y: E_z = sin(kx x) sin(ky y) with
    ky = (p + 1/2) pi / Ly, Ly the distance between the walls (the PMC wall lies half a cell inside the grid, so Ly is
    an odd multiple of dx/2: 0.625 = 12.5 cells is realised exactly)."""
    dx = 1.0 / 20
    w = F.FDTD((1.0, 0.625), dx, pol="tm", boundary={"x": "pec", "y": ("pec", "pmc")}, courant=0.6)
    Ly = w.interior[1]
    assert Ly == pytest.approx((w.shape[1] - 0.5) * dx) and Ly == pytest.approx(0.625, abs=1e-12)
    assert w.checks()["geometry"]["ok"]
    w.add_source(F.CurrentSource("ez", F.ModulatedGaussian(1.4, fwidth=0.4), position=(0.37, 0.23)))
    pid = w.add_probe((0.71, 0.41), ["ez"])
    n0 = 400
    w.advance(n0 + 3000)
    f_est = _pencil(w.probe(pid)["ez"][n0:][::2], 2 * w.dt, L=600)
    for m, p in ((1, 0), (1, 1), (2, 0), (2, 1)):
        k = np.array([m * math.pi / 1.0, (p + 0.5) * math.pi / Ly])
        f_yee = F.yee_frequency(k, dx, w.dt) / (2 * math.pi)
        got = f_est[np.argmin(np.abs(f_est - f_yee))]
        assert abs(got - f_yee) < 1e-8 * f_yee, (m, p, got, f_yee)
    # the negative control: the PEC/PEC modes (ky = p pi / Ly) are absent
    k = np.array([math.pi, math.pi / Ly])
    f_wrong = F.yee_frequency(k, dx, w.dt) / (2 * math.pi)
    assert np.min(np.abs(f_est - f_wrong)) > 1e-3


# --- regressions of review B8-fdtd -----------------------------------------------------------------------------------
@pytest.mark.parametrize("lo,hi,want", [("pec", "pec", 0.6), ("pmc", "pmc", 0.6), ("pml", "pec", 0.6),
                                        ("pml", "pml", 0.6), ("pml", "pmc", 0.6), ("pmc", "pml", 0.6),
                                        ("pec", "pmc", 0.625), ("pmc", "pec", 0.625)])
def test_axis_lengths_with_pec_and_pmc_walls(lo, hi, want):
    """F9: a PEC wall lies on an E plane (integer index; the far one at index n through the wrap), a PMC wall on an H
    plane (half-integer), so between them the length is an odd number of half cells: 0.6 with dx = 0.05 (12 cells) is
    not realisable and 0.625 (the nearest, a tie broken upwards) is realised and reported in ``checks()`` and
    ``describe()``. Next to a PML side the interior's edge is free and the length is exact (it was 0.625 for
    (pml, pmc) before the review, unreported)."""
    w = F.FDTD((1.0, 0.6), 0.05, pol="tm", boundary={"x": "pec", "y": (lo, hi)}, pml=4)
    assert w.interior[1] == pytest.approx(want, abs=1e-12)
    pos = {"pec": (0.0, w.shape[1]), "pmc": (0.5, w.shape[1] - 0.5)}  # wall index positions (lo side, hi side)
    if lo != "pml":
        assert w.coord(pos[lo][0], 1) == pytest.approx(0.0, abs=1e-12)  # the lower wall is the interior's edge
    if hi != "pml":
        assert w.coord(pos[hi][1], 1) == pytest.approx(want, abs=1e-12)  # the upper wall is at the realised length
    if lo == "pml":
        assert w.coord(w.npml[1][0], 1) <= 1e-12  # the layer ends at or before the interior's edge
    if hi == "pml":
        assert w.coord(w.shape[1] - w.npml[1][1], 1) >= want - 1e-12
    g = w.checks()["geometry"]
    assert g["ok"] == (want == 0.6) and w.describe()["size_requested"][1] == 0.6
    if want != 0.6:
        assert "PEC" in str(g["note"])
        exact = F.FDTD((1.0, 0.625), 0.05, pol="tm", boundary={"x": "pec", "y": (lo, hi)})
        assert exact.interior[1] == pytest.approx(0.625, abs=1e-12) and exact.checks()["geometry"]["ok"]


def test_saved_world_keeps_the_requested_length():
    """F9: a world restored from its state reports the same requested and realised lengths."""
    w = F.FDTD((1.0, 0.6), 0.05, pol="tm", boundary={"x": "pec", "y": ("pec", "pmc")})
    r = F.FDTD.from_state_dict(w.state_dict())
    assert r.checks()["geometry"] == w.checks()["geometry"] and list(r.shape) == list(w.shape)


def test_hard_sources_are_exact_at_the_magic_time_step():
    """F2: in 1-D at c dt = dx a hard source of f(t) radiates exactly f(t - |x - x0|/c). Hard E_z (TM) and its dual,
    hard H_z (TE, imposed after the H update at t_{n+1/2}): both within the profile's own jump at its cut-off
    (exp(-18) = 1.5e-8). Before the review the hard H was imposed after the E update and the run diverged (3.8e36)."""
    dx = 0.02
    for pol in ("tm", "te"):
        w = F.FDTD((6.0, dx), dx, pol=pol, boundary={"x": "pml", "y": "periodic"}, courant=1.0, pml=20)
        prof = F.GaussianPulse(0.2, t0=1.2)
        comp = "ez" if pol == "tm" else "hz"
        x0 = 2.0 if pol == "tm" else 2.0 + dx / 2
        y0 = 0.0 if pol == "tm" else dx / 2
        w.add_source(F.CurrentSource(comp, prof, position=(x0, y0), hard=True))
        pid = w.add_probe((x0 + 1.0, y0), [comp])
        w.advance(int(4.0 / w.dt))
        p = w.probe(pid)
        t = p["t"] - (0.5 * w.dt if comp[0] == "h" else 0.0)  # H is recorded half a step earlier
        err = np.max(np.abs(p[comp] - prof(t - 1.0)))
        assert err < 1e-7, (pol, err)


def test_hard_h_is_the_dual_of_hard_e_2d():
    """F2, 2-D at S = 0.5: a hard H_z (TE) and a hard E_z (TM) of the same profile solve dual problems on grids shifted
    by half a cell and half a step, so H_z(TE) at t_{n+1/2} equals E_z(TM) at t_{n+1} of the profile delayed by dt/2;
    measured max difference 3.2e-5 of the peak, which is the absorbing layers' echo (they sit at the same absolute
    positions on both grids, so their reflections, ~1e-5 here, are not dual). Before the review the two differed by
    86 % of the peak."""
    dx = 0.05
    out = {}
    for pol in ("tm", "te"):
        w = F.FDTD((4.0, 4.0), dx, pol=pol, pml=12, courant=0.5)
        comp = "ez" if pol == "tm" else "hz"
        o = 0.0 if pol == "tm" else dx / 2
        prof = F.GaussianPulse(0.15, t0=0.9 + (0.5 * w.dt if pol == "tm" else 0.0))
        w.add_source(F.CurrentSource(comp, prof, position=(2.0 + o, 2.0 + o), hard=True))
        pid = w.add_probe((2.8 + o, 2.0 + o), [comp])
        w.advance(240)
        out[pol] = w.probe(pid)[comp]
    peak = np.abs(out["tm"]).max()
    diff = np.max(np.abs(out["te"] - out["tm"])) / peak
    assert peak > 0.1 and diff < 1e-4, diff


def test_mixed_nodes_are_checked_for_stability(ru):
    """F11: E nodes of medium A (eps 0.25, mu 4) next to H nodes of medium B (eps 4, mu 0.25): each medium alone has
    n = 1, but the mixed nodes carry a wave at speed 4 (1-D limit S = 0.25). Before the review the world was accepted
    at S = 0.5 and its fields were NaN after 500 steps; now refused by the node maps' bound, and accepted at S = 0.24,
    where it stays bounded."""
    dx, L = 0.05, 1.0
    fine = 400
    xs = (np.arange(fine) + 0.5) / fine * L
    arr = (np.abs(xs / dx - np.round(xs / dx)) < 0.25)[:, None] * np.ones((1, 1), bool)  # covers the Ez nodes only

    def world(S):
        w = F.FDTD((L, dx), dx, pol="tm", boundary="periodic", courant=S)
        w.add_body(F.Box((-1.0, -1.0), (2.0, 1.0)), F.Medium(eps=4.0, mu=0.25, label="B"))
        w.add_body(F.Mask(array=arr, lo=(0.0, -1.0), hi=(L, 1.0)), F.Medium(eps=0.25, mu=4.0, label="A"))
        return w

    with pytest.raises(F.Unstable, match="at an interface of media") as e:
        world(0.5)
    assert "на стыке сред" in ru(e.value.args[0])
    w = world(0.24)
    assert np.unique(w._mats["ez"][0]).tolist() == [0.25] and np.unique(w._mats["hy"][0]).tolist() == [0.25]
    rng = np.random.default_rng(0)
    w.set_field("ez", rng.standard_normal(w.shape[:2]))
    e0 = w.energy()["total"]
    w.advance(4000)
    assert abs(w.energy()["total"] / e0 - 1) < 1e-10
    # a single medium with eps < 1 keeps its own limit (the node bound equals it): accepted just below, refused above
    F.FDTD((1.0, 1.0), 0.05, courant=0.45).add_body(F.Cylinder((0.5, 0.5), 0.2), F.Medium(eps=0.5))
    with pytest.raises(F.Unstable):
        F.FDTD((1.0, 1.0), 0.05, courant=0.55).add_body(F.Cylinder((0.5, 0.5), 0.2), F.Medium(eps=0.5))


def test_published_pole_conditions_are_sufficient_for_the_engine():
    """F13: Bidégaray-Fesquet (SIAM J. Numer. Anal. 46, 2551 (2008), arXiv:math/0506289) proves for the Lorentz-Young
    scheme — the engine's Lorentz/Drude update — stability under q <= 2 (2-D: c_inf dt <= dx / 2) and
    omega_0 dt <= 2 / sqrt(2 eps_s/eps_inf - 1) (Table 7, §5), and for the Debye-Joseph et al. scheme — the engine's
    trapezoid — under the vacuum condition (Table 1). Every sampled medium satisfying them is accepted by the engine's
    amplification radius (which also admits more: q <= 2 is sufficient, not necessary); a Lorentz pole beyond the
    omega condition at S = 0.5 is refused, and the refusal names the published conditions."""
    rng = np.random.default_rng(5)
    w = F.FDTD((1.0, 1.0), 0.05, courant=0.5)
    lams = np.linspace(0.0, w.lam_max, 257)
    for _ in range(60):
        eps_inf = rng.uniform(1.0, 4.0)
        de = rng.uniform(0.1, 8.0)
        es = (eps_inf + de) / eps_inf
        w0dt = rng.uniform(0.01, 1.0) * 2.0 / math.sqrt(2 * es - 1)
        S = min(rng.uniform(0.05, 1.0) * 0.5 * math.sqrt(eps_inf), 0.7)  # c_inf dt / dx <= 1/2, S below vacuum's
        ww = F.FDTD((1.0, 1.0), 0.05, courant=S)
        lor = F.Lorentz(de, w0dt / ww.dt / (2 * math.pi), rng.uniform(0.0, 0.5))
        m = F.Medium(eps=eps_inf, poles=[lor])
        assert F.amplification_radius(m, ww.dt, np.linspace(0, ww.lam_max, 257)) <= 1 + 1e-6, (eps_inf, de, w0dt, S)
        deb = F.Medium(eps=eps_inf, poles=[F.Debye(de, rng.uniform(0.2, 5.0) * ww.dt)])
        Sd = rng.uniform(0.05, 1.0) * math.sqrt(eps_inf) / math.sqrt(2)
        wd = F.FDTD((1.0, 1.0), 0.05, courant=min(Sd, 0.7071))
        assert F.amplification_radius(deb, wd.dt, np.linspace(0, wd.lam_max, 257)) <= 1 + 1e-6
    bad = F.Medium(eps=1.0, poles=[F.Lorentz(5.0, 1.2 / w.dt / (2 * math.pi), 0.0)])  # w0 dt = 1.2 > 2/sqrt(11) = 0.6
    assert F.amplification_radius(bad, w.dt, lams) > 1 + 1e-6
    with pytest.raises(F.Unstable, match="Bidégaray-Fesquet"):
        w.add_body(F.Cylinder((0.5, 0.5), 0.2), bad)


def test_field_energy_is_not_conserved_with_a_lossless_pole():
    """F15: ``energy()`` leaves out the polarization's energy, so with a lossless Lorentz body in a closed PEC box the
    field energy exchanges with it (measured 0.17 ... 1.00 of its start), while without the pole it is conserved."""
    vals = {}
    for poles in ([], [F.Lorentz(1.0, 1.0, 0.0)]):
        w = F.FDTD((1.0, 1.0), 0.04, pol="tm", boundary="pec")
        w.set_field("ez", lambda x, y: np.sin(np.pi * x) * np.sin(2 * np.pi * y))
        w.add_body(F.Box((0.3, 0.3), (0.7, 0.7)), F.Medium(eps=2.0, poles=poles), averaging="staircase")
        e = [w.energy()["total"]]
        for _ in range(10):
            w.advance(200)
            e.append(w.energy()["total"])
        vals[len(poles)] = np.array(e) / e[0]
    assert np.max(np.abs(vals[0] - 1)) < 1e-12
    assert np.min(vals[1]) < 0.5


def test_fields_are_checked_at_the_end_of_every_advance(ru):
    """F20: health was checked only at multiples of 256 steps, so short calls could return NaN fields silently."""
    w = F.FDTD((1.0, 1.0), 0.05)
    w.set_field("ez", np.inf)
    with np.errstate(invalid="ignore", over="ignore"), pytest.raises(F.Unstable, match="non-numeric") as e:
        w.advance(10)
    assert "поля стали нечисловыми" in ru(e.value.args[0])
