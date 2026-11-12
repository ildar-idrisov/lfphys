# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p04 after the reviews of 2026-11-04 (UX-ui U4, U7, U8, U12, U13; UX-params P4, P24, P25, P27): water and air from
the defaults give a working world at the speeds the grid resolves (and their own presets at Re = 20); a grid beyond the
memory budget is refused before it is built, with the estimate and what to change; the body force is placeable in
every world; bodies, probes and dye land where they can exist, what lies outside the domain is refused; a probe inside a
body says so; the live laws (viscosity, density, collision operator, dye) at the current moment, with the world rebuilt
by replay of the same commands; the engine's refusals in the world's terms."""

import math
import queue
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core.fluids import lbm as L  # noqa: E402
from lfviz import registry  # noqa: E402
from lfviz.sim import Runner  # noqa: E402
from p04_fluids import viz as P4  # noqa: E402

V = "p04_fluids"
CYR = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ")


def run(h, seconds, n=5):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + seconds * k / n)
        h.runner._frame(0.0)


def russian(text):
    return any(c in CYR for c in text) and "dt" not in text.replace("dt/", "") and "Traceback" not in text


def objs(h, typ):
    return [o for o in h.sim.objects.values() if o["type"] == typ]


@pytest.mark.parametrize("fluid", ["water", "air"])
def test_water_and_air_from_the_defaults_give_a_working_world(fluid):
    """P24: «Жидкость» = вода / воздух with the other defaults was refused (τ − ½ too small, the cell Reynolds number
    149); now u_max is lowered to what the 5 mm grid resolves (u dx / ν = 9) with a notice saying so, the palette's
    inlet speed follows it, and a channel with an inlet, an outlet and a disk runs with every check passing. Control:
    the DFG fluid keeps u_max = 0.45 m/s."""
    h = Harness(V, None, {"fluid": fluid})
    nu = L.FLUIDS["water_20C" if fluid == "water" else "air_20C"]["nu"]
    u = h.sim.u_max
    assert u < 0.45 and u * 0.005 / nu <= 9.0 + 1e-9 and u * 0.005 / nu > 8.0
    assert h.of("header")[-1]["params"]["u_max"] == u
    assert any("понижена" in m["text"] for m in h.of("notice"))
    for t in ("inlet", "outlet", "disk"):
        h.cmd("scene", op="add", type=t, values={})
    assert not h.errors(), h.errors()
    run(h, 2.0 * h.sim.default_speed)
    assert not h.errors(), h.errors()
    assert not [c for c in h.checks().values() if c.get("ok") is False]
    dfg = Harness(V)
    assert dfg.sim.u_max == 0.45 and not dfg.of("notice")


@pytest.mark.parametrize("params", [{"Lx": 1e-6}, {"Ly": 1e4}, {"Lx": 1e-6, "Ly": 1e4, "nx": "1024"}])
def test_a_grid_beyond_the_budget_is_refused_before_it_is_built(params):
    """P25: «Lx» = 10⁻⁶ м made 440 × 1.8·10⁸ nodes (591 GiB); now refused before any allocation, in Russian, with the
    nodes, the memory and what to change (nx, Lx); ``estimate_bytes`` gives the same estimate to the framework."""
    p, errors = SCHEMA_RESOLVE(params)
    with pytest.raises(ValueError) as e:
        P4.Simulation.check_params(p)
    text = str(e.value)
    assert russian(text) and "узлов" in text and ("ГБ" in text or "ТБ" in text) and "Длина области по x" in text
    b = P4.Simulation.estimate_bytes(p)
    nx, ny, _ = P4._grid(p)
    assert b[0] == L.Flow2D.memory_estimate(nx, ny, True)
    with pytest.raises(ValueError):
        P4.Simulation(p, 1, lambda *a: None)


def SCHEMA_RESOLVE(values):
    p, errors = P4.SCHEMA.resolve(None, values)
    return p, errors


def test_a_large_grid_that_fits_keeps_frames_short():
    """P25: a grid that fits but is slow (4·10⁶ nodes) stalled one frame for minutes (400 steps per advance call); the
    advance is cut to the steps the CPU makes in FRAME_S (here one)."""
    p, _ = SCHEMA_RESOLVE({"nx": "768", "Ly": 15.0})
    nx, ny, dx = P4._grid(p)
    per = L._interp_rate("cpu", nx * ny)
    k = int(min(P4.MAX_STEPS, max(1, P4.FRAME_S / per)))
    assert k == 1 and per > 0.1


def test_the_body_force_is_placeable_in_every_world_and_an_explicit_large_one_is_refused():
    """U7: «Объёмная сила» with its defaults (−9.81 m/s²) was refused in every world; now its default is what the scheme
    carries (here less than 9.81), it is placed (with a note when reduced), and an explicit −9.81 is refused in Russian
    with the u_max that would carry it — which, as a new world, does."""
    for preset in (None, "cylinder_re20", "cavity", "channel"):
        h = Harness(V, preset)
        h.cmd("scene", op="add", type="gravity", values={})
        assert not h.errors(), (preset, h.errors())
        g = objs(h, "gravity")[0]
        assert 0 < -g["values"]["gy"] <= 9.81
    h = Harness(V)
    g = objs(h, "gravity") or None
    h.cmd("scene", op="add", type="gravity", values={})
    gid = objs(h, "gravity")[0]["id"]
    h.cmd("scene", op="set", id=gid, values={"gy": -9.81})
    err = h.errors()[-1]
    assert russian(err) and "Наибольшая ожидаемая скорость" in err
    u_need = float(err.split("не меньше ")[-1].split()[0].replace(",", ".").replace("·10^", "e"))
    h2 = Harness(V, None, {"u_max": u_need})
    h2.cmd("scene", op="add", type="gravity", values={"gy": -9.81})
    assert not h2.errors(), h2.errors()
    assert objs(h2, "gravity")[0]["values"]["gy"] == -9.81


def test_side_objects_take_a_free_side_and_none_is_left():
    """U4: inlet, outlet and periodicity with their defaults were refused when their side was taken; now they take a free
    one (or the free pair), and with all four sides taken the palette says why."""
    h = Harness(V, "cylinder_re20")
    h.cmd("scene", op="add", type="inlet", values={})
    h.cmd("scene", op="add", type="lid", values={})
    assert not h.errors(), h.errors()
    sides = {s: h.sim.side_owner.get(s) for s in L.SIDES}
    assert all(v is not None for v in sides.values())
    st = h.sim.palette_state()
    assert "inlet" in st and "periodic" in st and russian(st["inlet"])
    h.cmd("scene", op="add", type="outlet", values={})
    assert russian(h.errors()[-1]) and "заняты" in h.errors()[-1]


def test_bodies_land_free_and_outside_is_refused():
    """U4 / U8: a second disk with the defaults and a copy land where they cover no other body; a disk moved 10 km away is
    refused (it was accepted and nothing appeared), a palette disk asked there is brought inside; a probe outside is
    refused; a body covering the domain is refused."""
    h = Harness(V)
    h.cmd("scene", op="add", type="disk", values={})
    h.cmd("scene", op="add", type="disk", values={})
    d = objs(h, "disk")
    h.cmd("scene", op="duplicate", id=d[0]["id"])
    assert not h.errors(), h.errors()
    masks = [h.sim.fl.shape_mask(h.sim._shape(o)) for o in objs(h, "disk")]
    assert len(masks) == 3 and not (masks[0] & masks[1]).any() and not (masks[0] & masks[2]).any()
    h.cmd("scene", op="set", id=d[0]["id"], values={"x": 1e4})
    assert "вне области" in h.errors()[-1] and russian(h.errors()[-1])
    h.cmd("scene", op="add", type="disk", values={"x": 1e4, "y": 1e4})
    far = objs(h, "disk")[-1]["values"]
    assert 0 <= far["x"] <= h.sim.size[0] and 0 <= far["y"] <= h.sim.size[1]
    h.cmd("scene", op="add", type="probe", values={})
    pid = objs(h, "probe")[0]["id"]
    h.cmd("scene", op="set", id=pid, values={"y": -5.0})
    assert "вне области" in h.errors()[-1]
    h.cmd("scene", op="set", id=d[0]["id"], values={"radius": 50.0})
    assert "закрыло бы" in h.errors()[-1]


def test_a_probe_inside_a_body_says_so():
    """P27: a probe inside a body read NaN without a word; now it says it is inside the body; a palette probe asked
    inside a body lands in the fluid next to it."""
    h = Harness(V, "cylinder_re20")
    h.cmd("scene", op="add", type="probe", values={"x": 0.6, "y": 0.2})
    pid = objs(h, "probe")[0]["id"]
    h.cmd("scene", op="set", id=pid, values={"x": 0.2, "y": 0.2})     # the cylinder's centre
    run(h, 0.05, 1)
    r = h.of("frame")[-1]["probes"][pid]
    assert "внутри тела" in r["где"] and "Цилиндр" in r["где"]
    h.cmd("scene", op="add", type="probe", values={"x": 0.2, "y": 0.2})
    p2 = objs(h, "probe")[-1]["values"]
    i, j = h.sim._at(p2["x"], p2["y"])
    assert not h.sim.fl.solid()[i, j]


def test_live_viscosity_density_collision_and_dye():
    """U12: ν doubled, ρ ×1000, BGK, the dye off and on at the current moment: the engine's values follow, the flow goes
    on with every check passing; pressures scale with ρ; the dye cannot go while a dye source is in the scene; a
    viscosity the grid cannot carry is refused in Russian with the smallest one; the header's laws are the world's
    start, the live values the ones in force."""
    h = Harness(V, "cylinder_re20")
    run(h, 0.5)
    p0 = np.nanmax(np.abs(h.sim.fl.fields()["p"]))
    h.set(nu=2e-3)
    assert h.sim.fl.nu == 2e-3 and not h.errors()
    h.set(rho=1000.0)
    assert np.nanmax(np.abs(h.sim.fl.fields()["p"])) == pytest.approx(1000.0 * p0, rel=1e-9)
    h.set(collision="bgk")
    assert h.sim.fl.collision == "bgk" and h.sim.fl.tau_m == h.sim.fl.tau_p
    h.set(dye="off")
    assert russian(h.errors()[-1]) and "Краситель" in h.errors()[-1] and h.sim.fl.dye_D is not None
    dye = objs(h, "dye_source")[0]["id"]
    h.cmd("scene", op="remove", id=dye)
    h.set(dye="off")
    assert h.sim.fl.dye_D is None and h.sim.D is None and "dye_source" in h.sim.palette_state()
    run(h, 0.3)
    h.set(dye="on")
    assert h.sim.fl.dye_D == pytest.approx(2e-3)       # «0 — как вязкость»: the viscosity in force
    run(h, 0.3)
    n = len(h.errors())
    h.set(nu=1e-9)
    assert len(h.errors()) == n + 1 and russian(h.errors()[-1]) and "ν не меньше" in h.errors()[-1]
    assert h.sim.fl.nu == 2e-3
    assert not [c for c in h.checks().values() if c.get("ok") is False], h.checks()
    assert h.of("live")[-1]["values"]["nu"] == 2e-3


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


def test_live_laws_and_placements_are_replayed_by_a_restore():
    params = dict(registry.load(V)["schema"].presets["cavity"]["params"], nx="128")
    sim, run_, frames, script = _world(params)
    run_._start_world()
    run_._advance(0.3)
    run_._frame(0.0)
    run_.handle({"cmd": "set", "args": {"values": {"nu": 0.02, "collision": "bgk"}}})
    run_.handle({"cmd": "scene", "args": {"op": "add", "type": "disk", "values": {}}})
    run_.handle({"cmd": "scene", "args": {"op": "add", "type": "gravity", "values": {}}})
    run_._advance(0.6)
    run_._frame(0.0)
    sim2, run2, frames2, _ = _world(params)
    run2.restore(1, list(script)[:-1], sim.t, lambda on: None)
    run2._frame(0.0)
    assert np.array_equal(sim.fl.populations(), sim2.fl.populations())
    assert sim2.live == sim.live and frames[-1][0]["probes"] == frames2[-1][0]["probes"]


def test_engine_refusals_speak_the_worlds_terms():
    """U13 / P24: «… уменьшите dt (или скорость)» named a step the owner cannot set; now the speed limit of this world
    and «Наибольшая ожидаемая скорость»."""
    h = Harness(V, "cylinder_re20")
    inlet = objs(h, "inlet")[0]["id"]
    h.cmd("scene", op="set", id=inlet, values={"speed": 100.0})
    err = h.errors()[-1]
    assert russian(err) and "м/с" in err and "dt" not in err
