# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p01 as a bench that never restarts (plan P16.1–P16.3, batch LB1). The Kerr–Newman hole is an object of the scene:
its mass changed at the current moment is a change of units (G = c = M = 1: the bodies' state in units of M kept, the
seconds and metres rescaled, proper times and observers' clocks in seconds continuous: the same evolution as a world that
never changed, read in other seconds); its spin and charge only as a declared «what if» (each body's place, proper time
and ZAMO-measured velocity kept, E, L, K recomputed, the world flagged as a model; refused where a body would be under
the new horizon). The binary's total mass a property of the binary (a change of units: the orbit goes on; the waves'
frequency ∝ 1/m, their strain ∝ m). Handles: positions in every frame (``at``), a Newtonian throw sets the velocity,
a drag keeps it; a Kerr body dragged to a point and thrown (the drawn velocity turned into the ZAMO-measured one and
back). Measurables: Kepler's elements of the Earth, the radial period of a far Kerr orbit against Kepler's, the binary's
phase against its angular velocity. Carry-over across the laws: what makes sense is translated, the rest listed.
A world with all of it is rebuilt by replay bit for bit."""

import math
import queue
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core import constants as K  # noqa: E402
from lfphys.core.gravity import kerr_newman as KN  # noqa: E402
from lfphys.i18n import render as en  # noqa: E402
from lfviz import registry  # noqa: E402
from lfviz.sim import Runner  # noqa: E402
from p01_gravity import viz as P1  # noqa: E402

V = "p01_gravity"


def run(h, seconds, n=4):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + seconds * k / n)
        h.runner._frame(0.0)


def objs(h, typ):
    return [o for o in h.sim.objects.values() if o["type"] == typ]


def failed(h):
    return [c for c in h.checks().values() if c.get("ok") is False]


def test_the_hole_is_an_object_of_its_world():
    """Every Kerr–Newman world has its hole in the scene (a preset without one, an empty world: the last object, so the
    preset's objects keep their ids; its values set on the world before any body), with the world's mass, spin and
    charge; it cannot be removed (a clear keeps it) nor doubled."""
    for preset, params in (("kerr_orbits", None), (None, {"laws": "kerr", "m_hole": 7.0, "spin": 0.5})):
        h = Harness(V, preset, params)
        first = list(h.sim.objects.values())[-1]
        assert first["type"] == "kn_hole" and h.sim.mode.hole_id == first["id"] and len(objs(h, "kn_hole")) == 1
        assert first["values"]["mass"] == h.params["m_hole"] and first["values"]["spin"] == h.params["spin"]
        assert "kn_hole" in h.sim.palette_state()
        h.cmd("scene", op="remove", id=first["id"])
        assert "computed around this hole" in en(h.errors()[-1])
        h.cmd("scene", op="clear")
        assert [o["type"] for o in h.sim.objects.values()] == ["kn_hole"] and h.sim.mode.geo.n == 0


def test_the_hole_mass_is_a_change_of_units():
    """M 10 -> 20 M☉ at t1: the bodies' Boyer–Lindquist state is untouched, the proper times and the observers' clocks
    in seconds go on continuously; after Δs more seconds the bodies are where a world that kept M = 10 has them after
    Δs/2 (the same evolution, every second now twice as long in units of M); the checks pass."""
    a, b = Harness(V, "kerr_orbits"), Harness(V, "kerr_orbits")
    for h in (a, b):
        run(h, 2e-3)
    ga = a.sim.mode.geo
    bl0, p0 = ga.bl(), ga.momenta()
    tau0 = ga.proper_time() * a.sim.mode.T
    obs = objs(a, "observer")[0]["id"]
    clock0 = a.sim.mode._obs_now(obs, a.sim.objects[obs]["values"], a.sim.mode.t_m())[0] * a.sim.mode.T
    hole = objs(a, "kn_hole")[0]["id"]
    a.cmd("scene", op="set", id=hole, values={"mass": 20.0})
    assert not a.errors(), a.errors()
    ev = [m for m in a.of("event") if "change of scale" in en(m.get("text", ""))]
    assert ev and ev[-1].get("notify")
    assert np.array_equal(ga.bl(), bl0) and np.array_equal(ga.momenta(), p0)
    assert np.allclose(ga.proper_time() * a.sim.mode.T, tau0, rtol=1e-14)
    m = a.sim.mode
    assert m._obs_now(obs, a.sim.objects[obs]["values"], m.t_m())[0] * m.T == pytest.approx(clock0, rel=1e-13)
    ds = 2e-3
    run(a, ds)
    run(b, ds / 2)
    # not bit for bit: the two worlds reach their times by different sub-steps; each run's global error is at most
    # the sum of its local errors: 128 accepted steps per body x rtol 1e-10 of the scale here, 1.3e-8, held at 1e-7
    # (review LB1-physics P12; measured by the reviewer 5.8e-15)
    assert np.allclose(a.sim.mode.geo.bl(), b.sim.mode.geo.bl(), rtol=1e-7, atol=1e-7)
    assert a.sim.mode.geo.t == pytest.approx(b.sim.mode.geo.t, rel=1e-12)
    assert not failed(a), failed(a)


def test_spin_and_charge_change_only_as_a_declared_what_if():
    """a 0.9 -> 0.5 and Q 0 -> 0.3 under moving bodies: each keeps its place, its proper time and its ZAMO-measured
    velocity (to round-off), its E and L change; the world says “WHAT IF” MODEL in its approximations and in the event; the
    checks (K and the mass shell, recounted from the change) pass; a change that would put a body under the new horizon
    is refused and leaves everything as it was."""
    h = Harness(V, "kerr_orbits")
    run(h, 1e-3)
    m = h.sim.mode
    g = m.geo
    keys = [k for k, s in zip(g.keys, g.status()) if s == "active"]
    rows = [g.keys.index(k) for k in keys]
    bl, tau, vz, E0 = g.bl()[rows], g.proper_time()[rows], g.zamo_velocity()[rows], g.constants()["E"][rows]
    hole = objs(h, "kn_hole")[0]["id"]
    h.cmd("scene", op="set", id=hole, values={"spin": 0.5, "charge": 0.3})
    assert not h.errors(), h.errors()
    g2 = m.geo
    r2 = [g2.keys.index(k) for k in keys]
    assert (m.a, m.q) == (0.5, 0.3) and np.array_equal(g2.bl()[r2], bl) and np.array_equal(g2.proper_time()[r2], tau)
    assert np.allclose(g2.zamo_velocity()[r2], vz, rtol=1e-12, atol=1e-14)
    assert not np.allclose(g2.constants()["E"][r2], E0)
    assert any("MODEL" in en(a) for a in h.of("approx")[-1]["approximations"])
    assert any("“WHAT IF” MODEL" in en(e.get("text", "")) for e in h.of("event"))
    run(h, 1e-3)
    assert not failed(h), failed(h)
    # after a capture (found in the browser: a captured body re-placed 1e-9 off the new horizon broke the shell check by
    # its rounding there); now held at r+ + capture_eps, where a capture stops a body
    c = Harness(V, "kerr_orbits")
    run(c, 8e-3, n=40)
    assert "captured" in c.sim.mode.geo.status()
    c.cmd("scene", op="set", id=objs(c, "kn_hole")[0]["id"], values={"spin": 0.5})
    gc = c.sim.mode.geo
    i = gc.status().index("captured")
    assert gc.bl()[i, 0] == pytest.approx(KN.horizons(0.5, 0.0)[0] + gc.capture_eps, rel=1e-12)
    run(c, 2e-4, n=20)
    assert not failed(c), failed(c)
    # a body near the horizon of a fast hole: a slower hole's horizon would swallow it
    f = Harness(V, None, {"laws": "kerr", "spin": 0.99})
    f.cmd("scene", op="add", type="body", values={"r": 1.6, "vmode": "zamo", "v_phi": 0.5, "v_r": 0.3})
    assert not f.errors(), f.errors()
    s0 = f.sim.mode.geo.state_dict()
    f.cmd("scene", op="set", id=objs(f, "kn_hole")[0]["id"], values={"spin": 0.0})
    assert "under the new horizon" in en(f.errors()[-1])
    assert f.sim.mode.a == 0.99 and f.sim.mode.geo.state_dict() == s0 and objs(f, "kn_hole")[0]["values"]["spin"] == 0.99


def test_the_what_if_is_the_engines_rule_without_a_speed_limit():
    """Review LB1-physics P5, P6. The rule is ``theories.alternatives.kn_change_whatif`` (listed in the world's engine
    modules, named in the approximations and the event, which also gives the numbers: the body whose E changed most, the
    circumferential radius's change, the largest γ kept). A body falling into an a = 0.9 hole past γ = 22.4 (ZAMO speed
    above 0.999 c) keeps its γ across a → 0.95 (the former world rule cut it to 0.999 c without a word)."""
    h = Harness(V, None, {"laws": "kerr", "spin": 0.9, "m_hole": 10.0})
    assert "theories.alternatives.kn_change_whatif" in h.sim.engine_modules()
    h.cmd("scene", op="add", type="body", values={"r": 1.7, "theta": 90.0, "vmode": "zamo", "v_r": -0.9, "v_phi": 0.0})
    assert not h.errors(), h.errors()
    m = h.sim.mode
    body = objs(h, "body")[0]["id"]
    for _ in range(400):
        run(h, 2e-6, n=1)
        i = m.geo.keys.index(body)
        if m.geo.status()[i] != "active" or np.linalg.norm(m.geo.zamo_velocity()[i]) > 0.9992:
            break
    i = m.geo.keys.index(body)
    v0 = m.geo.zamo_velocity()[i]
    assert m.geo.status()[i] == "active" and np.linalg.norm(v0) > 0.9992, np.linalg.norm(v0)  # γ > 25
    g0 = 1 / math.sqrt(1 - v0 @ v0)
    h.cmd("scene", op="set", id=objs(h, "kn_hole")[0]["id"], values={"spin": 0.95})
    assert not h.errors(), h.errors()
    v1 = m.geo.zamo_velocity()[m.geo.keys.index(body)]
    g1 = 1 / math.sqrt(1 - v1 @ v1)
    assert abs(np.linalg.norm(v1) - np.linalg.norm(v0)) <= 1e-12 and abs(g1 / g0 - 1) <= 1e-6 * g0 ** 2, (g0, g1)
    assert np.linalg.norm(v1) > 0.999 + 1e-4  # the former clamp would have left 0.999
    ev = [en(e["text"]) for e in h.of("event") if "“WHAT IF” MODEL" in en(e.get("text", ""))][-1]
    assert "kn_change_whatif" in ev and "circumference" in ev and "γ" in ev
    assert any("kn_change_whatif" in en(a) for a in h.of("approx")[-1]["approximations"])


def test_the_radial_period_restarts_when_the_hole_changes_and_the_throw_limit():
    """Review LB1-physics P10: the radial period is measured between two periapsis passages in world seconds; a change
    of the hole's mass (or a «what if») clears them — the period is undefined, with the reason, until two new passages
    (before, the passages in units of M were read with the new seconds per M: the period doubled with M without a new
    passage). Review LB1-p02-ux X4: a Kerr body declares its throw limit (`velocity_max` = its hidden `tv_max`, half
    the speed of light in drawing coordinates per world second, 0.5/T), renewed with the hole's mass."""
    k = Harness(V, None, {"laws": "kerr", "spin": 0.5, "m_hole": 10.0})
    assert k.sim.PALETTE["body"].handles["velocity_max"] == "tv_max"
    k.cmd("scene", op="add", type="body", values={"r": 30.0, "vmode": "zamo", "v_phi": 0.16, "v_r": 0.0})
    body = objs(k, "body")[0]["id"]
    m = k.sim.mode
    assert k.sim.objects[body]["values"]["tv_max"] == pytest.approx(0.5 / m.T, rel=1e-15)
    a_orb = m.measure_now()[0][f"{body}.a"]
    T_kep = 2 * math.pi * a_orb ** 1.5 * m.T
    run(k, 2.3 * T_kep, n=40)
    Tr = m.measure_now()[0][f"{body}.Tr"]
    assert 0.5 * T_kep < Tr < 2 * T_kep, (Tr, T_kep)  # measured (r ≈ 30 M: far from Kepler's; r = 400 M above)
    k.cmd("scene", op="set", id=objs(k, "kn_hole")[0]["id"], values={"mass": 20.0})
    assert not k.errors(), k.errors()
    meas, notes = m.measure_now()
    assert math.isnan(meas[f"{body}.Tr"]) and "anew" in en(notes[f"{body}.Tr"])
    assert k.sim.objects[body]["values"]["tv_max"] == pytest.approx(0.5 / m.T, rel=1e-15)
    run(k, 2.3 * T_kep * 2, n=60)
    assert m.measure_now()[0][f"{body}.Tr"] == pytest.approx(2 * Tr, rel=1e-3)  # the same orbit in twice the seconds
    k.cmd("scene", op="set", id=objs(k, "kn_hole")[0]["id"], values={"spin": 0.6})
    assert not k.errors(), k.errors()
    assert math.isnan(m.measure_now()[0][f"{body}.Tr"])


def test_the_binary_mass_is_a_change_of_units():
    """m 20 -> 40 M☉ on the binary itself: its state in units of m is kept (no restart), its accumulated phase goes on,
    the waves' frequency halves and the detector's strain doubles at that moment; the balance check passes after."""
    h = Harness(V, "pn_inspiral")
    run(h, 0.05)
    m = h.sim.mode
    b = m.bin
    x0, v0, ph0 = b["st"]["x"].copy(), b["st"]["v"].copy(), b["phase"]
    meas0 = m.measure_now()[0]
    binary = objs(h, "binary")[0]["id"]
    det = objs(h, "detector")[0]["id"]
    h.cmd("scene", op="set", id=binary, values={"m_total": 40.0})
    assert not h.errors(), h.errors()
    assert m.bin is b and np.array_equal(b["st"]["x"], x0) and np.array_equal(b["st"]["v"], v0) and b["phase"] == ph0
    meas1 = m.measure_now()[0]
    assert meas1[f"{binary}.f"] == pytest.approx(meas0[f"{binary}.f"] / 2, rel=1e-12)
    assert meas1[f"{det}.hp"] == pytest.approx(2 * meas0[f"{det}.hp"], rel=1e-12)
    assert meas1[f"{binary}.r"] == pytest.approx(2 * meas0[f"{binary}.r"], rel=1e-12)
    assert any("change of scale" in en(e.get("text", "")) for e in h.of("event"))
    run(h, 0.1)
    assert m.bin["phase"] > ph0 and not failed(h), failed(h)


def test_newtonian_handles_drag_and_throw():
    """Every body and field probe is in the frame's ``at``; a drag (an edit of x, y, z alone) moves the body and keeps
    its velocity; a throw (the scene's au/s) sets its velocity, written into the body's own km/s; a throw at 0.1 c
    and more is refused."""
    h = Harness(V, "sun_earth")
    run(h, 1e5)
    fr = h.of("frame")[-1]
    for o in h.sim.objects.values():
        assert o["id"] in fr["at"] and len(fr["at"][o["id"]]) == 3
    earth = [o for o in h.sim.objects.values() if en(o["label"]) == "Earth"][0]
    nb = h.sim.mode.nb
    v0 = nb.body(earth["id"])["v"].copy()
    h.cmd("scene", op="set", id=earth["id"], values={"x": 0.0, "y": 1.5, "z": 0.0})
    assert not h.errors(), h.errors()
    assert np.allclose(nb.body(earth["id"])["x"], [0, 1.5, 0]) and np.array_equal(nb.body(earth["id"])["v"], v0)
    tv = np.array([-1e-7, 0.0, 0.0])  # au/s: 15 km/s
    h.cmd("scene", op="set", id=earth["id"], values={"tvx": tv[0], "tvy": 0.0, "tvz": 0.0})
    assert not h.errors(), h.errors()
    assert np.allclose(nb.body(earth["id"])["v"], tv * P1.YR, rtol=1e-12)
    vals = h.sim.objects[earth["id"]]["values"]
    assert vals["vmode"] == "manual" and vals["vx"] == pytest.approx(-1e-7 * K.AU / 1e3)
    h.cmd("scene", op="set", id=earth["id"], values={"tvx": 0.0, "tvy": 2.1e-4})  # 3.1e4 km/s > 0.1 c
    assert "0.1 of the speed of light" in en(h.errors()[-1])


def test_kerr_drag_and_throw():
    """A body dragged to a point of the drawing goes to its r, θ, φ (a circular orbit to the equator under it); a body
    thrown starts with the ZAMO-measured velocity of the throw: its drawn velocity right after equals the throw's (the
    inverse of the conversion, to 1e-9)."""
    h = Harness(V, "kerr_orbits")
    m = h.sim.mode
    circ = [o for o in h.sim.objects.values() if o["type"] == "body" and o["values"]["vmode"] == "circular"][0]
    h.cmd("scene", op="set", id=circ["id"], values={"x": 6.0, "y": 0.0, "z": 2.0})
    assert not h.errors(), h.errors()
    v = h.sim.objects[circ["id"]]["values"]
    assert v["theta"] == 90.0 and v["z"] == pytest.approx(0.0, abs=1e-12)
    free = [o for o in h.sim.objects.values() if o["type"] == "body" and o["values"]["vmode"] == "zamo"][0]
    h.cmd("scene", op="set", id=free["id"], values={"x": 0.0, "y": 9.0, "z": 1.0})
    w = np.array([0.15, 0.05, -0.02]) / m.T  # drawing units per world second
    h.cmd("scene", op="set", id=free["id"], values={"tvx": w[0], "tvy": w[1], "tvz": w[2]})
    assert not h.errors(), h.errors()
    row = m.geo.keys.index(free["id"])
    assert np.allclose(m._vel([row])[0] / m.T, w, rtol=1e-9)
    assert h.sim.objects[free["id"]]["values"]["vmode"] == "zamo"
    h.cmd("scene", op="set", id=free["id"], values={"x": 0.1, "y": 0.1, "z": 0.0})
    assert "under the horizon" in en(h.errors()[-1])


def test_measurables_kepler_and_the_far_kerr_orbit():
    """The Earth around the Sun: a = 1 au, e ≈ 0, P = 1 yr by Kepler's third law with both masses; the energy and its
    drift, undefined with the reason until the first check. A far Kerr orbit (r ≈ 400 M): its radial period measured
    between two periapsis passages against Kepler's 2π a^(3/2) M (1PN: ~3/a = 0.8 % off). The binary's phase grows
    by ∫Ω dt."""
    h = Harness(V, "sun_earth")
    ms = {m["id"]: m for m in h.sim.measurables()}
    assert {"E", "dE", "L", "dL"} <= set(ms) and all(m["unit"] is not None for m in ms.values())
    run(h, 1e5, n=1)
    fr = h.of("frame")[-1]
    earth = [o for o in h.sim.objects.values() if en(o["label"]) == "Earth"][0]["id"]
    mm = fr["meas"]
    assert mm[f"{earth}.a"] == pytest.approx(1.0, rel=1e-6) and mm[f"{earth}.e"] < 1e-6
    me = K.GM_EARTH / K.GM_SUN
    assert mm[f"{earth}.P"] == pytest.approx(2 * math.pi / math.sqrt(P1.G_AU * (1 + me)), rel=1e-6)
    assert mm[f"{earth}.dist"] == pytest.approx(1.0, rel=1e-6) and abs(mm[f"{earth}.speed"] - 29.78) < 0.01
    run(h, 2e6, n=25)
    assert abs(h.of("frame")[-1]["meas"]["dE"]) < 1e-9
    k = Harness(V, None, {"laws": "kerr", "spin": 0.5, "m_hole": 10.0})
    k.cmd("scene", op="add", type="body", values={"r": 400.0, "vmode": "zamo", "v_phi": 0.042, "v_r": 0.0})
    body = objs(k, "body")[0]["id"]
    m = k.sim.mode
    a_orb = m.measure_now()[0][f"{body}.a"]
    T_kep = 2 * math.pi * a_orb ** 1.5 * m.T
    run(k, 2.2 * T_kep, n=40)
    Tr = m.measure_now()[0][f"{body}.Tr"]
    assert Tr == pytest.approx(T_kep, rel=0.02), (Tr, T_kep)
    p = Harness(V, "pn_inspiral")
    b = p.sim.mode.bin
    ph0 = b["phase"]
    om = []
    for _ in range(20):
        x, v = b["st"]["x"], b["st"]["v"]
        om.append(float(np.linalg.norm(np.cross(x, v))) / float(x @ x))
        run(p, 0.01, n=1)
    x, v = b["st"]["x"], b["st"]["v"]
    om.append(float(np.linalg.norm(np.cross(x, v))) / float(x @ x))
    dt = 0.01 / p.sim.mode.T
    expect = sum(0.5 * (om[i] + om[i + 1]) * dt for i in range(20))
    assert b["phase"] - ph0 == pytest.approx(expect, rel=1e-3)


def _new_world_from(h, params):
    """The framework's carry-over (P16.1): the scene exported, marked, given to a new world of other laws."""
    sc = h.sim.export_message()[0]["scene"]
    sc["carry"] = True
    viz = registry.load(V)
    p, errors = viz["schema"].resolve(None, {**params, "scene": sc})
    assert not errors, errors
    msgs = []
    sim = viz["simulation"](p, 1, lambda m, b=None: msgs.append(m))
    Runner(sim, lambda m, b=None: msgs.append(m), queue.Queue())._start_world()
    return sim, msgs


def test_carry_over_across_the_laws():
    """Newton -> Kerr: the Newtonian hole becomes the Kerr–Newman hole (its mass), the stars are listed with the
    reason; Kerr -> Newton: the hole becomes a Newtonian hole; the PN binary -> Newton: its two bodies as Newtonian
    holes with zero total momentum on either side of their centre of mass, the detector listed; Newton -> PN: two stars
    an au apart are far outside the binary's range — listed with the separation."""
    n = Harness(V, "hole_stars")
    sim, msgs = _new_world_from(n, {"laws": "kerr", "spin": 0.7})
    holes = [o for o in sim.objects.values() if o["type"] == "kn_hole"]
    assert len(holes) == 1 and holes[0]["values"]["mass"] == 1000.0 and holes[0]["values"]["spin"] == 0.7
    note = [m for m in msgs if m.get("type") == "notice" and "not carried" in en(m.get("text", ""))]
    assert note and "Star 1" in en(note[-1]["text"])
    k = Harness(V, "kerr_orbits")
    sim, _ = _new_world_from(k, {"laws": "newton"})
    assert [o["type"] for o in sim.objects.values()] == ["hole"]
    assert sim.objects[list(sim.objects)[0]]["values"]["mass"] == 10.0
    p = Harness(V, "pn_eccentric")
    run(p, 0.01)
    sim, msgs = _new_world_from(p, {"laws": "newton"})
    nb = sim.mode.nb
    assert nb.n == 2 and nb.masses().sum() == pytest.approx(40.0)
    assert np.allclose((nb.masses()[:, None] * nb.velocities()).sum(0), 0.0, atol=1e-9 * float(np.abs(nb.velocities()).max()))
    assert any("detector" in en(m.get("text", "")) for m in msgs if m.get("type") == "notice")
    s = Harness(V, "sun_earth")
    _, msgs = _new_world_from(s, {"laws": "pn"})
    assert any("outside the range of a GR binary" in en(m.get("text", "")) for m in msgs if m.get("type") == "notice")


def test_a_new_kerr_world_keeps_the_bodies_states():
    """Review LB1-framework F5 (p01): a new Kerr–Newman world of another hole (the dialog's mass, spin, charge) with
    "carry the scene". Another mass only: the bodies keep their state in units of M (a change of units), their proper
    times and the observers' clocks in seconds. Another spin: each body starts where it was, with the momentum its local
    ZAMO measured (its ZAMO velocity the same to 1e-12; E, L new), said in the notice object by object; a body under
    the new, larger horizon starts anew from its parameters, said as restarted (before: every state from another metric
    was refused off its mass shell, or the notice said nothing)."""
    k = Harness(V, "kerr_orbits")
    run(k, 2e-3)
    m0 = k.sim.mode
    g0 = m0.geo
    rows = [i for i, s in enumerate(g0.status()) if s == "active"]
    keys = [g0.keys[i] for i in rows]
    bl0, vz0, tau_s = g0.bl()[rows], g0.zamo_velocity()[rows], g0.proper_time()[rows] * m0.T
    sim, msgs = _new_world_from(k, {"laws": "kerr", "m_hole": 20.0, "spin": m0.a, "charge": m0.q})
    g = sim.mode.geo
    r = [g.keys.index(o["id"]) for o in sim.objects.values() if o["id"] in keys] if all(
        isinstance(x, str) for x in keys) else None
    assert sim.mode.M == 20.0 and g.n == g0.n
    order = [g.keys.index(kk) for kk in keys] if r is None else r
    assert np.array_equal(g.bl()[order], bl0)
    assert np.allclose(g.proper_time()[order] * sim.mode.T, tau_s, rtol=1e-14)
    n = [m for m in msgs if m.get("type") == "notice" and m.get("carry")][-1]
    assert "proper time in seconds kept" in en(n["text"]), en(n["text"])
    sim, msgs = _new_world_from(k, {"laws": "kerr", "m_hole": 10.0, "spin": 0.5, "charge": 0.0})
    g = sim.mode.geo
    order = [g.keys.index(kk) for kk in keys]
    assert np.array_equal(g.bl()[order], bl0) and np.max(np.abs(g.zamo_velocity()[order] - vz0)) <= 1e-9
    n = [m for m in msgs if m.get("type") == "notice" and m.get("carry")][-1]
    assert "with the momentum its local zero-angular-momentum observer" in en(n["text"]), en(n["text"])
    assert {r_["how"] for r_ in n["carry"]["objects"] if r_["id"] in keys} == {"state"}
    f = Harness(V, None, {"laws": "kerr", "spin": 0.99})
    f.cmd("scene", op="add", type="body", values={"r": 2.6, "theta": 90.0, "vmode": "zamo", "v_phi": 0.0, "v_r": -0.9})
    f.cmd("scene", op="add", type="body", values={"r": 12.0, "vmode": "zamo", "v_phi": 0.3})
    f.cmd("scene", op="add", type="body", values={"r": 1.6, "vmode": "zamo", "v_phi": 0.5, "v_r": 0.3})
    for _ in range(200):
        run(f, 2e-6, n=1)
        if f.sim.mode.geo.bl()[0, 0] < 1.9:
            break
    assert f.sim.mode.geo.bl()[0, 0] < 1.9 and f.sim.mode.geo.status()[0] == "active"
    sim, msgs = _new_world_from(f, {"laws": "kerr", "spin": 0.0})
    n = [m for m in msgs if m.get("type") == "notice" and m.get("carry")][-1]
    hows = {en(r_["label"]): r_["how"] for r_ in n["carry"]["objects"]}
    # the falling body's state lies under the new horizon r+ = 2: anew from its set-up (r = 2.6); the third body's set-up
    # (r = 1.6) is under it too: refused, named
    assert hows["Test body 1"] == "restarted" and hows["Test body 2"] == "state", (hows, en(n["text"]))
    assert hows["Test body 3"] == "refused" and "under the new hole's horizon" in en(n["text"])


def _world(params):
    viz = registry.load(V)
    p, errors = viz["schema"].resolve(None, params)
    assert not errors
    frames, script = [], []

    def emit(meta, blobs=None):
        if meta.get("type") == "frame":
            frames.append(meta)
            script.append({"frame": meta["t"]})
        elif meta.get("type") == "command":
            script.append({"t": meta["t"], "cmd": meta["cmd"], "args": meta["args"]})
    sim = viz["simulation"](p, 7, emit)
    return sim, Runner(sim, emit, queue.Queue()), frames, script


def test_a_world_with_live_masses_and_handles_is_replayed_bit_for_bit():
    """Kerr: the mass doubled, the spin changed («what if»), a body dragged and thrown; rebuilt by replaying its record:
    the same geodesics state, the same clock, the same measurables."""
    params = dict(registry.load(V)["schema"].presets["kerr_orbits"]["params"])
    sim, run_, frames, script = _world(params)
    run_._start_world()
    hole = [o for o in sim.objects.values() if o["type"] == "kn_hole"][0]["id"]
    body = [o for o in sim.objects.values() if o["type"] == "body"][1]["id"]
    run_._advance(1e-3)
    run_._frame(0.0)
    run_.handle({"cmd": "scene", "args": {"op": "set", "id": hole, "values": {"mass": 20.0}}})
    run_._advance(2e-3)
    run_._frame(0.0)
    run_.handle({"cmd": "scene", "args": {"op": "set", "id": hole, "values": {"spin": 0.6}}})
    run_.handle({"cmd": "scene", "args": {"op": "set", "id": body, "values": {"x": 0.0, "y": 10.0, "z": 0.5}}})
    run_.handle({"cmd": "scene", "args": {"op": "set", "id": body, "values": {"tvx": 1e3, "tvy": 0.0, "tvz": 0.0}}})
    run_._advance(3e-3)
    run_._frame(0.0)
    sim2, run2, frames2, _ = _world(params)
    run2.restore(1, list(script)[:-1], sim.t, lambda on: None)
    run2._frame(0.0)
    assert sim2.mode.geo.state_dict() == sim.mode.geo.state_dict()
    assert sim2.mode.clk.state() == sim.mode.clk.state() and sim2.mode.model == sim.mode.model
    ma, mb = frames[-1]["meas"], frames2[-1]["meas"]
    assert set(ma) == set(mb) and all(ma[k] == mb[k] or (math.isnan(ma[k]) and math.isnan(mb[k])) for k in ma)
