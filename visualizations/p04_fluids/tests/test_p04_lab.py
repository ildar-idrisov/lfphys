# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p04 as a bench that never restarts (plan P16.1–P16.3, batch LB1): the grid (nx), the domain (Lx, Ly) and the largest
expected speed (u_max) changed at the current moment, the flow continued on the new grid or time step
(``Flow2D.remap``) with its balances closed and the event stating the mass and momentum before and after; a domain grown
on either side (the objects move with the fluid), cropped back, a crop through a body or past a probe refused with the
world as it was; a grid beyond the budget refused before anything is allocated; the live grid repeated by a replay of
the record bit for bit. Handles: every positioned object's place in each frame (``at``), a body dragged (a scene edit of
its position alone) cheaply. Measurables: the list with labels (translated) and units, the frame's values for each of them,
the averaged coefficients undefined with the reason while their window fills, the measure() the sweeps read."""

import math
import queue
import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.i18n import english, is_t, render  # noqa: E402
from lfviz import registry  # noqa: E402
from lfviz.i18n import catalogue  # noqa: E402
from lfviz.sim import Runner  # noqa: E402

V = "p04_fluids"
CYR = {chr(c) for c in range(0x0410, 0x0450)} | {"\u0401", "\u0451"}  # the Russian alphabet


def en(x):
    """The English rendering of a text (a T, a T as the player gets it, or a plain string)."""
    return english(x) if isinstance(x, dict) else str(x)


def ru(x):
    """The Russian rendering of a text from the merged catalogues (what the player shows in Russian)."""
    return render(x, catalogue("ru"), "ru")


def run(h, seconds, n=5):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + seconds * k / n)
        h.runner._frame(0.0)


def objs(h, typ):
    return [o for o in h.sim.objects.values() if o["type"] == typ]


def failed(h):
    return [c for c in h.checks().values() if c.get("ok") is False]


def bench():
    """The DFG 2D-1 channel with a probe behind the cylinder (x = 1.1 m)."""
    h = Harness(V, "cylinder_re20")
    h.cmd("scene", op="add", type="probe", values={"x": 1.1, "y": 0.2})
    assert not h.errors(), h.errors()
    return h


def test_the_grid_changed_live_continues_the_flow():
    """nx 440 -> 880 (dx halved) and back, then u_max 0.3 -> 0.45 (the time step from the Mach number): the world goes
    on (no new world), the engine's grid and time step follow, every running check passes, the drag stays near the
    coarse grid's (the cylinder's C_x over the last step within 5 % after the refinement: the transfer does not ring the
    body); the event states the grids, the mass and momentum before and after and what the transfer changed."""
    h = Harness(V, "cylinder_re20")
    run(h, 1.0)
    fl = h.sim.fl
    disk = objs(h, "disk")[0]["id"]
    cd0 = h.sim._force(disk, h.sim.ref[disk][1])["cd"]
    worlds = len(h.of("header"))
    t0 = time.perf_counter()
    h.set(nx=880)
    lat = time.perf_counter() - t0
    assert not h.errors(), h.errors()
    assert (fl.nx, fl.ny) == (880, 164) and h.sim.live["nx"] == 880 and len(h.of("header")) == worlds
    ev = h.of("event")[-1]["text"]
    assert "440 × 82 → 880 × 164" in en(ev) and "mass" in en(ev) and "momentum" in en(ev) and "transfer" in en(ev)
    cd1 = h.sim._force(disk, h.sim.ref[disk][1])["cd"]
    assert abs(cd1 / cd0 - 1) < 0.05, (cd0, cd1)
    assert lat < 5.0, lat
    run(h, 0.3)
    h.set(nx=440)
    run(h, 0.3)
    dt0 = fl.units.dt
    h.set(u_max=0.45)
    assert fl.units.dt == pytest.approx(dt0 * 0.3 / 0.45, rel=1e-12) and h.sim.u_max == 0.45
    run(h, 0.5)
    assert not h.errors(), h.errors()
    assert not failed(h), failed(h)
    assert h.of("live")[-1]["values"]["nx"] == 440 and h.of("live")[-1]["values"]["u_max"] == 0.45


def test_the_domain_grows_and_shrinks_on_the_side_chosen():
    """Lx 2.2 -> 2.7 m on the right with the inflow: the cylinder keeps its coordinates, the grid its spacing (540
    nodes); back to 2.2; on the left: everything moves by +0.5 m with the fluid (the scene says so); a crop through the
    cylinder is refused (the world as it was); a probe that would fall outside is refused by name; Ly shrunk from the
    top to just above the cylinder is accepted. The checks pass throughout."""
    h = bench()
    run(h, 0.3)
    fl = h.sim.fl
    cyl = objs(h, "disk")[0]
    h.set(Lx=2.7, fill="inflow")
    assert not h.errors(), h.errors()
    assert fl.nx == 540 and fl.units.dx == pytest.approx(0.005) and cyl["values"]["x"] == 0.2
    assert "with the inflow" in en(h.of("event")[-1]["text"])
    run(h, 0.2)
    h.set(Lx=2.2)
    assert fl.nx == 440 and not h.errors()
    h.set(anchor="left_bottom", Lx=2.7)
    assert not h.errors(), h.errors()
    assert cyl["values"]["x"] == pytest.approx(0.7) and fl.obstacles()[0]["center"][0] == pytest.approx(0.7)
    assert h.of("scene")[-1]["objects"][[o["id"] for o in h.of("scene")[-1]["objects"]].index(cyl["id"])][
        "values"]["x"] == pytest.approx(0.7)
    run(h, 0.2)
    h.set(Lx=2.1)  # from the left: the dye source (x = 0.58) would leave the domain: refused by its name
    assert "“Dye” would be outside the new domain" in en(h.errors()[-1])
    h.cmd("scene", op="remove", id=objs(h, "dye_source")[0]["id"])
    f0, t0, n0 = fl.populations(), fl.t, len(h.errors())
    h.set(Lx=2.0)  # from the left: would cut the cylinder at x = 0.7 - 0.7 = 0
    assert len(h.errors()) == n0 + 1 and "would be cut by the edge" in en(h.errors()[-1])
    assert np.array_equal(fl.populations(), f0) and fl.t == t0 and h.sim.live["Lx"] == pytest.approx(2.7)
    h.set(anchor="right_top", Lx=0.9)  # from the right: the probe at x = 1.1 would be outside
    assert "probe" in en(h.errors()[-1]) and "outside the new domain" in en(h.errors()[-1]) and fl.nx == 540
    h.set(Ly=0.3)
    assert not h.errors()[n0 + 2:], h.errors()
    assert fl.ny == 60
    run(h, 0.2)
    assert not failed(h), failed(h)


def _force_channel():
    """A p04 world of the body-force Poiseuille channel: periodic along x, plain walls at the bottom and the top, g_x =
    1 m/s², 16 x 16 nodes over 16 mm, ν = 10⁻³ m²/s (peak 0.032 m/s); steady after 1.2 s (the slowest mode decays as
    exp(−π²νt/H²): e⁻⁴⁶)."""
    scene = {"format": "lfscene", "version": 1, "objects": [
        {"type": "periodic", "label": "Periodic along x", "values": {"axis": "x"}},
        {"type": "gravity", "label": "Force along the channel", "values": {"gx": 1.0, "gy": 0.0}}]}
    h = Harness(V, None, {"fluid": "custom", "rho": 1.0, "nu": 1e-3, "Lx": 0.016, "Ly": 0.016, "nx": 16,
                          "u_max": 0.05, "dye": "off", "scene": scene})
    assert not h.errors(), h.errors()
    run(h, 1.2, n=3)
    return h


def _pois(h):
    h.sim.checks()
    return h.checks()["pois_force"]["value"]


def test_a_wrong_transfer_is_seen_by_the_reference_not_by_the_balances(monkeypatch):
    """Review LB1-physics P7. The balances close by construction across a remap (its change is booked as "transfer"), so
    they cannot see an error of the transfer; the event says so, and the world's "Benchmarks" hold a flow a wrong transfer
    breaks: the body-force Poiseuille channel (the profile averaged along x against g_x y (H − y)/(2ν)). nx 16 → 32 and
    a new u_max: the profile stays on the parabola to round-off (measured ≤ 1e-12 of the peak; asserted 1e-9) and every
    running check passes. Negative control: the transferred velocity 1 % too large (the reviewer's mutation) — the
    momentum balance still passes (as documented), the reference is off by ~1e-2."""
    h = _force_channel()
    assert _pois(h) < 1e-9
    h.set(nx=32)
    assert not h.errors(), h.errors()
    ev = h.of("event")[-1]["text"]
    assert "the balance checks close by construction" in en(ev) and "Benchmarks" in en(ev)
    assert _pois(h) < 1e-9
    run(h, 0.2, n=2)
    h.set(u_max=0.08)
    run(h, 0.2, n=2)
    assert _pois(h) < 1e-9 and not failed(h), (_pois(h), failed(h))
    import lfphys.core.fluids.lbm as LB
    orig = LB.Flow2D._remap_fields

    def wrong(self, *a, **k):
        R, near = orig(self, *a, **k)
        R["u"] = R["u"].copy()
        R["u"][0] *= 1.01
        return R, near
    monkeypatch.setattr(LB.Flow2D, "_remap_fields", wrong)
    w = _force_channel()
    w.set(nx=32)
    assert not w.errors(), w.errors()
    w.sim.checks()
    assert w.checks()["momentum"]["ok"] is True  # blind, by construction
    assert _pois(w) > 3e-3, _pois(w)


def test_a_new_nx_states_the_new_height_and_the_scheme_compressibility():
    """Review LB1-physics P14: nx 440 → 333 on the DFG channel 2.2 × 0.41 m: dx = 6.607 mm fits 62 cells into the height,
    0.40961 m; the event says so, names the nx that keep both lengths (440, 220: 0.41/2.2 = 41/220), and that the DFG set-up is no
    longer recognised. Review LB1-p02-ux X14: u_max 0.3 → 0.12 at the same nodes keeps the pressure, so the scheme's
    density p/c_s² (its lattice mass) changes with its sound speed: the event attributes the transfer's mass change to
    the scheme's compressibility (computed from the pressure integral: equal to the booked change to 1 %) and states the
    incompressible fluid's mass ρ·S."""
    h = Harness(V, "cylinder_re20")
    run(h, 0.5)
    h.set(nx=333)
    assert not h.errors(), h.errors()
    ev = h.of("event")[-1]["text"]
    assert h.sim.fl.ny == 62 and "domain height 0.41 → 0.40961 m" in en(ev) and "nx = 440, 220" in en(ev), en(ev)
    assert "DFG set-up is no longer recognised" in en(ev)
    h.set(nx=440)
    run(h, 0.3)
    fl = h.sim.fl
    b0 = fl.balance()["mass"]
    Ip = float(np.nansum(fl.fields()["p"])) * fl.units.dx ** 2
    cs0 = fl.units.c * 3 ** -0.5
    h.set(u_max=0.12)
    assert not h.errors(), h.errors()
    ev = h.of("event")[-1]["text"]
    assert "the compressibility of the scheme, not of the fluid" in en(ev) and "ρ·S" in en(ev), en(ev)
    moved = fl.balance()["mass"]["booked"]["remap"] - b0["booked"]["remap"]
    predicted = Ip * (1 / (fl.units.c * 3 ** -0.5) ** 2 - 1 / cs0 ** 2)
    assert abs(moved) > 1e-3 * b0["now"]  # the scheme's mass did change visibly (~16× its former density deviation)
    assert moved == pytest.approx(predicted, rel=1e-2), (moved, predicted)


def test_a_grid_beyond_the_budget_is_refused_before_anything_is_allocated(monkeypatch):
    """nx = 8192 on the default 2.2 x 0.41 m domain: 8192 x 1527 nodes, about 12 GB: refused with the
    memory (in Russian too), the flow as it was."""
    monkeypatch.setattr("p04_fluids.viz._budget", lambda: 2 * 2 ** 30)
    h = Harness(V, "cylinder_re20")
    f0 = h.sim.fl.populations()
    h.set(nx=8192)
    err = h.errors()[-1]
    assert "memory" in en(err) and "limit" in en(err) and any(c in CYR for c in ru(err))
    assert np.array_equal(h.sim.fl.populations(), f0) and h.sim.live["nx"] == 440


def _world(params):
    viz = registry.load(V)
    p, errors = viz["schema"].resolve(None, params)
    assert not errors
    frames, script = [], []

    def emit(meta, blobs=None):
        if meta.get("type") == "frame":
            frames.append((meta, blobs))
            script.append({"frame": meta["t"]})
        elif meta.get("type") == "command":
            script.append({"t": meta["t"], "cmd": meta["cmd"], "args": meta["args"]})
    sim = viz["simulation"](p, 7, emit)
    return sim, Runner(sim, emit, queue.Queue()), frames, script


def test_the_live_grid_is_repeated_by_a_replay_bit_for_bit():
    """A world refined, grown on the left and given a new u_max, rebuilt by replaying its record: the same
    populations, the same scene, the same live values."""
    params = dict(registry.load(V)["schema"].presets["channel"]["params"], nx=256)
    sim, run_, frames, script = _world(params)
    run_._start_world()
    run_._advance(0.2)
    run_._frame(0.0)
    run_.handle({"cmd": "set", "args": {"values": {"nx": 320}}})
    run_._advance(0.3)
    run_._frame(0.0)
    run_.handle({"cmd": "set", "args": {"values": {"anchor": "left_bottom", "Lx": 0.5, "u_max": 0.12}}})
    run_._advance(0.4)
    run_._frame(0.0)
    sim2, run2, frames2, _ = _world(params)
    run2.restore(1, list(script)[:-1], sim.t, lambda on: None)
    run2._frame(0.0)
    assert np.array_equal(sim.fl.populations(), sim2.fl.populations())
    assert sim2.live == sim.live and [o["values"] for o in sim2.objects.values()] == \
        [o["values"] for o in sim.objects.values()]
    ma, mb = frames[-1][0]["meas"], frames2[-1][0]["meas"]
    assert set(ma) == set(mb) and all(ma[k] == mb[k] or (math.isnan(ma[k]) and math.isnan(mb[k])) for k in ma)


def _carry_run(preset="channel", **over):
    """A runner that can make new worlds (``new_world``), on a preset."""
    viz = registry.load(V)
    msgs = []

    def emit(meta, blobs=None):
        msgs.append(meta)

    def make_world(pr, vals, sd):
        p, errs = viz["schema"].resolve(pr, vals or {})
        if errs:
            raise ValueError("; ".join(errs))
        return viz["simulation"](p, 3, emit), {"preset": pr}
    params = dict(viz["schema"].presets[preset]["params"], **over)
    sim, _ = make_world(None, params, 3)
    run_ = Runner(sim, emit, queue.Queue(), make_world=make_world)
    run_._start_world()
    return run_, msgs, params


def _carry_notice(msgs):
    return [m for m in msgs if m.get("type") == "notice" and m.get("carry")][-1]


def test_a_new_world_keeps_the_flow(monkeypatch):
    """Review LB1-framework F5 (p04): "carry the scene" carried the objects and restarted the flow from rest while the
    dialog promised the state. Now the flow goes with the carry-over (``carry_state``: the engine's state; ``carry_world``
    → ``Flow2D.adopt``): a new world of another fluid law with the same grid takes the populations bit for bit (its
    balances start there and pass); a new world with another grid (nx 256 → 192) takes the flow through the engine's
    transfer (the inflow developed, not at rest) and says so; the notice's world entry is "state". Negative control: a
    world that gives no flow (``carry_state`` None) restarts it from rest and says exactly that."""
    run_, msgs, params = _carry_run(nx=256)
    run_._advance(0.4)
    run_._frame(0.0)
    old = run_.sim
    f0, t0 = old.fl.populations(), old.fl.t
    new = dict(params, fluid="custom", rho=1.0, nu=1e-3)
    new.pop("scene")
    run_.handle({"cmd": "new_world", "args": {"params": new, "carry": True}})
    assert run_.sim is not old
    fl = run_.sim.fl
    assert np.array_equal(fl.populations(), f0) and abs(fl.t - t0) <= old.fl.units.dt  # the step nearest the world's t
    n = _carry_notice(msgs)
    assert n["carry"]["world"]["how"] == "state" and "the flow carried over as it was" in en(n["text"]), en(n["text"])
    run_._advance(fl.t + 0.1)
    run_._frame(0.0)
    assert all(c["ok"] for c in fl.checks().values() if "ok" in c), fl.checks()
    umax = float(np.nanmax(fl.speed()))
    run_.handle({"cmd": "new_world", "args": {"params": dict(new, nx=192), "carry": True}})
    fl2 = run_.sim.fl
    assert fl2.nx == 192 and float(np.nanmax(fl2.speed())) > 0.8 * umax
    n = _carry_notice(msgs)
    assert n["carry"]["world"]["how"] == "state" and "by the engine's transfer" in en(n["text"]), en(n["text"])
    monkeypatch.setattr(type(run_.sim), "carry_state", lambda self: None)
    run_.handle({"cmd": "new_world", "args": {"params": new, "carry": True}})
    n = _carry_notice(msgs)
    assert n["carry"]["world"]["how"] == "restarted" and "the flow restarted from rest" in en(n["text"]), en(n["text"])
    assert float(np.nanmax(run_.sim.fl.speed())) == 0.0


def test_handles_positions_and_a_cheap_drag():
    """Every body, dye source and probe is in the frame's ``at`` at its x, y (the plane z = 0); the palette declares the
    handles; a body moved by an edit of its position alone is re-voxelised at once, its old nodes fluid again (the mass
    balance still closes), in well under a frame's budget on this grid."""
    h = bench()
    run(h, 0.2)
    fr = h.of("frame")[-1]
    for o in h.sim.objects.values():
        if o["type"] in ("disk", "probe", "dye_source"):
            assert fr["at"][o["id"]] == [o["values"]["x"], o["values"]["y"], 0.0]
    pal = {p["type"]: p for p in h.of("header")[-1]["playground"]["palette"]}
    if "handles" in pal["disk"]:
        assert pal["disk"]["handles"]["position"] == ["x", "y"] and pal["probe"]["handles"]["position"] == ["x", "y"]
    assert h.sim.PALETTE["disk"].handles["position"] == ["x", "y"]
    cyl = objs(h, "disk")[0]
    t0 = time.perf_counter()
    h.cmd("scene", op="set", id=cyl["id"], values={"x": 0.3, "y": 0.21})
    lat = time.perf_counter() - t0
    assert not h.errors(), h.errors()
    assert h.sim.fl.obstacles()[0]["center"] == [0.3, 0.21] and lat < 1.0, lat
    run(h, 0.1)
    assert h.of("frame")[-1]["at"][cyl["id"]] == [0.3, 0.21, 0.0]
    assert not failed(h), failed(h)


def test_measurables_and_their_values():
    """The list: unique ids, labels translated into Russian, units, each tied to its object or to the world; every frame carries a value
    for every one of them (NaN, with the reason, only for the averaged coefficients while their window fills);
    ``measure()`` gives the same numbers as the frame at the same moment; the probe's velocity and pressure are the
    fields at its node; the inlet's flow rate is the engine's."""
    h = bench()
    ms = h.sim.measurables()
    ids = [m["id"] for m in ms]
    assert len(ids) == len(set(ids))
    for m in ms:
        assert any(c in CYR for c in ru(m["label"])) and (m["unit"] == "" or is_t(m["unit"]))
        assert m["of"] is None or m["of"] in h.sim.objects
    run(h, 0.1, n=1)
    fr = h.of("frame")[-1]
    assert set(fr["meas"]) == set(ids)
    cyl = objs(h, "disk")[0]["id"]
    assert fr["meas"][f"{cyl}.cd_mean"] is None and "window" in en(fr["meas_note"][f"{cyl}.cd_mean"])
    probe = objs(h, "probe")[0]
    f = h.sim.fl.fields()
    i, j = h.sim._at(probe["values"]["x"], probe["values"]["y"])
    assert fr["meas"][f"{probe['id']}.ux"] == f["ux"][i, j] and fr["meas"][f"{probe['id']}.p"] == f["p"][i, j]
    inlet = objs(h, "inlet")[0]["id"]
    assert fr["meas"][f"{inlet}.q"] == pytest.approx(h.sim.fl.flow_rates()["left"])
    m = h.sim.measure()
    assert all((m[k] == fr["meas"][k]) or (fr["meas"][k] is None and math.isnan(m[k])) for k in ids)
    run(h, 3.0, n=3)  # past one sound period: the averaged coefficients are defined
    assert isinstance(h.of("frame")[-1]["meas"][f"{cyl}.cd_mean"], float)
