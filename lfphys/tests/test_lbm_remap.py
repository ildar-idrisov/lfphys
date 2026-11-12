# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plan P16.1 (the bench that never restarts): a 2-D flow continued on another grid, domain or time step
(``Flow2D.remap``) against closed forms — Poiseuille's parabola across a refinement, a coarsening and a new time step
(also from tau = 1, where the post-collision rescaling of Filippova & Haenel is singular), with two negative controls
(the populations copied as they are; the non-equilibrium part carried over without its rescaling); a Taylor-Green vortex
refined half-way against its exact decay and against the runs on either grid alone (control: naive copying); a new time
step at the same nodes; a domain grown and cropped (the fluid copied exactly where the nodes are the old ones, the books
closed, a crop through a body refused with the flow untouched); the state's round trip after a remap; the GPU against
the CPU after a remap."""

import math

import numpy as np
import pytest

from lfphys.core import backend
from lfphys.core.fluids import lbm

PER_X = {"left": "periodic", "right": "periodic"}
PER = {s: "periodic" for s in lbm.SIDES}
EPS = float(np.finfo(float).eps)


@pytest.fixture(autouse=True)
def _defaults():
    backend.configure(None)
    yield
    backend.configure(None)


def _gpu():
    return backend.devices()["gpu"]["available"]


def _poiseuille(tau=0.8, ny=8, g=1e-5, **kw):
    """The steady channel between half-way walls (lattice units dx = dt = 1, nu = (tau - 1/2)/3), x periodic."""
    nu = (tau - 0.5) / 3
    fl = lbm.Flow2D((4.0, float(ny)), 1.0, nu=nu, rho=1.0, dt=1.0, sides=PER_X, gravity=(g, 0.0), device="cpu", **kw)
    H = float(ny)
    fl.set_flow(velocity=lambda X, Y: (g / (2 * nu) * Y * (H - Y), 0 * X))
    fl.advance(int(36 * H**2 / (nu * math.pi**2)) + 200)
    return fl, nu, g, H


def _worst(fl, nu, g, H, steps):
    """The largest deviation from the parabola, relative to its peak, now and over the next ``steps`` steps."""
    def err():
        exact = g / (2 * nu) * fl.y * (H - fl.y)
        return float(np.max(np.abs(fl.velocity()[0] - exact[None, :])) / exact.max())
    w = err()
    for _ in range(steps):
        fl.advance(1)
        w = max(w, err())
    return w


@pytest.mark.parametrize("dx,dt", [(0.5, 0.25), (0.5, 0.5), (2.0, 4.0), (1.0, 0.5)],
                         ids=["refine-diffusive", "refine-acoustic", "coarsen", "new-time-step"])
@pytest.mark.parametrize("tau", [0.8, 1.0])
def test_poiseuille_continues_exactly_across_a_remap(tau, dx, dt):
    """TRT's steady channel is the exact parabola (to round-off); the remap's transfer (quadratic ghosts at the walls, the
    four-point interpolation, the non-equilibrium part rescaled) carries it over and the flow on the new grid stays on
    the parabola for 200 steps to round-off, whatever the new tau (tau = 1 -> 1.5 included); the balances close (the
    transfer's change booked). Measured: <= 1.3e-12 of the peak."""
    if dx == 2.0:
        fl, nu, g, H = _poiseuille(tau, ny=16)
    else:
        fl, nu, g, H = _poiseuille(tau)
    b0 = fl.balance()
    r = fl.remap(dx=dx, dt=dt)
    assert r["after"]["nodes"] == [round(4 / dx), round(H / dx)] and fl.units.dt == dt
    assert _worst(fl, nu, g, H, 200) < 1e-10
    b = fl.balance()
    # the residuals in physical units move by the rounding of the books put into the new units: under 4 ulps of their
    # gross size (measured 0.3-0.5; the "relative" momentum residual is per lattice mass, so unit-dependent)
    assert abs(b["mass"]["residual"] - b0["mass"]["residual"]) < 1e-13 * b["mass"]["now"]
    dP = max(abs(b["momentum"]["residual"][q] - b0["momentum"]["residual"][q]) for q in (0, 1))
    gross = sum(abs(v[0]) + abs(v[1]) for v in b["momentum"]["booked"].values())
    assert dP < 4 * EPS * gross
    assert "remap" in b["mass"]["booked"] or r["transfer"]["mass"] == 0.0


def test_poiseuille_negative_controls(monkeypatch):
    """What the transfer's parts do. (1) The populations copied as they are onto the refined grid (each node the old
    node's populations, i.e. lattice velocities read in the new units): the velocity doubles (c' = 2 c) — off by the
    whole profile. (2) The non-equilibrium part carried over without its rescaling (tau+ dt / tau+' dt' = 4 times too
    large a viscous stress): the flow leaves the parabola by ~1e-2 of its peak before the stress settles, 10^9 times the
    rescaled transfer's deviation."""
    fl, nu, g, H = _poiseuille(1.0)
    old = fl.populations()
    naive = lbm.Flow2D((4.0, H), 0.5, nu=nu, rho=1.0, dt=0.25, sides=PER_X, gravity=(g, 0.0), device="cpu")
    naive._f = np.ascontiguousarray(np.repeat(np.repeat(old, 2, axis=1), 2, axis=2))
    assert _worst(naive, nu, g, H, 20) > 0.9
    monkeypatch.setattr(lbm, "REMAP_NEQ_RESCALE", False)
    fl.remap(dx=0.5, dt=0.25)
    w = _worst(fl, nu, g, H, 200)
    assert w > 1e-3, w


def _tg_flow(N, dx, dt, tau=0.8, u0=0.02):
    """A Taylor-Green vortex in the periodic box of side 32 (lattice units of the coarse grid)."""
    L = 32.0
    nu = (tau - 0.5) / 3  # the coarse grid's lattice viscosity: dx = dt = 1 there
    k = 2 * math.pi / L
    fl = lbm.Flow2D((L, L), dx, nu=nu, rho=1.0, dt=dt, sides=PER, device="cpu")
    fl.set_flow(velocity=lambda X, Y: (-u0 * np.cos(k * X) * np.sin(k * Y), u0 * np.sin(k * X) * np.cos(k * Y)),
                pressure=lambda X, Y: -0.25 * u0**2 * (np.cos(2 * k * X) + np.cos(2 * k * Y)))
    return fl, nu, k, u0


def _tg_err(fl, nu, k, u0):
    a = u0 * math.exp(-2 * nu * k * k * fl.t)
    ux, uy = fl.velocity()
    return float(max(np.max(np.abs(ux + a * np.cos(k * fl._X) * np.sin(k * fl._Y))),
                     np.max(np.abs(uy - a * np.sin(k * fl._X) * np.cos(k * fl._Y)))) / a)


def _tg_rate(fl, k, steps):
    """The decay rate of the vortex's amplitude (its projection on the mode) over the next ``steps`` steps."""
    phi = -np.cos(k * fl._X) * np.sin(k * fl._Y)

    def amp():
        return float(np.sum(fl.velocity()[0] * phi) / np.sum(phi * phi))
    a0, t0 = amp(), fl.t
    fl.advance(steps)
    return -math.log(amp() / a0) / (fl.t - t0)


def test_taylor_green_refined_half_way_against_its_exact_decay():
    """32^2 for 300 steps, then 64^2 (dx/2, dt/4: the same tau). The transfer adds almost nothing to the error against
    the exact vortex: the four-point interpolation's bound at the new nodes (a quarter cell off the old ones:
    |(s + 1) s (s - 1) (s - 2)| / 4! = 0.41 / 24 at s = 1/4) times h^4 |d^4 u| = (k h)^4 a per axis, two axes, is
    5.1e-5 of the amplitude a; measured 7.5e-5 on top of the coarse grid's 3.7e-3 (the stress settling to the new grid
    adds the rest); asserted below 2e-4, four times the derived scale (review LB1-physics P12: a measured margin around a
    derived scale). The decay after it is the fine grid's: its rate's error equals the fine run's (measured 1.0e-3, the
    coarse grid's 3.9e-3: the scheme's second order, a ratio of 4); asserted within 1.2 times the fine run's (the
    transferred coarse error decaying inside the 400 steps) and below half the coarse run's (a factor 2 inside the
    second order's 4); the balances close. Negative control: the coarse populations copied onto the fine grid as
    they are (lattice velocities read in the new units: c' = 2 c) are off by the whole amplitude."""
    c, nu, k, u0 = _tg_flow(32, 1.0, 1.0)
    f, *_ = _tg_flow(64, 0.5, 0.25)
    r, *_ = _tg_flow(32, 1.0, 1.0)
    c.advance(301)
    f.advance(4 * 301)
    r.advance(300)
    rep = r.remap(dx=0.5, dt=0.25)  # the remap is one step of the coarse grid
    assert rep["factors"]["neq_plus"] == pytest.approx(0.25) and r.t == pytest.approx(c.t, rel=1e-12)
    assert _tg_err(r, nu, k, u0) - _tg_err(c, nu, k, u0) < 2e-4
    exact = 2 * nu * k * k
    rc, rf, rr = (abs(_tg_rate(x, k, n) / exact - 1) for x, n in ((c, 100), (f, 400), (r, 400)))
    assert rr < 1.2 * rf and rr < 0.5 * rc, (rc, rf, rr)
    b = r.balance()
    assert abs(b["mass"]["relative_residual"]) < 1e-13 and abs(b["momentum"]["relative_residual"]) < 1e-13
    n, *_ = _tg_flow(32, 1.0, 1.0)
    n.advance(300)
    naive, *_ = _tg_flow(64, 0.5, 0.25)
    naive._f = np.ascontiguousarray(np.repeat(np.repeat(n.populations(), 2, axis=1), 2, axis=2))
    naive.t = n.t
    naive.advance(400)
    assert _tg_err(naive, nu, k, u0) > 0.5


def _dye_blob(dx, dt):
    """A Gaussian of dye (S0 = 2.5) at rest in the periodic box 32^2 (lattice units of the coarse grid), D = 0.02."""
    fl = lbm.Flow2D((32.0, 32.0), dx, nu=0.1, rho=1.0, dt=dt, sides=PER, device="cpu", dye=0.02)
    X, Y = fl._X - 16.0, fl._Y - 16.0
    fl._g = np.ascontiguousarray(np.array(lbm.WG)[:, None, None] * np.exp(-(X * X + Y * Y) / 12.5)[None])
    return fl


def _dye_offset(fl):
    """The dye's variance along x about the centre minus Fick's S0^2 + 2 D t."""
    C = fl.dye()
    X = fl._X - 16.0
    return float(np.sum(C * X * X) / np.sum(C)) - (6.25 + 2 * 0.02 * fl.t)


def test_the_dye_is_carried_through_a_refinement_by_its_second_moment(monkeypatch):
    """Review LB1-physics P12 (the reviewer's lbm_dye_check3): Fick's law makes the variance of a diffusing blob grow by
    exactly 2 D t, so a transfer that mis-scales the dye's flux shifts it by a constant that diffusion never removes.
    A refinement (dx 1 -> 0.5, dt 1 -> 0.25) at t = 101 keeps the coarse history's offset from S0^2 + 2 D t: over the
    next 50 time units it moves by no more than either grid alone moves it (measured: -3.6e-4 after the transfer, -4.5e-4
    coarse alone, -2.6e-4 fine alone; asserted below 2e-3). Negative control: the non-equilibrium parts carried over
    without their rescaling (``REMAP_NEQ_RESCALE`` off) shift it at once by -0.041 (asserted beyond 2e-2)."""
    for rescale in (True, False):
        monkeypatch.setattr(lbm, "REMAP_NEQ_RESCALE", rescale)
        fl = _dye_blob(1.0, 1.0)
        fl.advance(100)
        fl.remap(dx=0.5, dt=0.25)
        o0 = _dye_offset(fl)
        fl.advance(200)
        d = _dye_offset(fl) - o0
        if rescale:
            assert abs(d) < 2e-3, d
        else:
            assert abs(d) > 2e-2, d
    monkeypatch.setattr(lbm, "REMAP_NEQ_RESCALE", True)
    co = _dye_blob(1.0, 1.0)
    co.advance(101)
    o0 = _dye_offset(co)
    co.advance(50)
    assert abs(_dye_offset(co) - o0) < 2e-3


@pytest.mark.parametrize("dye", [1e-3, None], ids=["dye", "no-dye"])
def test_the_remap_memory_estimate_bounds_the_measured_peak(dye):
    """Review LB1-physics P12: ``remap_memory_estimate`` against the peak of the NumPy buffers a remap holds
    (tracemalloc), for a refinement, a coarsening and a new time step at the same nodes: the peak lies within 0.3 and
    1 of the estimate (measured 0.58-0.68 with the per-node coefficients of the docstring; the former ones fell short
    of a coarsening: 1.08 and 1.15)."""
    import tracemalloc

    for n0, n1 in (((200, 40), (400, 80)), ((400, 80), (200, 40)), ((200, 40), (200, 40))):
        fl = lbm.Flow2D(size=(1.0, 0.2), dx=1.0 / n0[0], nu=1e-3, rho=1.0, u_max=0.2, dye=dye, device="cpu",
                        sides={"left": lbm.Inlet(0.1, "parabolic"), "right": lbm.Outlet()})
        fl.add_obstacle(lbm.Disk((0.3, 0.1), 0.03), interpolated=True)
        if dye:
            fl.add_dye_source(lbm.Disk((0.1, 0.1), 0.01), 1.0)
        fl.advance(20)
        est = fl.remap_memory_estimate(*n1)
        tracemalloc.start()
        try:
            base = tracemalloc.get_traced_memory()[0]
            fl.remap(dx=1.0 / n1[0], u_max=0.25 if n1 == n0 else None)
            peak = tracemalloc.get_traced_memory()[1] - base
        finally:
            tracemalloc.stop()
        assert 0.3 * est < peak <= est, (n0, n1, peak, est)


def test_adopt_continues_another_flow_bit_for_bit():
    """``Flow2D.adopt`` (review LB1-framework F5: a new world that keeps the flow). Two identical channels (a ramping
    parabolic inlet, an outlet, a disk, a dye source): the second, built anew at the first's time, adopts the first's
    fluid after 700 steps and then follows it bit for bit for 300 more steps (populations and dye; the inlet's ramp,
    half done, continues where it was); its balance starts at the adopted state. A different grid or time step is
    refused (``remap`` first); a body only in the adopting flow: its nodes take the rest weights, nodes solid only in
    the other start at rest; the dye zero when only the adopting flow carries it, dropped in the other case."""
    def chan(t0=0.0, dye=1e-3, disk=True):
        fl = lbm.Flow2D(size=(0.6, 0.12), dx=0.005, nu=1e-3, rho=1.0, u_max=0.3, dye=dye, device="cpu", t0=t0,
                        sides={"left": lbm.Inlet(velocity=0.2, profile="parabolic", ramp=1.5), "right": lbm.Outlet()})
        if disk:
            fl.add_obstacle(lbm.Disk((0.15, 0.06), 0.02), interpolated=True)
        if dye:
            fl.add_dye_source(lbm.Disk((0.05, 0.06), 0.01), 1.0)
        return fl
    a = chan()
    a.advance(700)
    assert 0.0 < a.inlet_scales()["left"] < 1.0
    b = chan(t0=a.t)
    rep = b.adopt(a)
    assert rep["copied"] == int((~a.solid()).sum()) and rep["rest"] == 0 and rep["dye"] == "copied"
    assert rep["ramps"] == ["left"] and b.inlet_scales()["left"] == a.inlet_scales()["left"]
    assert np.array_equal(b.populations(), a.populations())
    assert abs(b.balance()["mass"]["relative_residual"]) == 0.0
    a.advance(300)
    b.advance(300)
    assert np.array_equal(b.populations(), a.populations()) and np.array_equal(b.dye(), a.dye(), equal_nan=True)
    assert b.t == pytest.approx(a.t, rel=1e-12) and all(c["ok"] for c in b.checks().values())
    with pytest.raises(ValueError):
        lbm.Flow2D(size=(0.6, 0.12), dx=0.004, nu=1e-3, rho=1.0, u_max=0.3, device="cpu").adopt(a)
    with pytest.raises(ValueError):
        lbm.Flow2D(size=(0.6, 0.12), dx=0.005, nu=1e-3, rho=1.0, u_max=0.6, device="cpu").adopt(a)
    plain = chan(dye=None, disk=False)
    plain.advance(200)
    c = chan(t0=plain.t)  # a disk and dye that the adopted flow has not
    rep = c.adopt(plain)
    assert rep["dye"] == "zero" and rep["rest"] == 0 and np.nansum(c.dye()) == 0.0
    f = c.populations()
    assert np.all(f[:, c.solid()] == np.array(lbm.W)[:, None])
    d = chan(t0=a.t, dye=None, disk=False)  # the disk of ``a`` is fluid here: those nodes start at rest
    rep = d.adopt(a)
    assert rep["dye"] == "dropped" and rep["rest"] == int(a.solid().sum())
    ux, uy = d.velocity()
    assert np.max(np.abs(ux[a.solid()])) <= 1e-12 + abs(0.5 * d._F[0])


def test_a_new_time_step_at_the_same_nodes():
    """The largest expected speed changed (the time step through the lattice Mach number): the fields are carried node
    by node (no interpolation), the non-equilibrium part rescaled; the Taylor-Green decay continues at the scheme's
    accuracy (the error at the end within that of the runs with either time step alone, x 1.5), and the time step is the
    one a new flow with this u_max gets (``Units.from_flow``)."""
    L, N, u0 = 0.032, 32, 0.02
    nu = 4e-6
    k = 2 * math.pi / L

    def flow(u_max):
        fl = lbm.Flow2D((L, L), L / N, nu=nu, rho=1000.0, u_max=u_max, sides=PER, device="cpu")
        fl.set_flow(velocity=lambda X, Y: (-u0 * np.cos(k * X) * np.sin(k * Y), u0 * np.sin(k * X) * np.cos(k * Y)),
                    pressure=lambda X, Y: -0.25 * 1000.0 * u0**2 * (np.cos(2 * k * X) + np.cos(2 * k * Y)))
        return fl

    def err(fl):
        a = u0 * math.exp(-2 * nu * k * k * fl.t)
        return float(np.max(np.abs(fl.velocity()[0] + a * np.cos(k * fl._X) * np.sin(k * fl._Y))) / a)
    T = 0.25 / (2 * nu * k * k)
    a, b, r = flow(0.03), flow(0.06), flow(0.03)
    for x in (a, b):
        x.advance_to(T)
    r.advance_to(T / 2)
    rep = r.remap(u_max=0.06)
    assert r.units.dt == lbm.Units.from_flow(L / N, nu, 0.06, 0.1, 1000.0, 1.0).dt and r.u_max == 0.06
    assert rep["before"]["nodes"] == rep["after"]["nodes"] == [N, N]
    r.advance_to(T)
    assert err(r) < 1.5 * max(err(a), err(b)), (err(a), err(b), err(r))
    assert abs(r.balance()["mass"]["relative_residual"]) < 1e-13


def _channel(dye=1e-3):
    fl = lbm.Flow2D(size=(0.6, 0.12), dx=0.005, nu=1e-3, rho=1.0, u_max=0.3, dye=dye, device="cpu",
                    sides={"left": lbm.Inlet(velocity=0.2, profile="parabolic", ramp=0.2), "right": lbm.Outlet()})
    fl.add_obstacle(lbm.Disk((0.15, 0.06), 0.02), interpolated=True, label="disk")
    if dye:
        fl.add_dye_source(lbm.Disk((0.05, 0.06), 0.006), label="dye")
    fl.record_forces(11)
    fl.advance(400)
    return fl


def test_a_domain_grown_and_cropped_keeps_the_flow_and_its_books(ru):
    """Grown on the right by 0.1 m at the same spacing: the fluid of the present domain is its own (the nodes are the old
    ones: weights 0 and 1), so away from the old outlet the flow equals the same flow advanced one step on the old grid
    (to round-off of the decomposition); the new part moves with the inflow; the obstacle and the source keep their
    places; the balances close. Grown on the left: the coordinates of everything move by the shift. A crop through the
    body is refused and leaves the flow as it was (populations, time, books); a crop of the grown part back is
    accepted."""
    a, twin = _channel(), _channel()
    twin.advance(1)
    r = a.remap(size=(0.7, 0.12), fill="inflow")
    assert r["after"]["nodes"] == [140, 24] and r["fill"] == "inflow" and a.t == pytest.approx(twin.t)
    ua, ut = a.velocity()[0][:110], twin.velocity()[0][:110]
    assert np.nanmax(np.abs(ua - ut)) < 1e-12
    assert np.allclose(a.dye()[:110], twin.dye()[:110], atol=1e-13, equal_nan=True)
    new = a.velocity()[0][125:]
    inflow = 4 * 0.2 * a.y * (0.12 - a.y) / 0.12**2
    assert np.max(np.abs(new - inflow[None, :])) < 0.05 * 0.2  # the inflow's parabola, one step old
    assert a.obstacles()[0]["center"] == [0.15, 0.06]
    for key in ("mass", "momentum", "dye"):
        assert abs(a.balance()[key]["relative_residual"]) < 1e-13
    a.advance(200)
    for key in ("mass", "momentum", "dye"):
        assert abs(a.balance()[key]["relative_residual"]) < 1e-12
    # a crop through the body: refused, nothing changed
    f0, t0, s0, books = a.populations(), a.t, a.steps, a.balance()["lattice"]["books"]
    with pytest.raises(ValueError, match="would be cut by the edge") as e:
        a.remap(size=(0.16, 0.12))
    assert str(e.value).startswith("body “disk” would be cut")
    assert ru(e.value.args[0]).startswith("тело «disk»: его срезал бы край новой области")
    assert np.array_equal(a.populations(), f0) and (a.t, a.steps) == (t0, s0)
    assert a.balance()["lattice"]["books"] == books
    a.remap(size=(0.6, 0.12))
    assert a.nx == 120
    # grown on the left: everything moves with the fluid
    a.remap(size=(0.7, 0.12), shift=(0.1, 0.0))
    assert a.obstacles()[0]["center"] == pytest.approx([0.25, 0.06]) and a.dye_sources()[0]["shape"]["center"] == \
        pytest.approx([0.15, 0.06])
    a.advance(200)
    assert np.isfinite(a.populations()).all()
    for key in ("mass", "momentum", "dye"):
        assert abs(a.balance()[key]["relative_residual"]) < 1e-12


def test_refusals_leave_the_flow_as_it_was(ru):
    """A mask obstacle cannot move to another grid; a grid the scheme cannot run (the grid Reynolds number of a coarse
    grid above the open-domain limit) is refused by the same checks as a new flow — all or nothing."""
    a = _channel(dye=None)
    f0, t0, dt0 = a.populations(), a.t, a.units.dt
    with pytest.raises(ValueError, match="grid Reynolds number") as e:
        a.remap(dx=0.04)
    assert "число Рейнольдса ячейки" in ru(e.value.args[0])
    assert np.array_equal(a.populations(), f0) and a.t == t0 and a.units.dt == dt0 and a.nx == 120
    m = lbm.Flow2D((0.1, 0.05), 0.005, nu=1e-3, rho=1.0, u_max=0.1, device="cpu")
    m.add_obstacle(lbm.Mask(lambda X, Y: (X - 0.05) ** 2 + (Y - 0.025) ** 2 < 0.01**2), label="mask")
    with pytest.raises(ValueError, match="given as a mask of nodes") as e:
        m.remap(dx=0.0025)
    assert str(e.value).endswith("shifted: “mask”") and "заданные маской узлов" in ru(e.value.args[0])
    m.remap(u_max=0.12)  # the same nodes: a mask stays where it is
    assert m.u_max == 0.12


def test_the_state_after_a_remap_round_trips():
    """A remap with a new time step leaves a ramp starting at a fraction of a step; the state's plain data carries it
    and the copy continues bit for bit; the memory estimate of a remap covers more than the new grid alone."""
    a = _channel()
    a.remap(dx=0.004, u_max=0.35)
    assert any(not float(r["s0"]).is_integer() for r in a._ramps.values())
    b = lbm.Flow2D.from_state_dict(a.state_dict(), device="cpu")
    a.advance(50)
    b.advance(50)
    assert np.array_equal(a.populations(), b.populations()) and a.t == b.t
    assert a.remap_memory_estimate(300, 60) > lbm.Flow2D.memory_estimate(300, 60)


@pytest.mark.skipif(not _gpu(), reason="no GPU given to this container")
def test_gpu_equals_cpu_after_a_remap():
    """The remap runs on the host; a flow on GPU 0 moved back afterwards continues bit for bit like the CPU's."""
    backend.configure({"kernels": {"fluids.lbm": {"device": "gpu", "precision": "fp64"}}})
    c = _channel()
    g = lbm.Flow2D.from_state_dict(c.state_dict(), device="auto")
    g.advance(1)
    c.advance(1)
    assert g.device == "gpu" and np.array_equal(c.populations(), g.populations())
    for o in (c, g):
        o.remap(dx=0.004, size=(0.7, 0.12), fill="inflow")
        o.advance(300)
    assert g.device == "gpu"
    assert np.array_equal(c.populations(), g.populations())
    assert np.array_equal(c.dye(), g.dye(), equal_nan=True)
