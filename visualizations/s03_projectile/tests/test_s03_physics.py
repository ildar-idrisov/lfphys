# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""S03 projectile: the run as a whole (every preset, the events against the engine, causality, the refusals, the
companions), the real forces against independent computations and against the engine step E03's references
(``lfphys/sources/s03_forces_2026-11-18.md`` §7; EX2 design §10, §11 items 25, 39–42), and the bench's computed values
(``lab_reference``) against independent computations. The screens, the ways of the bench and the Watch's captions:
``test_s03_screens.py``."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import optimize

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core.mechanics import G_STANDARD as G  # noqa: E402
from lfphys.core.mechanics import drop_east_drift, history_bound, normal_gravity, vacuum_landing_time  # noqa: E402
from lfphys.theories.models import drag_quadratic as dq  # noqa: E402
from lfphys.theories.models import magnus  # noqa: E402
from lfphys.tools.stats import linear_fit  # noqa: E402
from lfviz import headless, registry  # noqa: E402
from s03_projectile.engine import shot as S  # noqa: E402
from s03_projectile.engine.shot import OBJECTS, Shot, flight_of, optimum_angle  # noqa: E402
from s03_projectile.viz import DEFAULT_LAW, INSTRUMENTS, SCHEMA, VIZ, Simulation  # noqa: E402

V = "s03_projectile"
HS = [round(0.20 + 0.05 * i, 2) for i in range(17)]
mm = 1e3


def _bad(checks):
    return [(c["id"], c.get("value"), c.get("ref"), c.get("rel"), c.get("tol")) for c in checks
            if headless.check_state(c) == "failed"]


def _run(preset=None, params=None, t=12.0):
    h = Harness(V, preset, params)
    h.run_to(t)
    h.runner._frame(0.0)
    return h


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_every_preset_runs_and_all_checks_pass(preset):
    h = _run(preset)
    assert not h.errors(), h.errors()
    cs = list(h.checks().values())
    assert len(cs) >= 3 and not _bad(cs), _bad(cs)
    assert h.of("header")[0]["engine"], "the engine modules are listed"
    kinds = [e["kind"] for e in h.of("event")]
    assert kinds.count("landing") == 1 and kinds[0] == "launch" and h.of("event")[0]["t"] == 0.0


def test_the_place_is_where_the_normal_gravity_is_the_standard_one():
    """45.5° N (design §11 item 42; E03): the WGS 84 normal gravity on the ellipsoid equals g_n there."""
    assert S.LATITUDE == pytest.approx(45.4996, abs=1e-4) and normal_gravity(S.LATITUDE) == pytest.approx(G, rel=1e-12)
    assert S.OMEGA_Z == pytest.approx(7.292115e-5 * math.cos(math.radians(S.LATITUDE)), rel=1e-12)


def test_the_events_carry_the_engines_values_and_come_when_the_time_reaches_them():
    p = {"object": "ball67", "h_m": 2.0, "v0": 12.0, "angle_deg": 35.0, "air": True}
    shot = Shot("ball67", 2.0, 12.0, 35.0, True)
    h = Harness(V, None, p)
    dt = 1 / 30
    k = 0
    while h.sim.t < shot.T + 0.2:
        k += 1
        h.run_to(k * dt)
        h.runner._frame(0.0)
    ev = {e["kind"]: e for e in h.of("event")}
    assert ev["landing"]["data"]["L"] == shot.L and ev["landing"]["data"]["T"] == shot.T
    assert ev["landing"]["text"]["$t"] == "the ball lands: range {L:.4g} m, flight time {T:.4g} s"
    # the events carry their values (EX2 §10), the sentence's to 6 digits (it shows 4), the data's in full
    assert ev["landing"]["text"]["a"] == {"L": float(f"{shot.L:.6g}"), "T": float(f"{shot.T:.6g}")}
    assert ev["apex"]["data"]["H"] == shot.flight.apex["y"] and ev["apex"]["t"] == shot.t_apex
    assert ev["apex"]["text"]["a"] == {"H": float(f"{shot.flight.apex['y']:.6g}")}
    assert ev["launch"]["text"]["a"] == {"v": 12.0, "a": 35.0}
    # causality: a message is emitted in the frame whose time has reached it; the samples are revealed no earlier
    for m, b in h.msgs:
        if m["type"] in ("traj", "event", "check") and m.get("t") is not None:
            assert m["t"] <= h.sim.t + 1e-12
        if m["type"] == "traj":
            assert float(np.max(b["s"][:, 0])) <= m["t"] + 1e-12
    frames = h.of("frame")
    before = [f for f in frames if f["t"] < shot.T]
    after = [f for f in frames if f["t"] >= shot.T]
    assert all(f["meas"]["range"] is None and f["meas"]["sideways"] is None for f in before)
    assert all(f["meas"]["range"] == shot.L and f["meas"]["sideways"] == mm * shot.side["right"] for f in after)
    assert all(f["meas"]["apex_h"] is None for f in frames if f["t"] < shot.t_apex)
    assert all(f["meas"]["p_air"] == 101.325 for f in frames)
    # the heat is the drag's work alone; the energy balance closes with the buoyancy's and the added mass's work
    f = frames[len(before) // 2]
    W = shot.flight.state(f["t"])[2]
    assert f["meas"]["Q"] == pytest.approx(-W[0], rel=1e-3) and len(W) == 4  # drag, Coriolis, buoyancy, added mass
    # the samples, all of them sent, are the engine's at exact multiples of 1/60 s
    s = np.vstack([b["s"] for m, b in h.msgs if m["type"] == "traj" and m["body"] == "main"])
    assert np.array_equal(s[:, 0], np.arange(len(s)) / 60.0)
    assert np.allclose(s[:, 1:], shot.flight.sample(60.0)["r"], rtol=0, atol=1e-12)


def test_the_refusals_say_why():
    for p in ({"h_m": 0.0, "angle_deg": 0.0}, {"h_m": 0.0, "angle_deg": -10.0}, {"h_m": 0.0, "v0": 0.0},
              {"h_m": 0.0, "companion": "drop"}, {"companion": "vacuum", "air": False}):
        params, errs = SCHEMA.resolve("field", p)
        assert not errs
        with pytest.raises(ValueError):
            Simulation.check_params(params)
    params, _ = SCHEMA.resolve("field", {"h_m": 1.0, "angle_deg": -30.0, "v0": 0.0})
    Simulation.check_params(params)  # a drop from 1 m: a flight
    # a ball rolling off the chute in air: the spinning ball's data cover Re ≤ 1e4 (7.53 m/s for the steel ball)
    assert S.spin_speed_limit("steel20") == pytest.approx(7.531, abs=1e-3)
    params, _ = SCHEMA.resolve("story", {"air": True, "v0": 4.0, "h_m": 5.0})  # up to 10.7 m/s
    with pytest.raises(ValueError):
        Simulation.check_params(params)
    for p in ({"air": True}, {"air": False, "v0": 4.0, "h_m": 5.0}, {"air": True, "object": "ball67", "v0": 25.0}):
        Simulation.check_params(SCHEMA.resolve("story", p)[0])
    # every point of part 1 in air is inside the data (h ≤ 1 m: at most 4.67 m/s)
    assert S.top_speed(1.0, 1.5) < S.spin_speed_limit("steel20")


def test_only_the_steel_ball_off_the_chute_spins():
    assert S.spin_of("steel20", 0.6, 1.5, 0.0) == 150.0 and S.rolls("steel20", 0.6, 1.5, 0.0)
    for args in (("steel20", 0.0, 5.0, 45.0), ("steel20", 0.6, 1.5, 5.0), ("ball67", 1.0, 15.0, 0.0),
                 ("steel20", 1.0, 0.0, 0.0)):
        assert S.spin_of(*args) == 0.0
    h = Harness(V, "chute", {"air": True})
    h.run_to(0.1)
    h.runner._frame(0.0)
    assert h.of("header")[0]["launcher"]["chute"] is True and h.of("header")[0]["launcher"]["spin"] == 150.0
    f = h.of("frame")[-1]
    assert f["F_lift"] and f["F_drag"]  # the Magnus force is drawn: the run's
    assert h.of("event")[0]["text"]["$t"].startswith("the ball leaves the chute") and h.of("event")[0]["text"]["a"]["w"] == 150.0


@pytest.mark.parametrize("air", [False, True])
def test_the_dropped_ball_and_the_independence_of_the_motions(air):
    """The dropped ball against its own references; the two heights: in vacuum on the rotating Earth they differ only
    by the Eötvös effect, against its first-order closed form y_thrown − y_dropped = Ω_z·v₀·t² (the thrown ball's
    extra upward acceleration 2Ω_z·v₀; this test's own formula)."""
    h = _run("story", {"air": air})
    cs = h.checks()
    assert headless.check_state(cs["other.drift"]) == "ok"
    same = cs["other.same_height"]
    main, other = h.sim.main, h.sim.other
    assert same.get("info") and same["value"] != 0
    if not air:
        assert headless.check_state(cs["other.T"]) == "ok"
        assert cs["other.T"]["ref"] == pytest.approx(math.sqrt(2 * 1.25 / G), rel=1e-15)
        t_end = other.ts[min(main.n_until(min(main.T, other.T)), other.n_until(min(main.T, other.T))) - 1]
        assert same["value"] == pytest.approx(S.OMEGA_Z * 2.0 * t_end ** 2, rel=2e-3)
        assert same["value"] < 0.03e-3  # «to 0.03 mm» (the Watch's caption)
        # the dropped ball drifts east: the engine's closed form of first order
        assert other.x_land == pytest.approx(drop_east_drift(1.25, S.LATITUDE, G), rel=1e-6)
    else:  # in air: no second method for a vertical fall (stated); the thrown ball rolls off the chute, and the Magnus
        # force of its topspin pushes it down more than its drag's upward part lifts it: it lands first, lower all along
        assert cs["other.T"]["ref"] is None and headless.check_state(cs["other.T"]) == "na"
        assert main.spin == 160.0 / 0.8 and same["value"] < 0 and main.T < other.T
        light = _run("story", {"air": True, "object": "ball67"})  # no spin: the drag's upward part lifts it
        assert light.checks()["other.same_height"]["value"] > 0 and light.sim.main.T > light.sim.other.T


def test_vertical_throws_against_the_closed_forms_and_the_first_order_drift():
    """In vacuum: T and H against the closed forms (within (Ω_z·T)²), the drift west of a throw straight up from the
    floor against its first-order closed form x = −Ω_z (v₀T² − gT³/3) (this test's own); in air the drift against the
    world's second method only, T and H without one."""
    for v0, h0 in ((10.0, 0.0), (25.0, 0.0), (5.0, 3.0)):
        s = Shot("ball67", h0, v0, 90.0, False)
        T = vacuum_landing_time(h0, v0, G)
        assert s.T == pytest.approx(T, rel=1e-9 + (S.OMEGA_Z * T) ** 2)
        if h0 == 0.0:
            x1 = -S.OMEGA_Z * (v0 * T ** 2 - G * T ** 3 / 3)
            assert s.x_land == pytest.approx(x1, rel=4 * (S.OMEGA_Z * T) ** 2 + 1e-8)
        assert s.references["drift"] == pytest.approx(s.x_land, rel=s.references["tol_L"])
    h = _run(None, {"object": "ball67", "h_m": 3.0, "v0": 10.0, "angle_deg": 90.0, "air": True})
    cs = h.checks()
    assert not _bad(cs.values()) and headless.check_state(cs["main.drift"]) == "ok"
    assert headless.check_state(cs["main.T"]) == "na" and headless.check_state(cs["main.energy"]) == "ok"
    assert cs["main.drift"]["value"] < 0  # thrown up: west


def test_the_second_method_agrees_where_it_applies():
    """angle_flight (the velocity's angle, assembled on its own) against fly in time, for every kind of flight the
    world makes: vacuum, air, the spinning ball, downward throws."""
    for args in (("steel20", 0.6, 1.5, 0.0, True), ("steel20", 0.0, 5.0, 45.0, True), ("ball67", 10.0, 25.0, 85.0, True),
                 ("ball67", 0.0, 20.0, 40.0, True), ("ball67", 10.0, 25.0, -30.0, False), ("steel20", 1.0, 2.0, 0.0, False)):
        s = Shot(*args)
        r = s.references
        assert r["how"] == "angle"
        assert abs(r["T"] / s.T - 1) < 1e-9 and abs(r["L"] / s.L - 1) < 1e-9 * max(1, r["scale"] / s.L), args


# --- the real forces against E03's references (s03_forces §7; design A.8) ---------------------------------------------
def _p1(h, edge="central", **kw):
    return flight_of("steel20", h, 1.5, 0.0, True, rotation=False, edge=edge, **kw).range


def _vac(h, v0, a):
    vx, vy = S.launch_vector(v0, a)
    return vx * vacuum_landing_time(h, vy, G)


def test_part_1_each_force_against_E03():
    """The chute (steel 20 mm, 1.5 m/s, h 0.20–1.00 m), mm: the Magnus force −0.134 to −1.083 (band −0.110 to −0.893 /
    −0.165 to −1.332), the spin's drag −0.046 to −0.242, the air's whole effect −0.227 to −1.734 (band −0.193 to
    −1.485 / −0.268 to −2.045), beyond the tape's 0.5 mm from h = 0.40 m; the world's shares are the same flights."""
    lift, sd, tot = [], [], []
    for h in HS:
        s = Shot("steel20", h, 1.5, 0.0, True)
        lift.append(mm * s.shares["lift"])
        sd.append(mm * s.shares["spin_drag"])
        tot.append(mm * s.shares["total"])
        assert s.shares["total"] == pytest.approx(_p1(h) - _vac(h, 1.5, 0.0), rel=1e-12)
    assert (round(max(lift), 3), round(min(lift), 3)) == (-0.134, -1.083)
    assert (round(max(sd), 3), round(min(sd), 3)) == (-0.046, -0.242)
    assert (round(max(tot), 3), round(min(tot), 3)) == (-0.227, -1.734)
    assert next(h for h, t in zip(HS, tot) if t < -0.5) == 0.40
    for edge, want in (("low", (-0.193, -1.485)), ("high", (-0.268, -2.045))):
        b = [mm * (_p1(h, edge) - _vac(h, 1.5, 0.0)) for h in (0.2, 1.0)]
        assert (round(b[0], 3), round(b[1], 3)) == want
    # the band in the drawer is these flights with the Earth's rotation
    s = Shot("steel20", 1.0, 1.5, 0.0, True)
    assert sorted(s.band.values()) == sorted(flight_of("steel20", 1.0, 1.5, 0.0, True, edge=e).range for e in ("low", "high"))
    # buoyancy and added mass +0.035 to +0.078; the curve against the constant +0.007 to +0.056 (neither spinning, no
    # medium: E03's columns); the world's «drag» share is the curve alone against vacuum
    from lfphys.core.mechanics import fly
    fl, cmc = [], []
    for h in (0.2, 1.0):
        s = Shot("steel20", h, 1.5, 0.0, True)
        fl.append(mm * s.shares["fluid"])
        curve = fly(s.body, (0.0, h), (1.5, 0.0), forces=[dq.CurveDrag.sphere(0.020, S.medium())]).range
        const = fly(s.body, (0.0, h), (1.5, 0.0), forces=[dq.QuadraticDrag.sphere(0.020, S.medium())]).range
        assert s.shares["drag"] == pytest.approx(curve - _vac(h, 1.5, 0.0), rel=1e-12)
        cmc.append(mm * (curve - const))
    assert [round(x, 3) for x in fl] == [0.035, 0.078]
    assert [round(x, 3) for x in cmc] == [0.007, 0.056]


def test_part_2_and_3_each_force_against_E03():
    """The launcher (steel, 5 m/s, θ 15–75°): the constant C_d −2.96 to −13.98 mm (the design's −13.7 [error in earlier]),
    the curve against the constant +0.459 to +2.053, buoyancy and added mass +0.291 to +0.582; the light ball (20 m/s,
    θ 20–70°): the curve against the constant +0.492 to +1.087 m, buoyancy and added mass +0.070 to +0.113 m."""
    from lfphys.core.mechanics import fly
    p2c, p2k, p2f = [], [], []
    for a in range(15, 76, 5):
        s = Shot("steel20", 0.0, 5.0, float(a), True)
        const = fly(s.body, (0.0, 0.0), S.launch_vector(5.0, a), forces=[dq.QuadraticDrag.sphere(0.020, S.medium())]).range
        p2c.append(mm * (const - _vac(0.0, 5.0, a)))
        p2k.append(mm * (_vac(0.0, 5.0, a) + s.shares["drag"] - const))
        p2f.append(mm * s.shares["fluid"])
    assert (round(max(p2c), 2), round(min(p2c), 2)) == (-2.96, -13.98) and p2c.index(min(p2c)) == 7  # 50°
    assert (round(min(p2k), 3), round(max(p2k), 3)) == (0.459, 2.053)
    assert (round(min(p2f), 3), round(max(p2f), 3)) == (0.291, 0.582)
    p3k, p3f = [], []
    for a in range(20, 71, 5):
        s = Shot("ball67", 0.0, 20.0, float(a), True)
        const = fly(s.body, (0.0, 0.0), S.launch_vector(20.0, a), forces=[dq.QuadraticDrag.sphere(0.067, S.medium())]).range
        p3k.append(_vac(0.0, 20.0, a) + s.shares["drag"] - const)
        p3f.append(s.shares["fluid"])
    assert (round(min(p3k), 3), round(max(p3k), 3)) == (0.492, 1.087)
    assert (round(min(p3f), 3), round(max(p3f), 3)) == (0.070, 0.113)


def test_the_history_bound_and_the_earths_rotation_against_E03():
    """The drawer's values: the history force's bound ≤ 0.037 mm (part 1), ≤ 0.357 mm (part 2, 50°), ≤ 61.5 mm (part
    3, 50°); its largest force over the weight 2.0e-4, 3.0e-4 (75°), 3.2e-3 (70°); with n = 500 steps against n = 2000
    to 1e-4. The Earth's rotation: part 1 +0.004 to +0.021 mm along and 0.003–0.016 mm to the right; part 2 −0.062 to
    +0.088 mm (30°) and 0.017–0.103 mm (55°); part 3 +2.84 mm (25°) to −1.64 mm (70°) and 1.35–3.73 mm (55°); Explore's
    longest throw +2.42 mm along and 7.30 mm to the right."""
    s = Shot("steel20", 1.0, 1.5, 0.0, True)
    full = history_bound(s.flight, n=2000)
    assert s.history["dL_bound"] == pytest.approx(full["dL_bound"], rel=1e-4)
    assert round(mm * s.history["dL_bound"], 3) == 0.037 and round(s.history["B_over_weight"], 5) == 2.0e-4
    p2 = {a: Shot("steel20", 0.0, 5.0, float(a), True) for a in range(15, 76, 5)}
    assert round(mm * max(x.history["dL_bound"] for x in p2.values()), 3) == 0.357
    assert max(p2, key=lambda a: p2[a].history["dL_bound"]) == 50 and max(p2, key=lambda a: p2[a].history["B_over_weight"]) == 75
    p3 = {a: Shot("ball67", 0.0, 20.0, float(a), True) for a in range(20, 71, 5)}
    assert round(mm * max(x.history["dL_bound"] for x in p3.values()), 1) == 61.5
    assert round(max(x.history["B_over_weight"] for x in p3.values()), 4) == 3.2e-3

    def along(x):
        return mm * (x.x_land - x.unrotated["L"])
    p1 = [Shot("steel20", h, 1.5, 0.0, True) for h in HS]
    assert (round(min(map(along, p1)), 3), round(max(map(along, p1)), 3)) == (0.004, 0.021)
    assert (round(min(mm * x.side["right"] for x in p1), 3), round(max(mm * x.side["right"] for x in p1), 3)) == (0.003, 0.016)
    a2 = {a: along(x) for a, x in p2.items()}
    assert (round(min(a2.values()), 3), round(max(a2.values()), 3), max(a2, key=a2.get)) == (-0.062, 0.088, 30)
    r2 = {a: mm * x.side["right"] for a, x in p2.items()}
    assert (round(min(r2.values()), 3), round(max(r2.values()), 3), max(r2, key=r2.get)) == (0.017, 0.103, 55)
    a3 = {a: along(x) for a, x in p3.items()}
    assert (round(max(a3.values()), 2), max(a3, key=a3.get), round(a3[70], 2)) == (2.84, 25, -1.64)
    r3 = {a: mm * x.side["right"] for a, x in p3.items()}
    assert (round(min(r3.values()), 2), round(max(r3.values()), 2), max(r3, key=r3.get)) == (1.35, 3.73, 55)
    x = Shot("ball67", 10.0, 25.0, 45.0, True)
    assert (round(along(x), 2), round(mm * x.side["right"], 2)) == (2.42, 7.30)


def test_the_drawer_states_the_forces_in_every_air_flight():
    h = _run("chute", {"air": True, "h_m": 1.0})
    cs = h.checks()
    for cid in ("main.curve", "main.spin", "main.air", "main.band", "main.cd_const", "main.history", "main.rotation"):
        assert cid in cs, cid
    assert cs["main.curve"]["ok"] and cs["main.spin"]["ok"]
    assert all(cs[c].get("info") for c in ("main.air", "main.band", "main.cd_const", "main.history", "main.rotation"))
    s = h.sim.main
    assert cs["main.air"]["value"] == s.shares["total"] and cs["main.history"]["value"] == s.history["dL_bound"]
    assert cs["main.rotation"]["value"] == mm * s.side["right"]
    lo, hi = sorted(s.band.values())
    assert cs["main.band"]["note"]["a"]["lo"] == pytest.approx(lo, rel=1e-5) and lo < s.L < hi
    assert cs["main.band"]["note"]["a"]["hi"] == pytest.approx(hi, rel=1e-5)
    assert cs["main.band"]["note"]["a"]["a"] == pytest.approx(magnus.LIFT_BAND[0], rel=1e-5)
    assert cs["main.band"]["note"]["a"]["d"] == pytest.approx(magnus.DRAG_BAND[1], rel=1e-5)
    # the constant C_d of earlier versions as the comparison (design §11 item 25): the curve flies farther here
    h = _run(None, {"object": "ball67", "h_m": 0.0, "v0": 20.0, "angle_deg": 40.0, "air": True})
    cc = h.checks()["main.cd_const"]
    assert cc.get("info") and cc["ref"] == h.sim.main.L and cc["value"] < cc["ref"]
    assert cc["note"]["a"]["p"] == pytest.approx(100 * (cc["value"] / cc["ref"] - 1), rel=1e-5)
    # in vacuum only the Earth's rotation is stated
    h = _run("launcher")
    assert set(k for k, c in h.checks().items() if c.get("info")) == {"main.rotation"}


# --- the bench's computed values (lab_reference) ------------------------------------------------------------------------
def _step(sid):
    lab = next(s for s in VIZ["screens"] if s["kind"] == "lab")
    return next(s for s in lab["steps"] if s["id"] == sid)


def _ref(sid, reference):
    st = _step(sid)
    fixed = headless.resolve(registry.load(V), st["preset"], st["fixed"])
    return Simulation.lab_reference(sid, fixed, {c["param"]: c["values"] for c in st["controls"]}, reference)


def _angle_range(obj, h, v0, a, air):
    """The range by the second method alone (the velocity's angle; no time integration), with this world's forces."""
    return Shot(obj, h, v0, a, air).references["L"]


def test_lab_reference_of_every_law_against_an_independent_computation():
    k = 1.5 * math.sqrt(2 / G)
    r = _ref("heights", "k_horizontal")
    assert r["value"] == pytest.approx(k, rel=1e-15) and r["kind"] == "closed form" and r["unit"].msgid == "m^½"
    rot = [mm * (Shot("steel20", h, 1.5, 0.0, False).L - 1.5 * math.sqrt(2 * h / G)) for h in HS]
    assert r["how"].args["a"] == min(rot) and r["how"].args["b"] == max(rot) and 0 < min(rot) < max(rot) < 0.03
    # k in air: the line through the origin over the second method's ranges in air (the tape's error)
    r = _ref("heights", "k_in_air")
    L2 = np.array([_angle_range("steel20", h, 1.5, 0.0, True) for h in HS])
    f = linear_fit(np.sqrt(HS), L2, 0.0, 0.0005, "line0")
    assert r["value"] == pytest.approx(f["params"][-1], rel=1e-9) and r["how"].args["h2"] == 0.40
    assert r["how"].args["z"] == pytest.approx((k - f["params"][-1]) / f["sigma"][-1], rel=1e-6) and r["how"].args["z"] > 5
    assert _ref("heights", "fall_coefficient")["value"] == pytest.approx(math.sqrt(2 / G), rel=1e-15)
    r = _ref("angles", "v2_over_g")
    assert r["value"] == pytest.approx(25.0 / G, rel=1e-15) and r["how"].args["a"] < 0 < r["how"].args["b"]
    r = _ref("angles", "slope_in_air")
    th = np.arange(15, 76, 5.0)
    s2 = np.sin(np.radians(2 * th))
    sx = np.sqrt((2 * np.cos(np.radians(2 * th)) * math.radians(0.5)) ** 2
                 + 0.5 * (4 * s2 * math.radians(0.5) ** 2) ** 2)
    f = linear_fit(s2, np.array([_angle_range("steel20", 0.0, 5.0, a, True) for a in th]), sx, 0.0005, "line0")
    assert r["value"] == pytest.approx(f["params"][-1], rel=1e-9) and round(r["how"].args["z"]) == 15
    assert _ref("angles", "theta_max_vacuum")["value"] == 45.0 and _ref("air", "theta_max_vacuum")["value"] == 45.0
    # the optimum in air: the second method's range maximised by Brent's method (no time integration)
    for sid, ref, obj, v0, want in (("air", "theta_max_air", "ball67", 20.0, 42.3), ("angles", "theta_max_in_air",
                                                                                      "steel20", 5.0, 45.0)):
        r = _ref(sid, ref)
        best = optimize.minimize_scalar(lambda a, o=obj, v=v0: -_angle_range(o, 0.0, v, a, True), bounds=(35.0, 48.0),
                                        method="bounded", options={"xatol": 1e-4}).x
        assert r["kind"] == "engine" and r["value"] == want and abs(r["value"] - best) <= 0.05 + 1e-4, (sid, best)
    r = _ref("air", "theta_max_air")
    assert r["how"].args["b"] == 41.9  # the constant C_d's optimum, stated beside it (E03: 41.9°)
    assert DEFAULT_LAW == {"heights": "k_horizontal", "angles": "v2_over_g", "air": "theta_max_air"}
    with pytest.raises(ValueError):
        Simulation.lab_reference("nothing", {}, {})
    with pytest.raises(ValueError):
        _ref("heights", "theta_max_air")


def test_optimum_angle_scans_the_world_forces():
    best, L, n = optimum_angle("ball67", 0.0, 20.0, True, 0.1)
    assert (best, n) == (42.3, 110) and L == pytest.approx(Shot("ball67", 0.0, 20.0, 42.3, True).L, rel=1e-9)
    assert optimum_angle("ball67", 0.0, 20.0, True, 0.1, drag="const")[0] == 41.9


def test_the_engine_modules_and_the_air_s_data_set():
    h = _run("chute", {"air": False})
    assert h.sim.engine_modules() == ["core.mechanics.particle", "core.mechanics.earth_frame", "core.mechanics.drag",
                                      "theories.models.drag_quadratic", "theories.models.magnus", "core.data:air"]
    eng = h.of("header")[0]["engine"]
    assert [d["id"] for d in eng if d["id"].startswith("core.data")] == ["core.data:air"]
    assert INSTRUMENTS["manometer"]["reads"] == "p_air" and h.of("frame")[0]["meas"]["p_air"] == 0.0
    assert OBJECTS["steel20"] == {"d": 0.020, "m": 0.0329}
