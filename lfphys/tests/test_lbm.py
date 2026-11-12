# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P8: the 2-D lattice Boltzmann solver (lfphys.core.fluids.lbm) against closed forms (Poiseuille, Couette with
its transient series, Taylor-Green decay, the second moment of a diffusing blob, the steady drag of a periodic array
equal to the body force), its conservation laws (mass, momentum and dye to round-off, booked through open boundaries
and geometry changes), the state round trip and the GPU kernel against the CPU (bit for bit); after review B7: the time
origin, the per-side inlet ramps, the hydrostatic rest state and the imposed-density refusals, the coefficient length's
default, the flow rates after an edit, the acoustic period against the measured ringing, the force record, the
velocity inlet's transverse layer, the surface velocity of a fixed body, and a tight rounding bound with a mutation
test. Lattice-unit runs use dx = dt = 1, rho = 1, so nu is the lattice viscosity. The cylinder and cavity benchmarks
are in test_lbm_benchmarks.py.
"""

import math
import pickle

import numpy as np
import pytest

from lfphys.core import backend
from lfphys.core.fluids import lbm

PER_X = {"left": "periodic", "right": "periodic"}
PER = {s: "periodic" for s in lbm.SIDES}
EPS = float(np.finfo(float).eps)


def roundoff(steps: int) -> float:
    """The bound for a conserved total's relative change from rounding that ``Flow2D.checks`` uses: 2 ulps of the total
    per step, plus 1e-14 for the rounding of the sums over all nodes themselves. Not a proven worst case [error in
    earlier: "the worst-case bound"; review LB1-physics P1]: the per-link records of the booked exchanges grow by the
    gross exchange every step, and as plain running sums their rounding grew like n^2 (a 4 x 16 channel failed after
    9537 steps); they are Kahan-compensated now (``lbm.LINK_ACC``), so the rounding left is the nodes' own (a systematic
    bias of the collision's rounding — the former rest-population formula drifted 0.36 eps per node and step — stays
    below it; ``test_the_running_check_holds_on_long_runs`` measures 2e-3 of it). What it cannot see (review B7 L18): a
    leak below ~2 eps of the total per step — 7.5e-13 per step at one link in the test cavity. Where no accumulator
    carries the quantity (the mass and the dye of a closed domain with fixed walls) ``roundoff_tight`` applies."""
    return 2 * EPS * steps + 1e-14


def roundoff_tight(fl, steps: int, total: float) -> float:
    """The relative bound for the mass or the dye of a closed domain with fixed walls (no accumulator books them):
    each node's update closes its own total (the rest population is set to it), so the only rounding left is that
    closure's, unbiased and independent between nodes and steps — a random walk of N_fluid steps terms of ~eps,
    bounded here at ten times eps sqrt(N_fluid steps) — plus the pairwise sums over the nodes, eps (log2(9 N) + 2)
    times the total. Measured: 0 (periodic Taylor-Green, a closed box with obstacles) and 0.63 eps sqrt(N S) (the lid
    cavity's mass, whose lid links do book it). Review B7 L18; the mutation test below shows what it catches."""
    n = len(fl._fluid_idx)
    return (10 * EPS * math.sqrt(n * steps) + EPS * (math.log2(9 * fl.N) + 2) * abs(total)) / abs(total)


@pytest.fixture(autouse=True)
def _defaults():
    backend.configure(None)
    yield
    backend.configure(None)


def _gpu():
    return backend.devices()["gpu"]["available"]


def lattice(nx, ny, tau, **kw):
    """A flow in lattice units: dx = dt = rho = 1, nu = (tau - 1/2)/3."""
    kw.setdefault("device", "cpu")
    return lbm.Flow2D((float(nx), float(ny)), 1.0, nu=(tau - 0.5) / 3, rho=1.0, dt=1.0, **kw)


# --- Poiseuille --------------------------------------------------------------------------------------------------------
def _poiseuille(ny, tau, g=1e-5, **kw):
    """Steady body-force-driven channel between half-way walls at y = 0 and y = H: returns (u - exact) and exact."""
    nu = (tau - 0.5) / 3
    fl = lattice(2, ny, tau, sides=PER_X, gravity=(g, 0.0), **kw)
    H = float(ny)
    fl.set_flow(velocity=lambda X, Y: (g / (2 * nu) * Y * (H - Y), 0 * X))
    fl.advance(int(36 * H**2 / (nu * math.pi**2)) + 200)  # 36 e-folds of the slowest mode
    exact = g / (2 * nu) * fl.y * (H - fl.y)
    return fl.velocity()[0][0] - exact, exact


@pytest.mark.parametrize("tau", [0.55, 0.8, 1.5, 4.0])
def test_poiseuille_is_exact_with_trt_for_any_viscosity(tau):
    """TRT with Lambda = 3/16 and half-way bounce-back: the parabola to round-off, whatever the viscosity (measured
    1.4e-12 ... 2.3e-12 of the centre velocity)."""
    err, exact = _poiseuille(8, tau)
    assert np.max(np.abs(err)) / exact.max() < 1e-10


@pytest.mark.parametrize("tau", [0.8, 1.5])
def test_poiseuille_with_bgk_depends_on_the_viscosity(tau):
    """Negative control: BGK (Lambda = (tau - 1/2)^2) misplaces the wall unless tau = 1/2 + sqrt(3/16)."""
    err, exact = _poiseuille(8, tau, collision="bgk")
    assert np.max(np.abs(err)) / exact.max() > 5e-3


@pytest.mark.parametrize("collision,magic,tau", [
    ("trt", 1 / 12, 0.7), ("trt", 1 / 12, 2.0), ("trt", 0.25, 0.7), ("trt", 0.25, 2.0), ("trt", 0.5, 0.7),
    ("trt", 0.5, 2.0), ("bgk", None, 0.8), ("bgk", None, 1.0), ("bgk", None, 1.5), ("bgk", None, 0.5 + math.sqrt(3 / 16))])
def test_bounce_back_slip_is_a_function_of_lambda_only(collision, magic, tau):
    """The steady discrete solution is the exact parabola plus a uniform slip (16 Lambda - 3) g / (24 nu) (lattice
    units): zero at the magic Lambda = 3/16, a function of Lambda alone, so for TRT independent of the viscosity, for
    BGK (Lambda = (tau - 1/2)^2) not. Found here numerically, it holds to round-off for
    every case (slip spread across the channel < 1e-10 g/nu); it is the published bounce-back result
    Heff^2 - H^2 = (16/3) Lambda - 1 (Ginzburg, Verhaeghe & d'Humieres, Commun. Comput. Phys. 3, 519 (2008), Table 4,
    p. 539), since a parabola of width Heff in the channel H is shifted by (Heff^2 - H^2) g / (8 nu)."""
    g = 1e-5
    err, _ = _poiseuille(8, tau, g=g, collision=collision, magic=magic if magic else 3 / 16)
    nu = (tau - 0.5) / 3
    lam = magic if collision == "trt" else (tau - 0.5) ** 2
    slip = err * nu / g
    assert np.ptp(slip) < 1e-9
    assert abs(slip.mean() - (16 * lam - 3) / 24) < 1e-9


def test_poiseuille_converges_at_second_order():
    """BGK at tau = 1 (Lambda = 1/4): the relative error falls 4 times per halving of dx (diffusive scaling)."""
    e = []
    for ny in (8, 16, 32):
        err, exact = _poiseuille(ny, 1.0, g=1e-5 * (8 / ny) ** 3, collision="bgk")
        e.append(np.max(np.abs(err)) / exact.max())
    r = [e[0] / e[1], e[1] / e[2]]
    assert all(3.9 < q < 4.1 for q in r), (e, r)


# --- Couette -----------------------------------------------------------------------------------------------------------
def _couette_series(y, t, U, H, nu, terms=400):
    """The impulsively started Couette flow (fluid at rest, the wall at y = H at U from t = 0)."""
    k = np.arange(1, terms + 1)[:, None]
    return U * y / H + np.sum(U * 2 * (-1.0) ** k / (k * math.pi) * np.sin(k * math.pi * y / H)
                              * np.exp(-(k * math.pi) ** 2 * nu * t / H**2), axis=0)


def test_couette_steady_profile_is_linear_to_round_off():
    fl = lattice(2, 16, 0.8, sides={**PER_X, "top": lbm.Wall(0.05)})
    fl.advance(int(40 * 256 / (0.1 * math.pi**2)))
    assert np.max(np.abs(fl.velocity()[0][0] - 0.05 * fl.y / 16)) / 0.05 < 1e-11


def test_couette_transient_against_the_series_at_second_order():
    """The start-up at nu t / H^2 = 0.05 (diffusive scaling, lid speed 0.05 * 8/ny): errors 6.0e-4, 1.5e-4, 3.7e-5 of U
    for ny = 8, 16, 32; negative control: the series with a viscosity 10 % off is 30 times farther."""
    errs, wrong = [], None
    for ny in (8, 16, 32):
        U, tau = 0.05 * 8 / ny, 0.8
        nu = (tau - 0.5) / 3
        fl = lattice(2, ny, tau, sides={**PER_X, "top": lbm.Wall(U)})
        fl.advance(int(round(0.05 * ny**2 / nu)))
        u = fl.velocity()[0][0]
        errs.append(np.max(np.abs(u - _couette_series(fl.y, fl.t, U, ny, nu))) / U)
        if ny == 32:
            wrong = np.max(np.abs(u - _couette_series(fl.y, fl.t, U, ny, 1.1 * nu))) / U
    assert errs[-1] < 5e-5
    assert all(3.8 < errs[i] / errs[i + 1] < 4.2 for i in range(2)), errs
    assert wrong > 30 * errs[-1]


# --- Taylor-Green --------------------------------------------------------------------------------------------------------
def _taylor_green(N, tau=0.8, u0=0.04, decay=-1.0):
    """Decay rate of the vortex u = U(-cos kx sin ky, sin kx cos ky) relative to 2 nu k^2 (diffusive scaling)."""
    nu = (tau - 0.5) / 3
    U, k = u0 * 16 / N, 2 * math.pi / N
    fl = lattice(N, N, tau, sides=PER)
    fl.set_flow(velocity=lambda X, Y: (-U * np.cos(k * X) * np.sin(k * Y), U * np.sin(k * X) * np.cos(k * Y)),
                pressure=lambda X, Y: -0.25 * U**2 * (np.cos(2 * k * X) + np.cos(2 * k * Y)))
    phi = -np.cos(k * fl._X) * np.sin(k * fl._Y)

    def amp():
        return float(np.sum(fl.velocity()[0] * phi) / np.sum(phi * phi))
    a0 = amp()
    n = int(round(1.0 / (2 * nu * k * k)))
    fl.advance(n)
    return -math.log(amp() / a0) / n / (2 * nu * k * k) - 1.0


def test_taylor_green_decays_as_exp_minus_2_nu_k2_t_at_second_order():
    """Relative errors of the rate 1.6e-2, 3.9e-3, 9.7e-4 for N = 16, 32, 64 (ratios 4.1, 4.0); negative control:
    exp(-nu k^2 t) (half the rate) is off by 1."""
    e = [_taylor_green(N) for N in (16, 32, 64)]
    assert abs(e[-1]) < 1.5e-3
    assert all(3.8 < e[i] / e[i + 1] < 4.3 for i in range(2)), e
    assert abs(2 * (1 + e[-1]) - 1) > 0.99  # the measured rate against nu k^2: twice it


def test_vorticity_and_pressure_fields_of_a_taylor_green_vortex():
    """The fields as set: vorticity 2 U k cos kx cos ky (centred differences: relative error (k dx)^2 / 6 = 1.6e-3 at
    N = 64) and pressure -rho U^2 (cos 2kx + cos 2ky) / 4 (to round-off of the conversion), in physical units."""
    N, U = 64, 0.02
    k = 2 * math.pi / (N * 1e-3)
    fl = lbm.Flow2D((N * 1e-3, N * 1e-3), 1e-3, nu=1e-6, rho=1000.0, dt=1e-3, sides=PER)
    fl.set_flow(velocity=lambda X, Y: (-U * np.cos(k * X) * np.sin(k * Y), U * np.sin(k * X) * np.cos(k * Y)),
                pressure=lambda X, Y: -0.25 * 1000.0 * U**2 * (np.cos(2 * k * X) + np.cos(2 * k * Y)))
    w = fl.vorticity()
    exact = 2 * U * k * np.cos(k * fl._X) * np.cos(k * fl._Y)
    err = np.max(np.abs(w - exact)) / (2 * U * k)
    assert err == pytest.approx((k * 1e-3) ** 2 / 6, rel=0.01)
    p = fl.pressure()
    assert np.max(np.abs(p + 0.25 * 1000.0 * U**2 * (np.cos(2 * k * fl._X) + np.cos(2 * k * fl._Y)))) < 1e-12


def test_threaded_cpu_step_equals_one_thread_bit_for_bit(monkeypatch):
    def run(threads):
        monkeypatch.setattr(lbm, "LBM_THREADS", threads)
        fl = _busy_flow()
        fl.advance(120)
        return fl
    a, b = run(1), run(4)
    assert len(lbm._blocks(b.nx, b.ny)) == 1  # this grid is small: one block - so check a big one as well
    monkeypatch.setattr(lbm, "MIN_BLOCK_NODES", 64)
    b = run(4)
    assert len(lbm._blocks(b.nx, b.ny)) == 4
    assert np.array_equal(a.populations(), b.populations()) and np.array_equal(a.dye(), b.dye(), equal_nan=True)


# --- conservation ----------------------------------------------------------------------------------------------------------
def _cavity_with_obstacles(interpolated=False, omega=0.0):
    fl = lattice(48, 40, 0.7, sides={"top": lbm.Wall(0.08)}, gravity=(0.0, -2e-5), dye=0.02)
    fl.add_obstacle(lbm.Disk((14.0, 15.0), 5.3), interpolated=interpolated, omega=omega)
    fl.add_obstacle(lbm.Rect((32.0, 12.0), (8.0, 4.0), 0.4))
    fl.add_obstacle(lbm.Polygon([(26.0, 28.0), (36.0, 30.0), (30.0, 34.0)]))
    fl.add_dye(lbm.Disk((24.0, 24.0), 6.0), 1.0)
    return fl


def test_closed_domain_conserves_mass_momentum_and_dye_to_round_off():
    """A driven cavity with three static obstacles, a body force and dye: the mass and the dye stay at their start
    values to round-off (nothing is booked), the momentum changes exactly by what the walls, obstacles and the body
    force exchange (booked per link)."""
    fl = _cavity_with_obstacles()
    m0, d0 = fl.balance()["lattice"]["mass"][0], fl.balance()["lattice"]["dye"][0]
    fl.advance(1500)
    b = fl.balance()
    assert abs(b["lattice"]["mass"][0] - m0) / m0 < roundoff(1500)
    assert abs(b["lattice"]["dye"][0] - d0) / d0 < roundoff(1500)
    assert abs(b["momentum"]["relative_residual"]) < roundoff(1500)
    assert set(b["momentum"]["booked"]) >= {"top", "bottom", "left", "right", "obstacle:0", "body_force"}
    assert all(c["ok"] for k, c in fl.checks().items() if k in ("mass", "momentum", "dye"))


def test_the_tight_bound_of_a_closed_domain_and_what_it_catches(monkeypatch):
    """Review B7 L18. A closed box with fixed walls, obstacles, a body force and dye: the mass and the dye stay within
    ``roundoff_tight`` (ten times eps sqrt(N_fluid steps) plus the sums' rounding: ~5e-15 of the total here, against
    6.7e-13 of ``roundoff``). Mutation: a leak of 1e-13 per step at one link, never booked, is caught by the tight bound
    (1.5e-10 in 1500 steps) and is not by the running one (~9e-14 of the total: below it)."""
    def box():
        fl = lattice(48, 40, 0.7, gravity=(0.0, -2e-5), dye=0.02)
        fl.add_obstacle(lbm.Disk((14.0, 15.0), 5.3))
        fl.add_obstacle(lbm.Rect((32.0, 12.0), (8.0, 4.0), 0.4))
        fl.set_flow(velocity=lambda X, Y: (0.03 * np.sin(math.pi * Y / 40), 0 * X))
        fl.add_dye(lbm.Disk((24.0, 24.0), 6.0), 1.0)
        return fl
    fl = box()
    m0, d0 = fl.balance()["lattice"]["mass"][0], fl.balance()["lattice"]["dye"][0]
    fl.advance(1500)
    b = fl.balance()
    assert abs(b["lattice"]["mass"][0] - m0) / m0 < roundoff_tight(fl, 1500, m0)
    assert abs(b["lattice"]["dye"][0] - d0) / d0 < roundoff_tight(fl, 1500, d0)
    assert roundoff_tight(fl, 1500, m0) < roundoff(1500) / 50
    step = lbm.Flow2D._step_cpu

    def leaky(self, s_in):
        step(self, s_in)
        self._f[1, 30, 30] += 1e-13
    monkeypatch.setattr(lbm.Flow2D, "_step_cpu", leaky)
    fl = box()
    fl.advance(1500)
    rel = abs(fl.balance()["mass"]["relative_residual"])
    assert rel > roundoff_tight(fl, 1500, m0) and rel < roundoff(1500)
    assert fl.checks()["mass"]["ok"]  # the running check's bound does not see it (documented)


def _long_channel():
    """The body-force channel 4 x 16 (tau 0.8, g 1e-5) of review LB1-physics P1, from the exact parabola."""
    nu, g, H = 0.1, 1e-5, 16.0
    fl = lattice(4, 16, 0.8, sides=PER_X, gravity=(g, 0.0))
    fl.set_flow(velocity=lambda X, Y: (g / (2 * nu) * Y * (H - Y), 0 * X))
    return fl


def test_the_running_check_holds_on_long_runs(monkeypatch):
    """Review LB1-physics P1 (STATUS V41 ac). The per-link records grow by the gross exchange (~0.2 per wall link per
    step): as plain running sums their rounding grew like n^2, and the running check failed this correct channel after
    9537 steps (1.7e-11 against 4.2e-12) and 6.1e-10 at 64 000. Kahan-compensated (both devices) and summed exactly per
    owner, the books are exact to their final rounding: the momentum residual over 64 000 steps stays below 1e-2 of the
    limit (measured 6.1e-14 against 2.8e-11, 2.1e-3; the reviewer's exact fsum of every step's records gave 6.8e-14),
    and every running check holds. Negative control: the same channel with the plain sums (``_kahan`` replaced by a
    plain addition) fails the momentum check at 9537 steps, as reported."""
    fl = _long_channel()
    fl.advance(64000)
    c = fl.checks()
    assert all(c[k]["ok"] for k in ("mass", "momentum", "mach", "re_cell", "compressibility")), c
    assert abs(c["momentum"]["relative_residual"]) < 1e-2 * c["momentum"]["limit"]
    assert abs(c["mass"]["relative_residual"]) < 1e-2 * c["mass"]["limit"]
    monkeypatch.setattr(lbm, "_kahan", lambda acc, cmp, x: (acc + x, cmp))
    bad = _long_channel()
    bad.advance(9537)
    cb = bad.checks()["momentum"]
    assert not cb["ok"] and abs(cb["relative_residual"]) > 2 * cb["limit"], cb


def test_interpolated_walls_leak_mass_but_the_balance_books_it():
    """Negative control of the mass check: with Bouzidi's interpolated bounce-back on the disk the mass drifts (by
    -5.2e-5 here), and the booked balance still closes to round-off. A rotating (Ladd) staircase disk exchanges
    momentum with the fluid; its balance closes too."""
    for kw in ({"interpolated": True}, {"omega": 0.004}):
        fl = _cavity_with_obstacles(**kw)
        m0 = fl.balance()["lattice"]["mass"][0]
        fl.advance(1500)
        b = fl.balance()
        if kw.get("interpolated"):
            assert abs(b["lattice"]["mass"][0] - m0) / m0 > 1e-6
        assert abs(b["mass"]["relative_residual"]) < roundoff(1500)
        assert abs(b["momentum"]["relative_residual"]) < roundoff(1500)


def test_inflow_outflow_balance():
    """A channel with a parabolic velocity inlet, a pressure outlet and an obstacle: the booked fluxes close the mass
    and momentum balances to round-off; the inlet's mass flux per step is rho0 Q of its profile (exact for the
    link-wise rule, after the ramp); at steady state what flows out equals what flows in."""
    U = 0.04
    fl = lattice(64, 16, 1.0, sides={"left": lbm.Inlet(U, "parabolic", ramp=200.0), "right": lbm.Outlet(0.0)},
                 dye=0.05)
    fl.add_obstacle(lbm.Disk((20.0, 8.0), 3.0))
    fl.add_dye_source(lbm.Disk((6.0, 8.0), 2.0), 1.0)
    fl.advance(6000)
    b = fl.balance()
    assert abs(b["mass"]["relative_residual"]) < roundoff(6000)
    assert abs(b["momentum"]["relative_residual"]) < roundoff(6000)
    assert abs(b["dye"]["relative_residual"]) < roundoff(6000)
    rates = fl.flow_rates()
    # the inlet's links: 6 w_i e_i.u at their wall points, i.e. (2/3) u at the cell centres and (1/6) u at both cell
    # edges from the diagonals (zero at the walls)
    prof = lambda s: 4 * U * s * (16 - s) / 16**2  # noqa: E731
    q_inlet = (2 / 3) * sum(prof(np.arange(16) + 0.5)) + (1 / 3) * sum(prof(np.arange(1, 16)))
    assert rates["left"] == pytest.approx(q_inlet, rel=1e-12)
    assert rates["right"] == pytest.approx(-q_inlet, rel=1e-6)


# --- dye ---------------------------------------------------------------------------------------------------------------------
def _blob_moments(fl):
    C = np.nan_to_num(fl.dye())
    M = C.sum()
    xm = (C * fl._X).sum() / M
    ym = (C * fl._Y).sum() / M
    return M, xm, ym, (C * (fl._X - xm) ** 2).sum() / M, (C * (fl._Y - ym) ** 2).sum() / M


@pytest.mark.parametrize("ux", [0.0, 0.05])
def test_dye_variance_grows_as_2_d_t_with_the_schemes_flow_correction(ux):
    """A blob in a uniform flow (periodic box, no walls): the centre moves with the flow and the variance grows as
    2 D t exactly per step in y, and in x as 2 (D - (tau_g- - 1/2) u^2) t (the linear D2Q5 equilibrium's numerical
    diffusion along the flow, stated in the module); the amount of dye is conserved to round-off."""
    fl = lattice(128, 96, 1.0, sides=PER, dye=0.05)
    fl.set_flow(velocity=(ux, 0.0))
    fl.add_dye(lbm.Disk((64.0 - 160 * ux, 48.0), 4.0), 1.0)  # centred in the box at mid-run: wrapped tails cancel
    fl.advance(100)  # past the start-up of the non-equilibrium parts ((1 - omega_g+)^100 ~ 1e-27)
    M0, x0, y0, vx0, vy0 = _blob_moments(fl)
    n = 300
    fl.advance(n)
    M1, x1, y1, vx1, vy1 = _blob_moments(fl)
    D = (fl.tau_gm - 0.5) / 3
    assert abs(M1 - M0) / M0 < roundoff(400)
    assert x1 - x0 == pytest.approx(ux * n, abs=1e-9)
    assert (vy1 - vy0) / (2 * n) == pytest.approx(D, rel=1e-9)
    assert (vx1 - vx0) / (2 * n) == pytest.approx(D - (fl.tau_gm - 0.5) * ux**2, rel=1e-6)


def test_dye_floor_is_reported():
    fl = lattice(16, 16, 0.8, sides=PER, dye=1e-9)
    n = fl.numbers()
    assert n["dye_diffusivity"] == pytest.approx((lbm.DYE_TAU_MIN - 0.5) / 3, rel=1e-12)
    assert n["dye_diffusivity_asked"] == 1e-9


# --- geometry at a running moment -----------------------------------------------------------------------------------------
@pytest.mark.parametrize("displaced", ["remove", "spread"])
def test_obstacle_added_and_removed_while_running(displaced):
    """A periodic box with flow: an obstacle added at a running moment removes the fluid in its nodes, booked exactly
    ("remove"), or returns that mass to the fluid ("spread": total mass to round-off); removed again, its nodes become
    fluid at the mean density of their fluid neighbours. The balance closes to round-off throughout."""
    fl = lattice(64, 48, 0.8, sides=PER, gravity=(1e-5, 0.0), dye=0.05, displaced=displaced)
    fl.add_dye(lbm.Rect((20.0, 24.0), (10.0, 30.0)), 1.0)
    fl.advance(300)
    m_before = fl.balance()["lattice"]["mass"][0]
    f_before = fl.populations()
    oid = fl.add_obstacle(lbm.Disk((24.0, 24.0), 7.0))
    covered = fl.solid()
    removed = float(f_before[:, covered].sum())
    m_after = fl.balance()["lattice"]["mass"][0]
    if displaced == "remove":
        assert m_after == pytest.approx(m_before - removed, rel=1e-14)
        assert fl.balance()["lattice"]["books"]["geometry"][0] == pytest.approx(-removed, rel=1e-12)
    else:
        assert abs(m_after - m_before) / m_before < roundoff(1)
    fl.advance(300)
    rho_neigh = fl.populations().sum(axis=0)
    fl.remove_obstacle(oid)
    r = fl.populations().sum(axis=0)
    rim = covered & ~np.roll(covered, 1, 0)
    ii, jj = np.argwhere(rim)[0]
    nb = [(ii + a) % 64 for a in (-1, 0, 1)]
    nbj = [(jj + c) % 48 for c in (-1, 0, 1)]
    vals = [rho_neigh[a, c] for a in nb for c in nbj if not covered[a, c]]
    if displaced == "remove":
        assert r[ii, jj] == pytest.approx(np.mean(vals), rel=1e-14)
    fl.advance(300)
    b = fl.balance()
    assert abs(b["mass"]["relative_residual"]) < roundoff(900)
    assert abs(b["momentum"]["relative_residual"]) < roundoff(900)
    assert abs(b["dye"]["relative_residual"]) < roundoff(900)
    if displaced == "spread":
        assert abs(b["lattice"]["mass"][0] - m_before) / m_before < roundoff(600)


def test_edits_are_all_or_nothing():
    fl = lattice(32, 32, 0.8, sides=PER)
    fl.advance(10)
    s0 = fl.state_dict()
    with pytest.raises(ValueError):
        fl.set_side("left", lbm.Wall())  # its periodic partner stays periodic: refused
    with pytest.raises(ValueError):
        fl.add_obstacle(lbm.Disk((10.0, 10.0), 3.0), interpolated=True, omega=0.1)
    with pytest.raises(ValueError):
        fl.set_sides({"top": lbm.Wall(0.9)})  # Ma > 0.3
    s1 = fl.state_dict()
    assert np.array_equal(s0["f"], s1["f"]) and s0["sides"] == s1["sides"] and s1["obstacles"] == []


# --- forces ------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("interpolated", [False, True])
def test_steady_drag_of_a_periodic_array_equals_the_body_force(interpolated):
    """Steady flow through a periodic array of disks driven by a body force g: the momentum exchange on the disk equals
    rho0 g times the fluid area (the momentum balance, exact at steady state: 1e-9 here); the lift and the torque of the
    symmetric set-up vanish."""
    g = 2e-6
    fl = lattice(40, 40, 1.0, sides=PER, gravity=(g, 0.0))
    oid = fl.add_obstacle(lbm.Disk((20.0, 20.0), 6.2), interpolated=interpolated)
    fl.advance(12000)
    fl.reset_force_mean()
    fl.advance(200)
    F = fl.forces()[oid]
    target = g * (~fl.solid()).sum()
    assert F["force"][0] == pytest.approx(target, rel=1e-8)
    assert F["mean"]["drag"] == pytest.approx(target, rel=1e-8)
    assert abs(F["force"][1]) < 1e-8 * target
    assert abs(F["torque"]) < 1e-10


# --- state, pickling, refusals, units --------------------------------------------------------------------------------------
def _busy_flow(device="cpu"):
    fl = lbm.Flow2D((0.12, 0.041), 0.001, nu=1e-5, rho=1.0, u_max=0.003, mach=0.1, device=device, dye=1e-6,
                    sides={"left": lbm.Inlet(0.003, "parabolic", dye=0.5, ramp=0.4), "right": lbm.Outlet(1e-6)},
                    gravity=(1e-6, 2e-7))
    fl.add_obstacle(lbm.Disk((0.02, 0.02), 0.005), interpolated=True)
    fl.add_obstacle(lbm.Rect((0.06, 0.02), (0.01, 0.005), 0.3), omega=0.05)
    fl.add_obstacle(lbm.Polygon([(0.09, 0.005), (0.1, 0.01), (0.095, 0.02)]), velocity=(0.001, 0.0))
    fl.add_dye_source(lbm.Disk((0.01, 0.03), 0.002), 2.0)
    return fl


def test_state_round_trip_continues_bit_identically():
    fl = _busy_flow()
    fl.advance(100)
    fl.reset_force_mean()
    fl.advance(30)
    d = fl.state_dict()
    g = lbm.Flow2D.from_state_dict(d)
    h = pickle.loads(pickle.dumps(fl))
    for o in (fl, g, h):
        o.advance(150)
        o.add_obstacle(lbm.Disk((0.08, 0.03), 0.004))
        o.advance(70)
    for o in (g, h):
        assert np.array_equal(fl.populations(), o.populations())
        assert np.array_equal(fl.dye(), o.dye(), equal_nan=True)
        assert fl.balance()["lattice"] == o.balance()["lattice"]
        assert fl.forces() == o.forces()


def test_refusals_and_the_blow_up_guard():
    with pytest.raises(ValueError, match="Маха"):
        lbm.Flow2D((0.1, 0.1), 1e-3, nu=1e-4, u_max=1.0, mach=0.35)
    with pytest.raises(ValueError, match="τ"):
        lbm.Flow2D((0.1, 0.1), 1e-3, nu=1e-9, dt=1e-3)
    with pytest.raises(ValueError, match="Рейнольдса"):  # closed: 25 accepted, open: 10
        lbm.Flow2D((0.1, 0.1), 1e-3, nu=1e-6, u_max=0.02, mach=0.1, sides={"left": lbm.Inlet(0.02),
                                                                           "right": lbm.Outlet()})
    lbm.Flow2D((0.1, 0.1), 1e-3, nu=1e-6, u_max=0.02, mach=0.1)
    fl = lattice(32, 32, 0.501, sides=PER)
    fl.advance(5)
    s0 = fl.populations()
    U = np.random.default_rng(1).normal(size=(2, 32, 32)) * 0.3  # Ma ~ 1 at tau = 0.501: blows up
    fl.set_flow(velocity=(U[0], U[1]))
    s1 = fl.populations()
    with pytest.raises(lbm.Unstable, match="восстановлено"):
        fl.advance(3000)
    assert np.array_equal(fl.populations(), s1) and fl.steps == 5 and not np.array_equal(s0, s1)


def test_units_numbers_and_cost():
    u = lbm.Units.from_flow(1e-3, nu=1e-6, u_max=0.01, mach=0.1, rho=998.2072)
    assert u.velocity(0.1 * lbm.CS) == pytest.approx(0.01, rel=1e-14)
    fl = lbm.Flow2D((0.2, 0.05), 1e-3, nu=1e-5, rho=998.2, u_max=0.02, mach=0.1, sides={"left": lbm.Inlet(0.02),
                                                                                       "right": lbm.Outlet()})
    fl.add_obstacle(lbm.Disk((0.05, 0.025), 0.005))
    n = fl.numbers()
    assert n["re"] == pytest.approx(0.02 * 0.01 / 1e-5)
    assert n["mach_declared"] == pytest.approx(0.1)
    c = fl.cost_estimate()
    assert c["per_step_s"] > 0 and c["device"] == fl.device
    assert "fluids.lbm" in backend.kernels()


def test_fluid_properties_from_their_sources():
    w = lbm.fluid_properties("water", 20.0)
    assert (w["rho"], w["mu"]) == (998.2072, 0.001001596)
    tab = np.array(lbm.WATER_1ATM)
    ev, od = tab[1::2], tab[2:-1:2]  # interpolate from every second row onto the others
    mu_i = np.exp(np.interp(od[:, 0], ev[:, 0], np.log(ev[:, 2])))
    assert np.max(np.abs(mu_i / od[:, 2] - 1)) < 4e-4
    a = lbm.fluid_properties("air", 15.0)
    assert round(a["rho"], 4) == 1.2250  # the standard's sea-level row (table I, p. 52)
    assert round(lbm.fluid_properties("air", 20.2, p=111310.0)["rho"], 4) == 1.3219  # its -800 m row
    assert a["mu"] == pytest.approx(1.458e-6 * 288.15**1.5 / (288.15 + 110.4), rel=1e-15)
    with pytest.raises(ValueError):
        lbm.fluid_properties("water", 50.0)


# --- review B7: time origin, inlet ramps, imposed densities, the force record ----------------------------------------------
def _channel(**kw):
    sides = kw.pop("sides", {"left": lbm.Inlet(0.2, "parabolic", ramp=0.5), "right": lbm.Outlet()})
    fl = lbm.Flow2D((0.4, 0.1), 0.004, nu=1e-3, rho=1.0, u_max=0.3, mach=0.1, device="cpu", sides=sides, dye=1e-3,
                    **kw)
    fl.add_obstacle(lbm.Disk((0.1, 0.05), 0.01))
    return fl


def test_a_flow_started_at_a_time_counts_its_steps_from_it():
    """Review B7 L2: Flow2D(t0=T) starts at T; every advance keeps t = T + steps dt (before, a time set from outside
    was lost at the first advance and the second computed T/dt steps at once); the inlet ramp starts at T; the state
    round trip keeps the origin. Negative control: the same flow from 0 has the same steps but a time T earlier."""
    a = _channel(t0=0.2)
    assert a.t == 0.2 and a.steps == 0 and a.inlet_scales()["left"] == 0.0
    n1 = int(round(0.01 / a.units.dt))
    a.advance_to(0.21)
    assert a.steps == n1 and a.t == pytest.approx(0.2 + n1 * a.units.dt, rel=1e-15)
    a.advance_to(0.22)
    assert a.steps == int(round(0.02 / a.units.dt)) and a.t == pytest.approx(0.22, abs=a.units.dt)
    b = _channel()
    b.advance(a.steps)
    assert np.array_equal(a.populations(), b.populations()) and a.t - b.t == pytest.approx(0.2, rel=1e-12)
    c = lbm.Flow2D.from_state_dict(a.state_dict())
    for o in (a, c):
        o.advance(50)
    assert c.t == a.t and np.array_equal(a.populations(), c.populations())
    with pytest.raises(ValueError):
        _channel(t0=float("nan"))


def test_an_inlet_edit_that_keeps_its_velocity_keeps_the_inflow_and_a_new_velocity_blends():
    """Review B7 L1. The inlets' ramps are per side. At a developed state: an edit of the inlet's dye, and a second
    inlet on another side, leave the inflow exactly as it was (before, both restarted the ramp of every inlet: the
    inflow fell to zero and the Kármán preset blew up); a new velocity (0.2 -> 0.24 m/s, ramp 0.2 s) blends from the
    old inflow to the new: inflow = (1 - s) Q_old + s Q_new at every step (the link-wise inflow is exact), monotone, and
    the balances close. Negative control: a ramp from rest (the side was a wall) starts at zero."""
    fl = _channel()
    fl.advance_to(1.0)
    q0 = fl.flow_rates()["left"]
    fl.set_side("left", lbm.Inlet(0.2, "parabolic", ramp=0.5, dye=0.5))
    assert fl.flow_rates()["left"] == q0  # the last step's record is kept through the edit (L14)
    fl.advance(1)
    assert fl.flow_rates()["left"] == pytest.approx(q0, rel=1e-14) and fl.inlet_scales()["left"] == 1.0
    fl.set_side("top", lbm.Inlet(0.01, "uniform"))
    fl.advance(1)
    assert fl.flow_rates()["left"] == pytest.approx(q0, rel=1e-14)
    fl.set_side("top", lbm.Wall())
    fl.set_side("left", lbm.Inlet(0.24, "parabolic", ramp=0.2, dye=0.5))
    qs = []
    for _ in range(int(round(0.25 / fl.units.dt))):
        fl.advance(1)
        s = fl.inlet_scales()["left"]
        qs.append(fl.flow_rates()["left"])
        assert qs[-1] == pytest.approx((1 - s) * q0 + s * 1.2 * q0, rel=1e-13)
    assert np.all(np.diff(qs) >= -1e-14 * q0) and qs[-1] == pytest.approx(1.2 * q0, rel=1e-13)
    b = fl.balance()
    assert abs(b["mass"]["relative_residual"]) < roundoff(fl.steps)
    fl.set_side("left", lbm.Wall())
    fl.set_side("left", lbm.Inlet(0.24, "parabolic", ramp=0.2))
    fl.advance(1)
    assert fl.flow_rates()["left"] < 1e-3 * q0


def test_a_fluid_at_rest_in_a_body_force_stays_at_rest_also_with_an_outlet():
    """Review B7 L6. A body force switched on: the fluid takes the hydrostatic density at once (c_s^2 grad rho = rho0
    g, lattice) and the outlet the hydrostatic part along its side, so the rest state is steady: after 20 s max |u| <
    1e-8 m/s (8.8e-10 measured). Negative control: an outlet at one density along its side (the former rule) drives a
    circulation of 0.13 m/s. A force whose rest state deviates from rho0 by more than RHO_DEV_MAX is refused and
    leaves the flow as it was; at the limit the density stays within the running check's MACH_MAX^2 (0.045 measured)."""
    def box(uniform_outlet=False):
        fl = lbm.Flow2D((0.4, 0.1), 0.002, nu=1e-3, rho=1.0, u_max=0.05, mach=0.1, device="cpu",
                        sides={"right": lbm.Outlet(0.0)})
        if uniform_outlet:
            fl._outlet_density = lambda name, side, s, gravity=None, sides=None: np.full_like(np.asarray(s, float), 1.0)
        fl.set_gravity((0.0, -0.5))
        fl.advance_to(20.0)
        return fl
    fl = box()
    assert np.nanmax(fl.speed()) < 1e-8
    assert abs(fl.balance()["mass"]["relative_residual"]) < roundoff(fl.steps)
    assert np.nanmax(box(uniform_outlet=True).speed()) > 0.05
    big = lbm.Flow2D((2.2, 0.41), 0.005, nu=1e-3, rho=1.0, u_max=0.45, mach=0.1, device="cpu")
    s0 = big.state_dict()
    with pytest.raises(ValueError, match="объёмная сила"):
        big.set_gravity((0.0, -9.81))  # g H / c_s^2 = 0.199: deviation 0.099 > 0.045
    assert big.gravity == (0.0, 0.0) and np.array_equal(big.populations(), s0["f"])
    g_lim = 2 * lbm.RHO_DEV_MAX * lbm.CS2 * big.units.dx**2 / big.units.dt**2 / big.size[1]  # deviation g_lat H / 2 c_s^2
    big.set_gravity((0.0, -0.999 * g_lim))
    big.advance_to(2.0)
    lo, hi = big.numbers()["density_range"]
    assert max(1 - lo, hi - 1) < lbm.MACH_MAX**2 and big.checks()["compressibility"]["ok"]


def test_the_outlet_pressure_is_checked_and_named_when_the_flow_fails():
    """Review B7 L7. An outlet pressure whose lattice density deviates by more than RHO_DEV_MAX (the scale c_s^2 rho
    (dx/dt)^2 = 20.25 Pa here: 10 Pa is a density 1.49) is refused; at the limit the reflected step stays within the
    running check (0.089 measured over 6 s). A blow-up names the imposed outlet pressure."""
    fl = lbm.Flow2D((1.1, 0.2), 0.005, nu=1e-3, rho=1.0, u_max=0.45, mach=0.1, device="cpu")
    for p in (10.0, 1.0):
        with pytest.raises(ValueError, match="давление выхода"):
            fl.set_side("right", lbm.Outlet(p))
    p_lim = lbm.RHO_DEV_MAX * lbm.CS2 * fl.units.rho * fl.units.c**2
    fl.set_side("right", lbm.Outlet(0.999 * p_lim))
    dev = 0.0
    for _ in range(30):
        fl.advance_to(fl.t + 0.1)
        lo, hi = fl.numbers()["density_range"]
        dev = max(dev, 1 - lo, hi - 1)
    assert lbm.RHO_DEV_MAX < dev < lbm.MACH_MAX**2  # the step doubled at the closed end, within the check
    bad = lattice(32, 32, 0.501, sides={"right": lbm.Outlet(0.01)})
    U = np.random.default_rng(1).normal(size=(2, 32, 32)) * 0.3
    bad.set_flow(velocity=(U[0], U[1]))
    with pytest.raises(lbm.Unstable, match="давление на выходе"):
        bad.advance(3000)


def test_a_coefficient_length_set_back_to_zero_is_the_default_again():
    """Review B7 L10: ref_length 0 means the width across the flow; a custom length set back to 0 is cleared (before,
    it stayed: C_x and C_y half their values, silently). Negative values are refused."""
    fl = _channel()
    oid = 0
    assert fl.forces()[oid]["length"] == pytest.approx(0.02)
    fl.update_obstacle(oid, ref_length=0.2)
    assert fl.forces()[oid]["length"] == 0.2
    fl.update_obstacle(oid, ref_length=0.0)
    assert fl.forces()[oid]["length"] == pytest.approx(0.02)
    fl.update_obstacle(oid, label="x")  # None keeps
    assert fl.forces()[oid]["length"] == pytest.approx(0.02)
    with pytest.raises(ValueError):
        fl.update_obstacle(oid, ref_length=-1.0)


def test_flow_rates_right_after_an_edit_are_the_last_steps():
    """Review B7 L14: after an edit and before the next step, flow_rates() gives the last step's rates (as forces()
    does), not zeros."""
    fl = lattice(120, 30, 0.65, sides={"left": lbm.Inlet(0.03, "parabolic"), "right": lbm.Outlet(0.0)})
    fl.advance(500)
    before = fl.flow_rates()
    fl.add_obstacle(lbm.Disk((80.0, 15.0), 3.0))
    assert fl.flow_rates() == before and before["left"] > 0


def test_the_acoustic_period_against_the_measured_ringing():
    """The domain's slowest standing sound wave: a plug flow started at once between a velocity inlet (closed for
    sound) and an outlet (open) rings at 4 L / c_s (measured 1386.3 steps against 1385.6, L = 200), a pressure mode
    between two walls at 2 L / c_s (692.83 against 692.82), a periodic axis L / c_s. Negative control: the
    channel's ringing is not 2 L / c_s."""
    def period(fl, n, every=10, skip=100):
        ts, ps = [], []
        for _ in range(n // every):
            fl.advance(every)
            ts.append(fl.t)
            ps.append(fl.populations()[:, 0, :].sum(axis=0).mean())
        ts, ps = np.array(ts[skip // every:]), np.array(ps[skip // every:])
        c = ps - ps.mean()
        up = np.flatnonzero((c[:-1] < 0) & (c[1:] >= 0))
        tz = ts[up] - c[up] * (ts[up + 1] - ts[up]) / (c[up + 1] - c[up])
        return (tz[-1] - tz[0]) / (len(tz) - 1)
    a = lattice(200, 4, 0.52, sides={"left": lbm.Inlet(0.01), "right": lbm.Outlet(), "bottom": "periodic",
                                     "top": "periodic"})
    ap = a.acoustic_period()
    assert ap["x"]["kind"] == "closed-open" and ap["y"]["kind"] == "periodic" and ap["axis"] == "x"
    assert ap["period"] == pytest.approx(4 * 200 / lbm.CS, rel=1e-14) and ap["y"]["period"] == pytest.approx(4 / lbm.CS)
    T = period(a, 14000)
    assert T == pytest.approx(ap["period"], rel=2e-3) and abs(T / (2 * 200 / lbm.CS) - 1) > 0.9
    b = lattice(200, 4, 0.52, sides={"bottom": "periodic", "top": "periodic"})
    b.set_flow(pressure=lambda X, Y: 1e-3 * np.cos(math.pi * X / 200))
    assert b.acoustic_period()["x"]["kind"] == "closed-closed"
    assert period(b, 8000, skip=0) == pytest.approx(b.acoustic_period()["period"], rel=2e-3)


def test_the_force_record_is_the_mean_over_whole_blocks_whatever_the_calls():
    """The force record (block means of the momentum exchange): the mean of its blocks over a span equals the engine's
    mean since ``reset_force_mean`` over the same steps (a second method, to 1e-12); it is the same however advance is
    called; an edit of the flow's set-up restarts it (a dye source does not); it survives the state round trip and
    pickling; a steady periodic array's blocks equal the body force (closed form, 1e-8)."""
    def run(split):
        fl = _channel()
        fl.advance_to(0.5)
        fl.record_forces(25)
        fl.reset_force_mean()
        for n in split:
            fl.advance(n)
        return fl
    a, b = run([1000]), run([7, 333, 1, 659])
    ra, rb = a.force_record(), b.force_record()
    assert np.array_equal(ra["t_end"], rb["t_end"]) and np.array_equal(ra["obstacles"][0]["force"],
                                                                       rb["obstacles"][0]["force"])
    assert len(ra["t_end"]) == 40
    assert np.allclose(ra["obstacles"][0]["force"].mean(axis=0), a.forces()[0]["mean"]["force"], rtol=1e-12, atol=0)
    a.add_dye_source(lbm.Disk((0.02, 0.05), 0.005), 1.0)
    assert len(a.force_record()["t_end"]) == 40
    c = lbm.Flow2D.from_state_dict(a.state_dict())
    for o in (a, c):
        o.advance(60)
    assert np.array_equal(a.force_record()["obstacles"][0]["force"], c.force_record()["obstacles"][0]["force"])
    a.update_obstacle(0, shape=lbm.Disk((0.12, 0.05), 0.01))
    r = a.force_record()
    assert len(r["t_end"]) == 0 and r["since"] == pytest.approx(a.t)
    g = 2e-6
    p = lattice(40, 40, 1.0, sides=PER, gravity=(g, 0.0))
    oid = p.add_obstacle(lbm.Disk((20.0, 20.0), 6.2))
    p.advance(12000)
    p.record_forces(50)
    p.advance(200)
    F = p.force_record()["obstacles"][oid]["force"]
    assert np.allclose(F[:, 0], g * (~p.solid()).sum(), rtol=1e-8)


def test_the_velocity_inlet_leaves_a_transverse_layer_that_grows_with_the_cell_reynolds_number():
    """Review B7 L12 (documented, not removed): a plain channel started from the exact parabola keeps a transverse
    velocity at the link-wise velocity inlet: max |u_y| / U in the inlet column 0.0040 at cell Re 1 and 0.038 at 10
    (0.0020 at column 20); the edge of stability with an inlet (cell Re ~12 with TRT in a plain channel, the reviewer's
    r07; a periodic channel driven by a force is stable at 60) is the inlet's: RE_CELL_MAX_OPEN = 10."""
    U = 0.1 * lbm.CS
    out = {}
    for rc in (1, 10):
        fl = lbm.Flow2D((120.0, 42.0), 1.0, nu=U / rc, rho=1.0, dt=1.0, device="cpu",
                        sides={"left": lbm.Inlet(U, "parabolic"), "right": lbm.Outlet(0.0)})
        fl.set_flow(velocity=lambda X, Y: (4 * U * Y * (42 - Y) / 42**2, 0 * X))
        fl.advance(8000)
        a = np.abs(fl.velocity()[1]) / U
        out[rc] = (a[0].max(), a[20].max())
    assert 0.0036 < out[1][0] < 0.0044 and 0.034 < out[10][0] < 0.042, out
    assert out[10][1] < 0.1 * out[10][0], out


def test_a_body_with_a_surface_velocity_stays_where_it_is():
    """Review B7 L3 (what the engine does, stated in the playground): an obstacle given a velocity keeps its nodes; its
    surface velocity makes the front half a source and the back half a sink (equal and opposite, booked)."""
    fl = lbm.Flow2D((0.4, 0.2), 0.004, nu=1e-3, rho=1.0, u_max=0.1, mach=0.1, device="cpu")
    oid = fl.add_obstacle(lbm.Disk((0.2, 0.1), 0.02), velocity=(0.05, 0.0))
    solid0 = fl.solid()
    fl.advance_to(1.0)
    assert np.array_equal(solid0, fl.solid()) and fl.obstacles()[0]["center"] == [0.2, 0.1]
    k = fl._L["owner"] == oid
    acc = fl._link_acc()["acc_m"][k]
    front = fl._L["wx"][k] > 0.2
    assert acc[front].sum() > 1.0 and acc[~front].sum() < -1.0
    assert abs(acc.sum()) < 1e-12 * acc[front].sum()
    assert abs(fl.balance()["mass"]["relative_residual"]) < roundoff(fl.steps)


# --- GPU ---------------------------------------------------------------------------------------------------------------------
@pytest.mark.skipif(not _gpu(), reason="no GPU given to this container")
def test_gpu_equals_cpu_bit_for_bit():
    """Every link type (bounce-back, moving, inlet with its ramp, both interpolated kinds, the outlet with its
    hydrostatic part), the body force, the dye with its source and inlet, a geometry change in between, an inlet's new
    velocity blending from the old one while a second inlet ramps from rest (per-side scales, review B7 L1), the force
    record: the GPU state equals the CPU state bit for bit."""
    backend.configure({"kernels": {"fluids.lbm": {"device": "gpu", "precision": "fp64"}}})
    c, g = _busy_flow("cpu"), _busy_flow("auto")
    assert c.device == "cpu" and g.device == "gpu"
    for o in (c, g):
        o.record_forces(17)
    for k in range(3):
        c.advance(300)
        g.advance(300)
        assert np.array_equal(c.populations(), g.populations())
        assert np.array_equal(c.dye(), g.dye(), equal_nan=True)
        assert all(np.array_equal(v, g._link_acc()[k]) for k, v in c._link_acc().items())
        for o in (c, g):
            if k == 0:
                o.add_obstacle(lbm.Disk((0.1, 0.03), 0.003))
            elif k == 1:
                o.set_sides({"left": lbm.Inlet(0.0025, "parabolic", dye=0.5, ramp=10.0),
                             "top": lbm.Inlet(0.0005, "uniform", ramp=20.0)})
    assert c.inlet_scales()["left"] < 1.0 and c.inlet_scales()["top"] < c.inlet_scales()["left"]
    rc, rg = c.force_record(), g.force_record()
    assert len(rc["t_end"]) > 0 and all(np.array_equal(rc["obstacles"][i]["force"], rg["obstacles"][i]["force"])
                                        for i in rc["obstacles"])
    assert c.forces() == g.forces()
    assert g.balance()["mass"]["relative_residual"] == pytest.approx(c.balance()["mass"]["relative_residual"],
                                                                    abs=1e-14)
