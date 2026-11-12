# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v09: Thomas-Wigner precession in 3-D. Every preset builds and passes its checks; the result is revealed only when
the run's time reaches the loop's closure; loops in a plane against their closed forms in any orientation (Thomas's
2 pi (gamma - 1), the circle's area, the triangle's and the polygon's); the double cover (a turn by 2 pi: gyroscopes
back, spinor sign -1); non-planar loops reduce to planar ones at chi = 0; the trajectory in ordinary space of uniform
circular motion; the field of three-burn loops and its slices against Gauss-Bonnet; the slice planes of the shared
environment (any orientation, three at most, kept in a new world, auto coarse, none in ordinary space)."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core import lorentz as LZ  # noqa: E402
from lfphys.core import spin_transport as T  # noqa: E402
from v09_thomas_3d.engine import loops as LP  # noqa: E402
from v09_thomas_3d.viz import SCHEMA  # noqa: E402

V = "v09_thomas_3d"
SMALL = {"ngrid": 48}


def failed(h):
    return [c["id"] for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]


def finish(h):
    h.run_to(h.sim.T_end * 1.0001)
    return h


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_presets_build_close_and_pass(preset):
    h = finish(Harness(V, preset, SMALL))
    assert not h.errors() and not failed(h), (h.errors(), failed(h))
    ids = set(h.checks())
    assert {"closed", "roundoff", "holonomy", "fuel_bound"} <= ids
    hdr = h.of("header")[0]
    assert ("holonomy_su2" in ids) == hdr["loop"]["planar"] == ("holonomy_accumulated" in ids)
    assert len(h.of("holonomy")) == 1 and h.of("arrow")
    vel = hdr["space"] == "velocity"
    assert bool(h.of("volume")) == vel and bool(h.of("slice")) == vel
    assert hdr["scene3d"]["planes"]["max"] == (3 if vel else 0)
    if vel:
        assert "field_exact" in ids and "plane_exact_1" in ids


def test_the_result_waits_for_the_closure():
    """Nothing about the result before the craft is back at rest (review B2-2: neither the rotation nor the duration,
    the proper time at the end or the largest gamma; the speed comes from the programme); the path is revealed only up
    to the run's time."""
    h = Harness(V, "triangle", SMALL)
    sim = h.sim
    hdr = h.of("header")[0]
    assert not {"T_end", "tau_end", "eta_max"} & set(hdr["loop"])
    assert sim.default_speed == pytest.approx(sim.mv.fuel() / sim.accel * 365.25 * 86400 / 20.0)
    h.run_to(0.5 * sim.T_end)
    assert not h.of("holonomy") and "holonomy" not in h.checks() and not h.of("arrow")
    n = sum(m["count"] for m in h.of("path"))
    k = int(np.searchsorted(sim.tt, 0.5 * sim.T_end, side="right"))
    assert max(m["from"] + m["count"] for m in h.of("path")) == k and n >= k
    assert len([m for m in h.of("event") if m.get("kind") == "burn"]) == 2  # the third burn starts later
    finish(h)
    r = h.of("holonomy")[0]
    assert r["T_end"] == pytest.approx(sim.T_end / (365.25 * 86400)) and r["tau_end"] > 0 and r["gamma_max"] > 1
    assert [m for m in h.of("event") if m.get("kind") == "closed"]


def test_the_lab_box_grows_with_the_path():
    """In ordinary space the box starts from an input scale (c^2/a) and doubles as the revealed path nears its edge; it
    never frames the future trajectory in advance (review B2-2)."""
    h = Harness(V, None, {"space": "lab", "loop": "thomas", "rho": 1.2, "turns": 2})
    sim = h.sim
    h0 = 1.0 / sim.accel
    assert h.of("header")[0]["scene3d"]["box"][1][0] == pytest.approx(h0)
    P = sim.track.x[:, 1:]
    for frac in (0.2, 0.5, 1.0001):
        h.run_to(frac * sim.T_end)
        k = int(np.searchsorted(sim.tt, frac * sim.T_end, side="right"))
        half = h.of("box")[-1]["box"][1][0] if h.of("box") else h0
        assert np.max(np.abs(P[:k])) <= 0.9 * half  # the revealed path fits
        assert half <= max(h0, 2 / 0.9 * np.max(np.abs(P[:k])))  # and the box is not bigger than needed


@pytest.mark.parametrize("loop,extra,ref", [
    ("thomas", {"rho": 0.6, "turns": 2}, lambda p: 2 * 2 * math.pi * (math.cosh(0.6) - 1)),
    ("circle", {"rho": 1.1}, lambda p: float(T.circle_area(1.1))),
    ("polygon", {"rho": 0.9, "sides": 5}, lambda p: T.regular_polygon_area(5, 0.9)),
])
@pytest.mark.parametrize("normal", [(90.0, 90.0), (0.0, 0.0), (37.0, 211.0)])
def test_planar_loops_in_any_plane(loop, extra, ref, normal):
    """The gyroscopes turn by the enclosed area about the loop's normal, against the sense of the loop, in any
    orientation of the loop's plane; the spinor by exp(+i A n.sigma / 2)."""
    p = {**SMALL, "loop": loop, "nth": normal[0], "nph": normal[1], **extra}
    h = finish(Harness(V, None, p))
    hol = h.sim.hol
    A = ref(p)
    n = np.asarray(h.of("header")[0]["loop"]["normal"])
    assert np.max(np.abs(hol["R"] - LZ.rot3(n, -A))) < 1e-11
    assert np.max(np.abs(hol["su2"] - LZ.sl2_rotation(n, -A))) < 1e-11


@pytest.mark.parametrize("loop", ["thomas", "circle", "triangle", "polygon", "crown", "helix", "seam"])
def test_the_edges_of_the_schema(loop):
    """The largest loops the schema allows (rho 3, six repetitions, 24 sides, chi 80) and the smallest (rho 0.05, six
    repetitions): either refused with the reason (too close to light for float64) or every check passes; the measured
    round-off stays far below the alarm level; loops flown m times pass through rest between the repetitions (m times
    the area)."""
    small = finish(Harness(V, None, {**SMALL, "loop": loop, "rho": 0.05, "turns": 6, "nth": 63.0, "nph": 17.0}))
    assert not failed(small) and small.sim._round_est() * 20 <= small.sim._round_bound()
    p = {**SMALL, "loop": loop, "rho": 3.0, "turns": 6, "sides": 24, "chi": 80.0, "alpha": 170.0}
    try:
        h = finish(Harness(V, None, p))
    except AssertionError:
        raise
    except Exception as e:  # a refused world
        assert "скорости света" in str(e) and loop == "helix", e
        return
    assert not h.errors() and not failed(h), (h.errors(), failed(h))
    assert h.sim._round_est() * 20 <= h.sim._round_bound()  # an alarm level, measured >= 46 below it
    if h.sim.info["planar"]:
        one = finish(Harness(V, None, {**p, "turns": 1}))
        assert h.sim.info["reference"] == pytest.approx(6 * one.sim.info["reference"], rel=1e-14)


@pytest.mark.parametrize("loop", ["triangle", "polygon"])
def test_large_planar_loops_in_tilted_planes(loop):
    """Review B2-1: large triangles and polygons (rho 2 - 3, repeated) in tilted planes pass their checks: the burns are
    built in extended precision, so the loop flown stays in its plane to the flight's own round-off."""
    rng = np.random.default_rng(11)
    for _ in range(6):
        p = {"space": "lab", "loop": loop, "rho": float(rng.uniform(2.0, 3.0)), "turns": int(rng.integers(1, 5)),
             "sides": int(rng.integers(3, 25)), "alpha": float(rng.uniform(20, 160)),
             "nth": float(rng.uniform(10, 170)), "nph": float(rng.uniform(0, 360))}
        h = finish(Harness(V, None, p))
        assert not failed(h), (p, failed(h))
        c = h.checks()
        assert c["holonomy_accumulated"]["ok"] and abs(c["holonomy_accumulated"]["value"] - h.sim.info["reference"]) \
            <= 8 * h.sim._round_est() + 1e-12 * (1 + h.sim.info["reference"])


def test_rotation_per_fuel_of_repeated_nonplanar_loops():
    """Review B2-3: for a non-planar loop flown m times the comparison with the bound uses one loop (its SU(2) angle
    and its fuel), the same for any m."""
    one = finish(Harness(V, None, {**SMALL, "loop": "crown", "turns": 1}))
    three = finish(Harness(V, None, {**SMALL, "loop": "crown", "turns": 3}))
    assert three.of("holonomy")[0]["per_bound"] == pytest.approx(one.of("holonomy")[0]["per_bound"], rel=1e-9)
    assert three.of("holonomy")[0]["per_fuel_L"] == pytest.approx(one.sim.mv.fuel(), rel=1e-12)


def test_triangle_is_the_wigner_rotation():
    p = {**SMALL, "loop": "triangle", "rho": 1.3, "alpha": 70.0}
    h = finish(Harness(V, None, p))
    e1, e2, n = LP.base_frame(90.0, 90.0)
    u = math.tanh(1.3) * e1
    v = math.tanh(1.3) * (math.cos(math.radians(70)) * e1 + math.sin(math.radians(70)) * e2)
    _, _, _, th = LZ.wigner_rotation(u, v)
    assert h.sim.hol["angle"] == pytest.approx(float(th), abs=1e-12)
    assert float(th) == pytest.approx(float(LZ.wigner_angle_closed_form(u, v)), abs=1e-13)


def test_double_cover():
    """A circle of area 2 pi (cosh rho = 2): the gyroscopes come back (SO(3) angle 0) but the spinor changes sign."""
    h = finish(Harness(V, "spin_flip", SMALL))
    r = h.of("holonomy")[0]
    assert r["angle"] < 1e-8 and r["su2_angle"] == pytest.approx(2 * math.pi, abs=1e-8) and r["spinor_sign"] == -1
    # two such circles: the spinor is back too
    h2 = finish(Harness(V, None, {**SMALL, "loop": "circle", "rho": math.acosh(2.0), "turns": 2}))
    assert h2.of("holonomy")[0]["su2_angle"] < 1e-7 and h2.of("holonomy")[0]["spinor_sign"] == 1


@pytest.mark.parametrize("loop,planar", [("crown", "polygon"), ("helix", "circle"), ("seam", None)])
def test_nonplanar_loops_at_chi_zero_are_planar(loop, planar):
    """At chi = 0 the crown is the regular polygon, the helix the circle through rest (plus a return burn of zero
    rapidity) and the seam the regular 96-gon (its area by the closed form): the same rotation as the planar loop;
    out of the plane the rotation differs and its axis leaves the plane's normal."""
    a = finish(Harness(V, None, {**SMALL, "loop": loop, "chi": 0.0, "rho": 0.9, "sides": 6}))
    n = np.asarray(a.of("header")[0]["loop"]["normal"])
    if planar:
        R = finish(Harness(V, None, {**SMALL, "loop": planar, "rho": 0.9, "sides": 6})).sim.hol["R"]
    else:
        R = LZ.rot3(n, -T.regular_polygon_area(LP.SEAM_BURNS, 0.9))
    assert np.max(np.abs(a.sim.hol["R"] - R)) < 1e-11
    c = finish(Harness(V, None, {**SMALL, "loop": loop, "chi": 40.0, "rho": 0.9, "sides": 6}))
    assert np.max(np.abs(c.sim.hol["R"] - R)) > 1e-3
    assert abs(c.sim.hol["axis"] @ n) < 1 - 1e-6


def test_seam_converges_to_the_smooth_curve():
    h = finish(Harness(V, "seam", SMALL))
    d = h.checks()["seam_convergence"]["value"]
    assert 0 < d < 2e-3


def test_uniform_circular_motion_in_ordinary_space():
    """The turn of the Thomas loop is uniform circular motion: constant speed tanh(rho), radius
    gamma^2 beta^2 c^2 / a about a fixed centre; the out and back burns are hyperbolic motion."""
    rho, g_ = 0.7, 2.0
    h = finish(Harness(V, None, {"space": "lab", "loop": "thomas", "rho": rho, "accel_g": g_}))
    sim, tr = h.sim, h.sim.track
    turn = tr.piece == 1
    sp = np.linalg.norm(tr.beta[turn], axis=1)
    assert np.max(np.abs(sp - math.tanh(rho))) < 1e-12
    a = g_ * LP.G_LY
    r = math.sinh(rho) ** 2 / a  # gamma^2 beta^2 c^2 / a with c = 1
    P = tr.x[turn, 1:]
    c = P.mean(axis=0)  # whole revolutions sampled uniformly in time: the centre
    assert np.max(np.abs(np.linalg.norm(P - c, axis=1) - r)) < 1e-6 * r
    assert sim.T_end == pytest.approx(tr.x[-1, 0] * 365.25 * 86400, rel=1e-15)  # the world clock counts seconds
    # the out burn: hyperbolic motion, x = (cosh rho - 1)/a, t = sinh rho / a
    end1 = sim.mv.pieces[0]
    i1 = np.flatnonzero(tr.piece == 0)[-1]
    assert tr.x[i1, 0] == pytest.approx(math.sinh(end1.rapidity) / a, rel=1e-13)


def test_field_and_slices_against_gauss_bonnet():
    """The field of three-burn loops: theta by the engine's matrices equals the triangle's area at points of every
    slice; the ratio to the planar bound stays below 1 (triangles are planar loops)."""
    h = Harness(V, None, {**SMALL, "field": "theta"})
    for pid, n in ((1, (0.3, 0.9, -0.2)), (2, (1.0, 0.0, 0.0)), (3, (0.0, 0.0, 1.0))):
        h.cmd("view", op="plane", id=pid, origin=[0.1, 0.0, 0.05], normal=list(n))
        sl = h.of("slice")[-1]
        assert sl["id"] == pid and sl["verify"]["ok"] and sl["verify"]["points"] == 3
        s = h.sim.slices[pid]
        assert np.isfinite(s["th"]).sum() > 1000  # the ball's part of the plane is computed
    assert not failed(h)
    with pytest.raises(Exception):
        h.sim.view({"op": "plane", "id": 4, "normal": [0, 0, 1]})
    vol = h.of("volume")[0]  # review B2-4: the volume carries its own scale for previews read from it
    assert vol["quantity"]["peak"] == pytest.approx(h.sim.field_peak * math.pi)
    hr = Harness(V, None, {**SMALL, "field": "ratio", "eta_u": 1.5})
    sl = hr.sim.slices[1]
    assert np.nanmax(sl["val"]) < 1.0 and np.nanmax(sl["val"]) > 0.3


def test_planes_kept_in_a_new_world_and_auto_is_coarse():
    h = Harness(V, "triangle", SMALL)
    h.cmd("view", op="plane", id=2, normal=[0.2, 0.3, 0.9], origin=[0.0, 0.0, 0.3])
    before = {p["id"]: p["normal"] for p in h.of("planes")[-1]["planes"]}
    h.cmd("new_world", params={**SMALL, "loop": "circle"})
    after = {p["id"]: p["normal"] for p in h.of("planes")[-1]["planes"]}
    assert after.keys() == before.keys() and np.allclose(after[2], before[2])
    h.cmd("view", op="plane", id=2, auto=True, speed=0.5)  # 0.5 c per year of world time
    n0 = len(h.of("slice"))
    h.run_to(h.sim.t + 3.0 * 365.25 * 86400)
    moved = h.of("slice")[n0:]
    assert moved and all(m["coarse"] for m in moved)
    lab = Harness(V, "lab")
    with pytest.raises(Exception):
        lab.sim.view({"op": "plane", "id": 1})
    assert not lab.of("planes") or not lab.of("planes")[-1]["planes"]


def test_frames_carry_the_gyroscopes():
    h = Harness(V, "thomas", SMALL)
    h.run_to(0.3 * h.sim.T_end)
    f, _ = h.sim.frame()
    O = np.asarray(f["O"]).reshape(3, 3)
    assert np.allclose(O @ O.T, np.eye(3), atol=1e-12)
    assert np.allclose(np.asarray(f["spin"]), O @ h.sim.spin0, atol=1e-15)
    n, th = LZ.axis_angle(O)
    assert f["rot_angle"] == pytest.approx(float(th), abs=1e-15)
