# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p01: the gravity playground. Every preset builds and runs with its conservation checks passing (every check
message, not the last of each: review B6-G7), and three presets run through their decisive events (the binary to its
stop, the hole's capture of a star, the Kerr capture); the Newtonian bodies: a body added "on a circular orbit" is on
the two-body circular orbit for any mass, an object changed at the current moment moves on from there, a collision
merges two bodies (the scene loses one, mass and momentum kept; the merged mass and radius reach the scene and its
file), a refused change leaves the world running; the post-Newtonian binary: the energy it loses against the waves'
flux within the ordering of its reaction series, its detector's strain against the quadrupole formula of a circular
orbit; the black hole: the clocks of the static, ZAMO and orbiting observers against their closed forms, a body that
falls in is captured, a body on a circular orbit stays on it; the scene as a file restores bodies where they were,
also after a capture or a stop, with the observers' clocks."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core import constants as K  # noqa: E402
from lfphys.core.gravity import kerr_newman as KN, pn_binary as PN  # noqa: E402
from p01_gravity import viz as P01  # noqa: E402
from p01_gravity.viz import G_AU, KMS, RS_AU, SCHEMA, YR  # noqa: E402

U = 2.0 ** -53

V = "p01_gravity"


def run(h, t_end, n=200):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + (t_end - t0) * k / n)
        h.runner._frame(0.0)


def failed(h):
    """Every check message that failed, with its time (review B6-G7: reading only the last message of each check hid
    the earlier failures)."""
    return [(c["id"], c["t"], c.get("value"), c.get("tol")) for c in h.of("check") if c.get("ok") is False]


def scene(laws, *objects, **params):
    return {"laws": laws, **params, "scene": {"format": "lfscene", "version": 1, "objects": list(objects)}}


def reload(h):
    """The scene exported and started again as a new world (the player's file)."""
    h.cmd("scene", op="export")
    sc = h.of("scene_export")[-1]["scene"]
    return Harness(V, None, {**sc["laws"], "scene": sc})


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_every_preset_builds_and_keeps_its_conservation_laws(preset):
    if preset == "pythagorean":
        pytest.skip("its close encounters take minutes of computation (a run of its own below)")
    h = Harness(V, preset)
    run(h, h.sim.t + 4.0 * h.sim.default_speed, 120)
    assert not h.errors(), h.errors()
    assert not failed(h), failed(h)
    assert h.checks(), "no running check"
    assert h.of("trail") and h.of("frame")[-1]["ids"]


def test_a_body_on_a_circular_orbit_is_on_the_two_body_circle_for_any_mass():
    """Review B6-G6: "circular" gives the relative speed sqrt(G (M + m)/d) of the two-body circle (d in 3-D), the
    others the reflex, and keeps the system's centre-of-mass velocity: the Earth's relative speed is 29.78 km/s and the
    momentum stays 0; two equal stars stay at their distance d = 1 au to the integration's error (x2 rule against a
    companion with eta/16, plus the rounding of the start, 64 u per step) - the former start gave them e = 0.5; a
    planet off the plane is on a circle in its tilted plane; the preset with five planets does not drift; a body on
    the z-axis through the centre of mass has no defined plane (refused)."""
    h = Harness(V, "sun_earth")
    nb = h.sim.mode.nb
    m_sun, m_e = nb.masses()[:2]
    vrel = np.array(nb.body("o2")["v"]) - np.array(nb.body("o1")["v"])
    assert np.linalg.norm(vrel) == pytest.approx(math.sqrt(G_AU * (m_sun + m_e)), rel=8 * U)
    assert np.linalg.norm(vrel) / KMS == pytest.approx(29.78, abs=0.02)
    assert np.linalg.norm(nb.momentum()) <= 8 * U * m_e * np.linalg.norm(vrel)
    for objs in ([{"type": "star", "values": {"mass": 1.0, "radius": 0.001}},
                  {"type": "star", "values": {"mass": 1.0, "radius": 0.001, "x": 1.0, "vmode": "circular"}}],
                 [{"type": "star", "values": {"mass": 1.0}},
                  {"type": "planet", "values": {"mass": 300.0, "x": 0.6, "z": 0.8}}]):
        h = Harness(V, None, scene("newton", *objs))
        nb = h.sim.mode.nb
        nc = P01.NB.NBody.from_state_dict(nb.state_dict(), eta=nb.eta / 16)
        for t in np.linspace(0.0, 2.0, 9)[1:]:
            nb.advance(t)
            nc.advance(t)
            d = np.linalg.norm(np.diff(nb.positions(), axis=0))
            dc = np.linalg.norm(np.diff(nc.positions(), axis=0))
            assert abs(d - 1.0) <= 2 * abs(d - dc) + 64 * U * nb.diagnostics()["steps"], (objs[1], t, d)
        x, v = np.diff(nb.positions(), axis=0)[0], np.diff(nb.velocities(), axis=0)[0]
        n = np.cross(x, v) / np.linalg.norm(np.cross(x, v))
        assert n[2] > 0 and np.linalg.norm(nb.momentum()) <= 1e-12 * np.sum(nb.masses())
    h = Harness(V, "inner")
    nb = h.sim.mode.nb
    scale = float(np.sum(nb.masses()[:, None] * np.abs(nb.velocities())))
    P0, com0 = np.linalg.norm(nb.momentum()), nb.center_of_mass()[0]
    assert P0 <= 64 * U * scale  # the barycentre at rest: no drift (before: 12.6 m/s, 2.7 au per 1000 years)
    run(h, 10 * YR, 50)
    # it moves at most by the momentum left plus the momentum check's own round-off floor (1e-12 of sum m |v|)
    assert np.linalg.norm(nb.center_of_mass()[0] - com0) <= (P0 + 1e-12 * scale) / nb.total_mass() * 10.0
    # a planet asked for on the z-axis through the centre of mass: no plane is defined there; the palette puts it at
    # the first free point along +x and says so (review UX-ui U4: before, it was refused with that reason)
    h = Harness(V, None, scene("newton", {"type": "star", "values": {"mass": 1.0}}))
    h.cmd("scene", op="add", type="planet", values={"x": 0.0, "y": 0.0, "z": 2.0})
    assert len(h.sim.objects) == 2 and not h.errors(), h.errors()
    b = h.sim.mode.nb.body("o2")
    assert b["x"][0] > 0 and b["x"][2] == 2.0 and any("плоскость" in e["text"] for e in h.of("event")), h.of("event")


def test_a_change_applies_at_the_current_moment_and_a_collision_merges():
    h = Harness(V, "sun_earth")
    run(h, 0.25 * YR, 50)
    h.cmd("scene", op="set", id="o2", values={"x": 0.5, "y": 0.0, "vmode": "manual", "vx": 0.0, "vy": 0.0})
    b = h.sim.mode.nb.body("o2")
    assert b["x"] == [0.5, 0.0, 0.0] and b["v"] == [0.0, 0.0, 0.0]
    p0 = h.sim.mode.nb.momentum().copy()
    m0 = h.sim.mode.nb.masses().sum()
    run(h, h.sim.t + 0.2 * YR, 400)  # the Earth now falls into the Sun from rest
    merges = [e for e in h.of("event") if e.get("kind") == "merge"]
    assert merges and "o2" not in h.sim.objects and len(h.sim.mode.nb.keys) == 1
    assert h.sim.mode.nb.masses().sum() == pytest.approx(m0, rel=1e-15)
    assert np.allclose(h.sim.mode.nb.momentum(), p0, atol=1e-12 * m0)
    assert [o["id"] for o in h.of("scene")[-1]["objects"] if o["type"] != "field"] == ["o1"]


def test_the_scene_file_restores_bodies_where_they_were():
    h = Harness(V, "inner")
    run(h, 0.3 * YR, 60)
    h.cmd("scene", op="export")
    sc = h.of("scene_export")[-1]["scene"]
    h2 = Harness(V, None, {**sc["laws"], "scene": sc})
    for k in h.sim.mode.nb.keys:
        assert h2.sim.mode.nb.body(k)["x"] == h.sim.mode.nb.body(k)["x"]
        assert h2.sim.mode.nb.body(k)["v"] == h.sim.mode.nb.body(k)["v"]
    assert h2.sim.t == pytest.approx(h.sim.t)


def test_the_binary_loses_energy_as_its_waves_carry_it_away():
    h = Harness(V, "pn_inspiral")
    T = h.sim.mode.T
    run(h, 3000 * T, 150)
    assert [c for c in h.of("check") if c["id"] == "balance"] and not failed(h), failed(h)
    r = float(np.linalg.norm(h.sim.mode.bin["st"]["x"]))
    assert r < 20.0  # it came closer
    # the detector's strain against the quadrupole formula of a circular orbit (gw_quadrupole's docstring, Blanchet
    # 2014 Eqs. 322a, 323a at Newtonian order): h+ = -A+ cos 2psi, hx = -Ax sin 2psi with A+ = 2 nu (G m/c^2 R)
    # (1 + cos^2 i) / r, Ax = 4 nu (G m/c^2 R) cos i / r: (h+/A+)^2 + (hx/Ax)^2 = 1 up to O(x) (the orbit is the PN one)
    fr = h.of("frame")[-1]
    hp, hx = fr["probes"]["o2"]["h₊"], fr["probes"]["o2"]["h×"]
    nu, x, ci = 0.25, 1.0 / r, math.cos(math.radians(30.0))
    s0 = h.sim.mode.gm / K.C ** 2 / (400.0 * 3.0856775814913673e22)
    Ap, Ax = 2 * nu * s0 * (1 + ci * ci) * x, 4 * nu * s0 * ci * x
    assert (hp / Ap) ** 2 + (hx / Ax) ** 2 == pytest.approx(1.0, abs=10 * x)


def test_without_radiation_reaction_the_energy_is_conserved():
    h = Harness(V, "pn_inspiral")
    h.cmd("scene", op="set", id="o1", values={"orders": "cons"})
    run(h, h.sim.t + 2000 * h.sim.mode.T, 100)
    assert h.checks()["energy"]["ok"], h.checks()["energy"]


def test_clocks_near_the_hole_against_their_closed_forms():
    h = Harness(V, "kerr_orbits")
    run(h, 200 * h.sim.mode.T, 100)
    a = 0.9
    pr = h.of("frame")[-1]["probes"]
    # a static observer at r = 4 in the equator: dtau/dt = sqrt(1 - 2 r / Sigma), Sigma = r^2 (Q = 0)
    assert pr["o6"]["ход dτ/dt"] == pytest.approx(math.sqrt(1 - 8 / 16), rel=1e-14)
    # a circular prograde orbit at r = 6: dtau/dt = sqrt(1 - 3/r + 2 a r^(-3/2)) / (1 + a r^(-3/2)) (Bardeen, Press &
    # Teukolsky 1972 Eq. 2.13: u^t = (r^(3/2) + a) / (r^(3/4) sqrt(r^(3/2) - 3 r^(1/2) + 2 a)))
    r = 6.0
    ut = (r ** 1.5 + a) / (r ** 0.75 * math.sqrt(r ** 1.5 - 3 * r ** 0.5 + 2 * a))
    assert pr["o7"]["ход dτ/dt"] == pytest.approx(1 / ut, rel=1e-12)
    # the falling body is captured; the circular one keeps its radius; Carter's constant and the shell hold
    assert any(e.get("kind") == "captured" for e in h.of("event"))
    i = h.sim.mode.geo.keys.index("o1")
    assert h.sim.mode.geo.bl()[i, 0] == pytest.approx(3.0, rel=1e-7)
    assert not failed(h)


def test_the_pythagorean_problem_keeps_its_energy_through_close_encounters():
    """Burrau's three bodies: the first close encounters are resolved (energy within the companion-measured error)."""
    h = Harness(V, "pythagorean")
    run(h, 4 * YR, 300)
    assert not failed(h)


# --- review B6-gravity (2026-11-03): its findings, each with its regression test ------------------------------------
def test_the_binary_runs_to_where_its_reaction_series_ends_and_stops_there(monkeypatch):
    """Review B6-G1: below r ~ 9.1 the full equations (2.5PN + 3.5PN reaction, harmonic gauge) gain energy, so the
    preset never reached r_stop = 6 and flew apart. The run now stops at reaction_limit(nu), where the reaction's
    remainder against the 1PN flux equals the 1PN correction it carries (10.59 G m/c^2 for q = 1), with an event that
    says why; every balance message passes its derived tolerance |c1| x/(1 + c1 x) on the way (measured: at most 0.6
    of it). Negative controls: without that stop (the former rule) the balance check fails and the binary has not
    stopped by t = 4.5e4 G m/c^3; a 3.5PN term 1.5 times too strong fails it at once."""
    h = Harness(V, "pn_inspiral")
    T, nu = h.sim.mode.T, 0.25
    r_rr = P01.reaction_limit(nu)
    assert h.sim.mode.bin["r_stop"] == r_rr and 10.5 < r_rr < 10.7
    run(h, 3e4 * T, 600)
    b = h.sim.mode.bin
    assert b["status"] == "stopped" and abs(np.linalg.norm(b["st"]["x"]) - r_rr) <= 1e-9 * r_rr
    ev = [e for e in h.of("event") if e.get("kind") == "merger"]
    assert len(ev) == 1 and "упорядоченным рядом" in ev[0]["text"]
    assert len([c for c in h.of("check") if c["id"] == "balance"]) > 10 and not failed(h), failed(h)
    # the criterion: at r_rr the remainder equals the 1PN correction (Brent to 1e-9 in r); the reaction still
    # dissipates there and has changed sign at r = 9
    d, xx = P01.reaction_on_circle(r_rr, nu)
    c1 = P01.flux_c1(nu)
    assert abs(abs(d - (1 + c1 * xx)) - abs(c1) * xx) <= 1e-8
    assert d > 0 and P01.reaction_on_circle(9.0, nu)[0] < 0
    # D itself against a second route: the energy change of a short integration from the circular state (Richardson
    # on dt and dt/2; the conservative part's contribution starts at rdot = 0 and enters only at O(dt^2))
    for r in (12.0, 8.5):
        st = PN.circular_state(r, nu, P01.ALL_ORDERS, quasi=False)
        E0 = float(PN.energy(st["x"], st["v"], nu, 2))
        dE = []
        for dt in (2.0, 1.0):
            end = PN.integrate(st, dt, nu, P01.ALL_ORDERS, n_out=2, rtol=1e-13)["end"]
            dE.append((float(PN.energy(end["x"], end["v"], nu, 2)) - E0) / dt)
        D_int = -nu * (2 * dE[1] - dE[0])
        dd, x2 = P01.reaction_on_circle(r, nu)
        D_cs = dd * 6.4 * nu * nu * x2 ** 5
        assert abs(D_int - D_cs) <= 2 * abs(dE[1] - dE[0]) * nu + 1e-12 * abs(D_cs), (r, D_int, D_cs)
    # controls
    monkeypatch.setattr(P01, "reaction_limit", lambda nu: 0.0)
    h = Harness(V, "pn_inspiral")
    run(h, 4.5e4 * T, 450)
    assert h.sim.mode.bin["status"] == "running" and failed(h)
    monkeypatch.undo()
    orig = PN.coefficients

    def strong(r, rdot, v2, nu, orders=PN.ORDERS):
        o = PN._orders(orders)
        A, B = orig(r, rdot, v2, nu, tuple(k for k in o if k != 3.5))
        if 3.5 in o:
            A3, B3 = orig(r, rdot, v2, nu, (3.5,))
            A, B = A + 1.5 * A3, B + 1.5 * B3
        return A, B
    monkeypatch.setattr(PN, "coefficients", strong)
    h = Harness(V, "pn_inspiral")
    run(h, 3000 * T, 150)
    assert failed(h)


def test_a_copy_or_a_body_put_on_another_lands_next_to_it_and_says_so():
    """Review UX-ui U4 (before it, B6-G2 refused both): a copy of a massive body "at the current moment" would lie on
    the original (two point masses at one point) and a star asked for exactly on the Sun would be inside it; both now
    go to the first free point along +x, the copy with the original's velocity, and a toast (an event with ``notify``)
    says where and why. Behind it the engine still refuses two point masses at one point and is left exactly as it
    was (its plain-data state unchanged; the world runs on)."""
    import json
    h = Harness(V, "sun_earth")
    run(h, 0.1 * YR, 10)
    nb = h.sim.mode.nb
    e0 = nb.body("o2")
    h.cmd("scene", op="duplicate", id="o2")
    assert not h.errors(), h.errors()
    c = nb.body("o4")
    assert c["v"] == e0["v"] and c["x"][1:] == e0["x"][1:] and c["x"][0] > e0["x"][0]
    assert any(e.get("notify") and "копия" in e["text"] for e in h.of("event"))
    xs = nb.body("o1")["x"]
    h.cmd("scene", op="add", type="star", values={"mass": 1.0, "x": xs[0], "y": xs[1], "z": xs[2]})
    assert not h.errors() and len(nb.keys) == 4
    s5 = nb.body("o5")["x"]
    assert np.linalg.norm(np.subtract(s5, xs)) > P01.CLEAR * 2 * K.R_SUN / K.AU
    assert any(e.get("notify") and "свободное место" in e["text"] for e in h.of("event"))
    before = json.dumps(nb.state_dict())
    with pytest.raises(ValueError, match="same point"):  # the guard behind it: refused, nothing changed
        nb.add(nb.body("o1")["x"], (0, 0, 0), 1.0, 0.0, key="extra")
    assert json.dumps(nb.state_dict()) == before
    n_err = len(h.errors())
    run(h, h.sim.t + 0.1 * YR, 10)
    assert len(h.errors()) == n_err and nb._x.shape[0] == nb._a.shape[0] == len(nb.keys)


def test_palette_places_at_a_free_spot_and_merges_are_toasted():
    """Review UX-ui U4: in the inner Solar System «＋ Звезда» and «＋ Чёрная дыра» at the default (0, 0, 0) landed in the
    Sun (the star merged within a frame, the hole swallowed the Sun) with a line in «События» only. Through ``place``
    (the framework calls it for every palette add) they go to free points and the Sun stays; a body pushed into the Sun
    by hand merges with a toast that names the time since it was added."""
    h = Harness(V, "inner")
    run(h, 0.02 * YR, 4)
    nb = h.sim.mode.nb
    for kind in ("star", "hole", "planet", "test"):
        v = h.sim.place(kind, {})
        h.cmd("scene", op="add", type=kind, values=v)
        assert not h.errors(), h.errors()
    run(h, h.sim.t + 0.001 * YR, 4)
    assert "o1" in nb.keys  # the Sun is still there
    X = nb.positions()
    i = nb.keys.index("o1")
    for j, k in enumerate(nb.keys):
        if k != "o1":
            assert np.linalg.norm(X[j] - X[i]) > 0.01, k
    # a negative control: without ``place`` (the values as the palette sent them before) the star lands in the Sun
    h2 = Harness(V, "inner")
    run(h2, 0.02 * YR, 4)
    h2.sim.mode._blocker = lambda *a, **k: None  # the free-spot test switched off
    h2.cmd("scene", op="add", type="star", values={})
    run(h2, h2.sim.t + 0.01 * YR, 4)
    merges = [e for e in h2.of("event") if e.get("kind") == "merge"]
    assert merges and merges[0].get("notify") and "после добавления" in merges[0]["text"]


def test_the_energy_check_of_a_world_whose_energy_is_zero():
    """Review B6-G3: a star at rest with a test body has total energy exactly 0 (test bodies carry none); the check is
    scaled by kinetic + |potential| energy (0 here, so shown absolute) and no longer divides by zero."""
    h = Harness(V, None, scene("newton", {"type": "star", "values": {"mass": 1.0}},
                               {"type": "test", "values": {"x": 2.0}}))
    run(h, 0.5 * YR, 50)
    e = [c for c in h.of("check") if c["id"] == "energy"]
    assert not h.errors() and e and all(c["ok"] and c["value"] == 0.0 for c in e)


def test_a_merged_body_keeps_its_mass_and_radius_in_the_scene_its_file_and_its_edits():
    """Review B6-G4: two stars merge (1 + 0.5 M_sun; equal-density radius 2^(1/3) R_sun); the kept object's parameters
    show the merged mass and radius, the file restores them (the state carries them: the engine's mass and radius bit
    for bit), and a change of colour leaves the engine untouched (it reset the radius before)."""
    import json
    h = Harness(V, None, scene("newton", {"type": "star", "label": "A", "values": {"mass": 1.0, "radius": 1.0}},
                               {"type": "star", "label": "B", "values": {"mass": 0.5, "radius": 1.0, "x": 0.2,
                                                                         "vmode": "manual"}},
                               {"type": "star", "label": "C", "values": {"mass": 0.1, "radius": 1.0, "x": 30.0,
                                                                         "vmode": "manual"}},
                               collisions="merge"))
    nb = h.sim.mode.nb
    run(h, 0.2 * YR, 100)
    assert nb.keys == ["o1", "o3"] and nb.body("o1")["m"] == 1.5
    vals = h.sim.objects["o1"]["values"]
    assert vals["mass"] == 1.5 and vals["radius"] == pytest.approx(2 ** (1 / 3), rel=8 * U)
    nb2 = reload(h).sim.mode.nb  # the objects are numbered anew in the new world: compare in order
    assert np.array_equal(nb2.masses(), nb.masses()) and np.array_equal(nb2.radii(), nb.radii())
    before = json.dumps(nb.state_dict())
    h.cmd("scene", op="set", id="o1", values={"color": "#ff6b6b"})
    assert json.dumps(nb.state_dict()) == before


def test_a_newtonian_hole_keeps_its_schwarzschild_radius_after_swallowing_a_star():
    """Review B6-G5 (the preset hole_stars through its capture): the hole absorbs the falling star and its radius is
    the Schwarzschild radius of the new mass (it was the star's, 235 times larger); the other stars stay."""
    h = Harness(V, "hole_stars")
    run(h, 0.1 * YR, 200)
    nb = h.sim.mode.nb
    merges = [e for e in h.of("event") if e.get("kind") == "merge"]
    assert len(merges) == 1 and "o4" not in h.sim.objects and nb.keys == ["o1", "o2", "o3"]
    hole = nb.body("o1")
    assert hole["m"] == 1001.0 and hole["radius"] == RS_AU * 1001.0
    assert h.sim.objects["o1"]["values"]["mass"] == 1001.0 and not failed(h), failed(h)


def test_scene_files_after_a_capture_and_a_stop_and_the_observers_clocks():
    """Review B6-G11, G7 (the preset kerr_orbits through the capture of "Падает"): every check message passes (each
    body's drift budget grows as 1/Delta with the shell's terms near the horizon; the former tolerance failed there);
    its file loads - the captured body stays captured at its place with its proper time and drift accounting - and the
    observers' clocks read the same after the file as before; a binary stopped at its end loads stopped."""
    h = Harness(V, "kerr_orbits")
    T = h.sim.mode.T
    run(h, 200 * T, 100)
    assert any(e.get("kind") == "captured" for e in h.of("event")) and not failed(h), failed(h)
    g = h.sim.mode.geo
    assert "captured" in g.status()
    pr = h.of("frame")[-1]["probes"]
    h2 = reload(h)
    g2 = h2.sim.mode.geo
    assert g2.keys == g.keys and g2.status() == g.status()
    assert np.array_equal(g2.bl(), g.bl()) and np.array_equal(g2.proper_time(), g.proper_time())
    c, c2 = g.constants(), g2.constants()
    for k in ("dK", "budget_K", "budget_mu2"):
        assert np.array_equal(c[k], c2[k]), k
    h2.runner._frame(0.0)
    pr2 = h2.of("frame")[-1]["probes"]
    for oid in ("o6", "o7"):
        assert pr2[oid]["часы наблюдателя τ, с"] == pr[oid]["часы наблюдателя τ, с"]
    hb = Harness(V, "pn_inspiral")
    hb.cmd("scene", op="set", id="o1", values={"r_stop": 19.5})
    run(hb, hb.sim.t + 3000 * hb.sim.mode.T, 60)
    assert hb.sim.mode.bin["status"] == "stopped"
    hb2 = reload(hb)
    assert hb2.sim.mode.bin["status"] == "stopped" and not hb2.errors()


def test_kerr_observers_and_bodies_change_only_what_was_changed():
    """Review B6-G12: an observer on a circular orbit added at t = 500 M with phi = 0 is drawn at phi = 0 then (it was
    drawn at Omega t, 36.8 degrees off), its clock starting at 0; B6-G13: a body's colour changes neither its geodesic
    nor its proper time (it restarted it); B6-G19: a circular observer inside the ISCO is refused (not integrated, it
    would stay on an unstable orbit), outside it is accepted."""
    import json
    h = Harness(V, None, scene("kerr", m_hole=10.0, spin=0.9, charge=0.0))
    run(h, 500 * h.sim.mode.T, 10)
    h.cmd("scene", op="add", type="observer", values={"kind": "circular", "r": 6.0, "phi": 0.0})
    h.runner._frame(0.0)
    m, b = [(m, b) for m, b in h.msgs if m.get("type") == "frame"][-1]
    oid = [o["id"] for o in h.sim.objects.values() if o["type"] == "observer"][0]  # the hole is an object too (LB1)
    pos = np.asarray(b["pos"]).reshape(-1, 3)[m["ids"].index(oid)]
    assert abs(math.atan2(pos[1], pos[0])) <= 1e-6 and m["probes"][oid]["часы наблюдателя τ, с"] == 0.0
    h = Harness(V, "kerr_orbits")
    run(h, 50 * h.sim.mode.T, 20)
    before = json.dumps(h.sim.mode.geo.state_dict())
    h.cmd("scene", op="set", id="o2", values={"color": "#ff6b6b"})
    assert json.dumps(h.sim.mode.geo.state_dict()) == before
    # found while processing the review: a refused restart (here a start under the horizon) had already removed the
    # body from the engine, so it vanished while the scene kept it; now every body goes on exactly as it was
    h.cmd("scene", op="set", id="o2", values={"r": 1.0})
    assert "горизонт" in h.errors()[-1] and json.dumps(h.sim.mode.geo.state_dict()) == before
    r_isco = KN.isco(0.9, 0.0, True)
    n = len(h.sim.objects)
    h.cmd("scene", op="add", type="observer", values={"kind": "circular", "r": 0.98 * r_isco})
    assert "ISCO" in h.errors()[-1] and len(h.sim.objects) == n
    h.cmd("scene", op="add", type="observer", values={"kind": "circular", "r": 1.02 * r_isco})
    assert len(h.sim.objects) == n + 1


def test_the_newtonian_frame_stops_growing_when_a_body_is_flung_out():
    """Review B6-G19: a body escaping leaves the frame (it grows to 64 times the scene's size at its last change)
    instead of shrinking the rest to a point; the Sun and a test body at 1 au: the frame stops at 128 au."""
    h = Harness(V, None, scene("newton", {"type": "star", "values": {"mass": 1.0}},
                               {"type": "test", "values": {"x": 1.0, "vmode": "manual", "vy": 60.0}}))
    run(h, 3000 * YR, 60)
    assert np.max(np.abs(h.sim.mode.nb.positions())) > 1e4
    assert h.sim.mode.box_h == 128.0 and h.of("box")[-1]["box"][1][0] == 128.0


# --- trails (review UX-ui U2, UX-3d A13) ------------------------------------------------------------------------------
HERMITE_STEP = math.radians(2.0)  # web/view.js


def _hermite(x0, v0, t0, x1, v1, t1):
    """The view's piece between two trail points (web/view.js ``hermite``): the cubic Hermite curve split into chords of
    at most HERMITE_STEP of turn; returns its points after the first."""
    dt = t1 - t0
    c = np.dot(v0, v1)
    th = math.atan2(float(np.linalg.norm(np.cross(v0, v1))), float(c))
    n = min(24, max(1, math.ceil(th / HERMITE_STEP)))
    u = np.arange(1, n + 1)[:, None] / n
    return ((2 * u ** 3 - 3 * u ** 2 + 1) * x0 + (u ** 3 - 2 * u ** 2 + u) * dt * v0 + (-2 * u ** 3 + 3 * u ** 2) * x1
            + (u ** 3 - u ** 2) * dt * v1)


def _pieces(h, key):
    """The pieces of a body's trail as sent ([(t, x, v)] between breaks), from every trail message after the last reset."""
    pieces, cur = [], []
    for m, b in h.msgs:
        if m.get("type") != "trail":
            continue
        if m.get("reset"):
            pieces, cur = [], []
        off = 0
        for i, k in enumerate(m["ids"]):
            n = m["counts"][i]
            if k == key:
                for j in range(off, off + n):
                    if np.isfinite(b["pts"][j][0]):
                        cur.append((float(b["tt"][j]), b["pts"][j].astype(float), b["vel"][j].astype(float)))
                    elif cur:
                        pieces.append(cur)
                        cur = []
            off += n
    return pieces + ([cur] if cur else [])


def _trail_of(h, key):
    """The longest piece of a body's trail."""
    return max(_pieces(h, key), key=len, default=[])


def _drawn_at(tr, ts):
    """The view's drawn polyline evaluated at the times ts (inside [first, last] kept point): the chord of the Hermite
    piece's tessellation at the time's fraction u of its piece — a point of the drawn line, so its distance to the true
    position bounds the drawn line's deviation there."""
    T = np.array([q[0] for q in tr])
    out = np.empty((len(ts), 3))
    for n, t in enumerate(ts):
        i = min(max(int(np.searchsorted(T, t, side="right")) - 1, 0), len(tr) - 2)
        (t0, x0, v0), (t1, x1, v1) = tr[i], tr[i + 1]
        pts = np.vstack([x0[None], _hermite(x0, v0, t0, x1, v1, t1)])
        u = (t - t0) / (t1 - t0) * (len(pts) - 1)
        k = min(int(u), len(pts) - 2)
        out[n] = pts[k] + (u - k) * (pts[k + 1] - pts[k])
    return out


@pytest.mark.parametrize("factor", [1.0, 10.0])
def test_orbits_are_drawn_smoothly_at_any_speed(factor):
    """The inner Solar System run as the player runs it (frames of speed/20), at the default speed and ten times faster:
    Mercury's trail points are at most TRAIL_TURN (20 degrees) of turn apart and at least 18 per orbit (before: one point
    per frame, 74.8 degrees and 4.8 per orbit at x1, a line back and forth for the Earth at x10), they are the solver's
    own trajectory, and the line the view draws from them (Hermite pieces in chords of 2 degrees) is within 2.5e-4 of
    the orbit's radius of the computed trajectory at 3000 times (the same world advanced in small steps: the motion does
    not depend on how time is sliced). Negative control: the former trail, one point per frame joined by chords, is off
    by more than 0.1 of the radius."""
    h = Harness(V, "inner")
    speed = h.sim.default_speed * factor
    frames = [h.sim.t + speed / 20.0 * k for k in range(1, 41)]
    for t in frames:
        h.run_to(t)
        h.runner._frame(0.0)
    key = "o2"  # Mercury
    tr = _trail_of(h, key)
    V_ = np.array([q[2] for q in tr])
    turns = np.degrees(np.arctan2(np.linalg.norm(np.cross(V_[:-1], V_[1:]), axis=1), np.einsum("ij,ij->i", V_[:-1], V_[1:])))
    t0, t1 = tr[0][0], tr[-1][0]
    orbits = (t1 - t0) / (0.2408 * YR)
    assert turns.max() <= 20.0 + 1e-6 and len(tr) >= 18 * orbits, (turns.max(), len(tr), orbits)
    ref = Harness(V, "inner")
    nb = ref.sim.mode.nb
    ts = np.linspace(t0, t1, 3000)
    tk = np.array([q[0] for q in tr])
    allt = np.unique(np.concatenate([ts, tk]))
    true = {}
    for t in allt:
        nb.advance(t / YR)
        true[t] = nb.positions()[nb.keys.index(key)].copy()
    r = 0.387
    for t, x, _ in tr:  # the kept points are the solver's own positions (float32 in the message)
        assert np.linalg.norm(true[t] - x) <= 1e-6 * r
    dev = np.linalg.norm(_drawn_at(tr, ts) - np.array([true[t] for t in ts]), axis=1)
    assert dev.max() <= 2.5e-4 * r, dev.max() / r
    # negative control: one point per frame joined by chords (the former trail), at the same times
    fr = [t for t in frames if t0 <= t <= t1]
    nb3 = Harness(V, "inner").sim.mode.nb
    per = []
    for t in fr:
        nb3.advance(t / YR)
        per.append(nb3.positions()[nb3.keys.index(key)].copy())
    per = np.array(per)
    chord = np.array([per[min(max(int(np.searchsorted(fr, t, side="right")) - 1, 0), len(fr) - 2)]
                      + (t - fr[min(max(int(np.searchsorted(fr, t, side="right")) - 1, 0), len(fr) - 2)])
                      / (fr[1] - fr[0]) * (per[min(max(int(np.searchsorted(fr, t, side="right")) - 1, 0), len(fr) - 2) + 1]
                                           - per[min(max(int(np.searchsorted(fr, t, side="right")) - 1, 0), len(fr) - 2)])
                      for t in ts if fr[0] <= t <= fr[-1]])
    tt = [t for t in ts if fr[0] <= t <= fr[-1]]
    assert np.max(np.linalg.norm(chord - np.array([true[t] for t in tt]), axis=1)) > 0.1 * r


@pytest.mark.parametrize("preset", ["kerr_orbits", "pn_inspiral", "hole_stars"])
def test_trail_points_of_every_mode_are_within_the_turn_limit(preset):
    """Kerr (sub-steps measured by the turn of each body), the PN binary (points of the step's dense solution) and the
    Newtonian hole with its stars: at the default speed and ten times faster every trail's consecutive points are at most
    TRAIL_TURN apart in direction (a small excess where a sub-step turned more than measured before it)."""
    for factor in (1.0, 10.0):
        h = Harness(V, preset)
        speed = h.sim.default_speed * factor
        for k in range(1, 61):
            h.run_to(h.sim.t + speed / 20.0)
            h.runner._frame(0.0)
        assert not h.errors(), h.errors()
        keys = {k for m in h.of("trail") for k in m["ids"]}
        assert keys
        for key in keys:
            for tr in _pieces(h, key):
                if len(tr) < 3:
                    continue
                V_ = np.array([q[2] for q in tr])
                sp = np.linalg.norm(V_, axis=1)
                # within a piece; a body nearly at rest (the 1000 M☉ hole: below 1 % of its piece's largest speed) has
                # no direction worth the name and moves by nothing on the screen
                ok = (np.minimum(sp[:-1], sp[1:]) > 0.01 * sp.max())
                turns = np.degrees(np.arctan2(np.linalg.norm(np.cross(V_[:-1], V_[1:]), axis=1),
                                              np.einsum("ij,ij->i", V_[:-1], V_[1:])))[ok]
                if len(turns):
                    assert turns.max() <= 26.0, (preset, factor, key, turns.max())


def test_collisions_change_at_the_current_moment_with_the_world_kept():
    """Review UX-ui U12: the collision law is live. Two stars of 20 R☉ on a circle 0.1 au apart overlap for ever with
    «проходят»; switched to «сливаются», they merge at that moment (mass and momentum kept) and the scene file takes the
    law in force. Negative control: a world kept on «проходят» keeps both."""
    objs = ({"type": "star", "values": {"mass": 1.0, "radius": 20.0, "x": -0.05}},
            {"type": "star", "values": {"mass": 1.0, "radius": 20.0, "x": 0.05, "vmode": "circular"}})
    h = Harness(V, None, scene("newton", *objs, collisions="pass"))
    nb = h.sim.mode.nb
    run(h, 0.05 * YR, 10)
    assert len(nb.keys) == 2 and nb.collisions == "pass"
    assert np.linalg.norm(np.diff(nb.positions(), axis=0)) < 2 * 20.0 * K.R_SUN / K.AU  # they overlap
    p0, m0 = nb.momentum().copy(), nb.masses().sum()
    h.set(collisions="merge")
    assert not h.errors(), h.errors()
    assert h.of("live")[-1]["values"]["collisions"] == "merge"
    run(h, h.sim.t + 0.001 * YR, 2)
    assert len(nb.keys) == 1 and nb.masses().sum() == pytest.approx(m0, rel=1e-15)
    assert np.allclose(nb.momentum(), p0, atol=1e-12)
    assert any(e.get("kind") == "merge" and e.get("notify") for e in h.of("event"))
    h.cmd("scene", op="export")
    assert h.of("scene_export")[-1]["scene"]["laws"]["collisions"] == "merge"
    h2 = Harness(V, None, scene("newton", *objs, collisions="pass"))
    run(h2, 0.051 * YR, 12)
    assert len(h2.sim.mode.nb.keys) == 2


def test_trail_velocities_are_the_derivatives_of_the_positions():
    """The velocities the view's Hermite pieces use (U2): Kerr's from the geodesic equations through the drawing map,
    the binary's bodies' from ``pn_binary.directional`` of their positions — against central differences of the
    positions themselves (the second method), to the differences' own truncation."""
    h = Harness(V, "kerr_orbits")
    m = h.sim.mode
    g = m.geo
    rows = [i for i, s in enumerate(g.status()) if s == "active"]
    V0 = m._vel(rows)
    s0 = g.state_dict()
    dt = 1e-3
    g2 = P01.KN.Geodesics.from_state_dict(s0)
    g2.advance(g2.t + dt)
    Xp = g2.cartesian()[rows]
    # a one-sided second-order difference (4 X(dt/2) - 3 X(0) - X(dt)) / dt from the same state
    g3 = P01.KN.Geodesics.from_state_dict(s0)
    g3.advance(g3.t + dt / 2)
    Xh = g3.cartesian()[rows]
    X0 = g.cartesian()[rows]
    fd = (4 * Xh - 3 * X0 - Xp) / dt
    assert np.max(np.linalg.norm(fd - V0, axis=1) / np.linalg.norm(V0, axis=1)) < 1e-5
    h2 = Harness(V, "pn_inspiral")
    pm = h2.sim.mode
    b = pm.bin
    Y0, W, _ = pm._body_states(b["st"]["x"], b["st"]["v"])
    ys = []
    for dtt in (1e-3, 2e-3):
        res = PN.integrate(b["st"], b["st"]["t"] + dtt, b["nu"], b["orders"], n_out=3)
        ys.append(np.stack(PN.body_positions(res["end"]["x"], res["end"]["v"], b["nu"])))
    fd = (4 * ys[0] - 3 * Y0 - ys[1]) / 2e-3
    assert np.max(np.linalg.norm(fd - W, axis=1) / np.linalg.norm(W, axis=1)) < 1e-6
