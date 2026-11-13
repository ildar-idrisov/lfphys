# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u34 orbits: the run as a whole (all presets, checks, causality, live changes, actions, worlds)."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.i18n import render  # noqa: E402
from u34_orbits.viz import MERCURY_GR_ARCSEC_PER_CENTURY, SCHEMA  # noqa: E402

V = "u34_orbits"


def _scale(h):
    """A time scale of the current world's orbit in seconds (the run's own estimate)."""
    s = h.sim
    return (s._period_estimate(s.track) or s.track.dyn) * s.T_s


def _bad_checks(h):
    out = []
    for c in h.checks().values():
        if c.get("ok") is False:
            out.append(c)
        elif c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]:
            out.append(c)
    return out


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_every_preset_runs_and_all_checks_pass(preset):
    h = Harness(V, preset)
    h.run_to(4.5 * _scale(h))
    assert not h.errors(), h.errors()
    assert not _bad_checks(h), [(c["label"], c["value"], c["ref"], c["rel"], c["tol"]) for c in _bad_checks(h)]
    assert h.checks(), "a preset must report checks"
    assert h.of("header")[0]["engine"], "engine modules are listed"


def test_measured_advance_matches_the_exact_one():
    for preset, rel in (("default", 1e-10), ("neutron_star", 1e-10), ("mercury", 2e-5)):
        h = Harness(V, preset)
        h.run_to(3.2 * _scale(h))
        c = [m for m in h.checks().values() if m["id"].endswith(".adv")][0]
        assert abs(c["rel"]) < rel, (preset, c)
        ap = [m for m in h.of("apsis") if m["kind"] == "peri"]
        assert len(ap) >= 3 and ap[-1]["adv"] == pytest.approx(h.sim.info["adv_exact"], rel=max(rel, 1e-9))


def test_mercury_reports_43_arcsec_per_century():
    h = Harness(V, "mercury")
    h.run_to(2.5 * _scale(h))
    c = [m for m in h.checks().values() if m["id"].endswith(".century")][0]
    assert c["ref"] == MERCURY_GR_ARCSEC_PER_CENTURY
    assert c["value"] == pytest.approx(42.98, abs=0.006)
    ids = {m["id"].split(".")[1] for m in h.checks().values()}
    assert {"merc_a", "merc_e", "ppn", "adv", "adv2"} <= ids


def test_nothing_is_revealed_ahead_of_the_world_time():
    h = Harness(V, "default")
    P = _scale(h)
    for T in (0.3 * P, 1.1 * P, 2.7 * P):
        h.run_to(T)
        for m, b in h.msgs:
            if m.get("type") in ("trail", "gtrail"):
                assert float(np.max(b["t"])) <= T * (1 + 1e-12)
            if m.get("type") in ("apsis", "event", "check", "segment"):
                assert m["t"] <= T * (1 + 1e-12)


def test_live_change_restarts_the_body_now():
    h = Harness(V, "default")
    P = _scale(h)
    h.run_to(1.3 * P)
    t_change = h.sim.t
    phi_before = h.sim.track.state(t_change / h.sim.T_s)["phi"]
    h.set(r0=30.0)
    segs = h.of("segment")
    assert len(segs) == 2 and segs[1]["t"] == t_change and segs[1]["launch"]
    assert segs[1]["init"]["r0"] == 30.0 and segs[1]["init"]["phi0"] == pytest.approx(phi_before, abs=1e-12)
    st, _ = h.sim.frame()
    assert st["r"] == pytest.approx(30.0, rel=1e-12) and st["tau"] == 0.0
    assert h.of("live")[-1]["values"]["r0"] == 30.0
    h.run_to(2.5 * P)
    # the old segment's computed future was withdrawn: no samples of segment 0 after the change
    t0 = [b["t"] for m, b in h.msgs if m.get("type") == "trail" and m["seg"] == 0]
    assert max(float(np.max(t)) for t in t0) <= t_change * (1 + 1e-12)
    assert not h.errors()


def test_refused_change_leaves_the_world_as_it_was():
    h = Harness(V, "neutron_star")  # R = 12 km = 5.8 M
    h.run_to(0.5 * _scale(h))
    n_seg = len(h.of("segment"))
    h.set(r0=3.0)
    assert h.errors() and "inside the body" in render(h.errors()[-1])
    assert h.of("live")[-1]["values"]["r0"] == 10.0
    assert len(h.of("segment")) == n_seg
    h.set(speed=1.59)  # still bound? the run says what it is; no error expected
    assert len(h.of("segment")) == n_seg + 1


def test_boost_changes_the_orbit_and_keeps_the_clock():
    h = Harness(V, "default")
    P = _scale(h)
    h.run_to(0.7 * P)
    tg = h.sim.t / h.sim.T_s
    before = h.sim.track.state(tg)
    h.action("boost", dv=0.1)
    seg = h.of("segment")[-1]
    assert seg["launch"] is False and seg["init"]["how"] == "boost"
    assert seg["init"]["v"] == pytest.approx(1.1 * math.hypot(before["v_r"], before["v_phi"]), rel=1e-12)
    st, _ = h.sim.frame()
    assert st["tau"] == pytest.approx(before["tau"] * h.sim.T_s, rel=1e-12)  # the body's clock goes on
    assert st["x"] == pytest.approx(before["x"], rel=1e-12)
    h.run_to(3 * P)
    assert not h.errors() and not _bad_checks(h)
    h.action("boost", dv=2.0)
    assert "Action “Push” not done" in render(h.errors()[-1])  # by its label (review UX-params P20)


def test_newton_world_is_flagged_and_its_ellipse_is_closed():
    h = Harness(V, "newton_ellipse")
    hdr = h.of("header")[0]
    assert hdr["modifications"] and hdr["modifications"][0]["id"] == "gravity"
    ids = [d["id"] for d in hdr["engine"]]
    assert "theories.approx.newton" in ids and "core.gravity.orbit_stream" in ids  # the ghost is GR
    P = h.sim.info["period_ref"]
    h.run_to(3.05 * P)
    c = h.checks()
    adv = [m for m in c.values() if m["id"].endswith(".adv")][0]
    assert adv["ok"] and abs(adv["value"]) * math.pi / 180 / 3600 < 1e-9
    per = [m for m in c.values() if m["id"].endswith(".period")][0]
    assert abs(per["rel"]) < 1e-9
    # back at the start after exactly one Kepler period (the world revealed it): closed orbit
    st = h.sim.track.state(P / h.sim.T_s)
    assert (st["x"], st["y"]) == pytest.approx((20.0, 0.0), abs=1e-7)
    # the GR ghost from the same initial data precesses
    gp = h.of("gapsis")
    assert len(gp) >= 2 and abs(math.atan2(gp[1]["y"], gp[1]["x"])) > 0.1
    assert not _bad_checks(h)


def test_inside_isco_the_perturbed_circle_falls_and_outside_it_stays_bound():
    h = Harness(V, "plunge")
    h.run_to(20 * _scale(h))
    assert any(e.get("kind") == "horizon" for e in h.of("event"))
    out = [m for m in h.checks().values() if m["id"].endswith(".outcome")]
    assert out and out[0]["ok"] and "outside the ISCO" in render(out[0]["note"])
    h2 = Harness(V, "plunge", {"r0": 7.0})
    assert h2.sim.info["kind"] == "bound"
    h2.run_to(5 * _scale(h2))
    assert not any(e.get("kind") == "horizon" for e in h2.of("event"))
    assert not _bad_checks(h2)


def test_radial_fall_is_the_cycloid_in_proper_time():
    h = Harness(V, "radial")
    h.run_to(10 * _scale(h))
    c = [m for m in h.checks().values() if m["id"].endswith(".fall_tau")][0]
    assert abs(c["rel"]) < 1e-10
    st, _ = h.sim.frame()
    assert not st["alive"] and st["status"] == "horizon"


def test_circular_orbit_clock_rate():
    h = Harness(V, "bh_isco")
    h.run_to(3.5 * _scale(h))
    c = {m["id"].split(".")[1]: m for m in h.checks().values()}
    assert abs(c["rate"]["rel"]) < 1e-10 and c["rate"]["ref"] == pytest.approx(math.sqrt(1 - 3 / 6.2), rel=1e-15)
    assert abs(c["period"]["rel"]) < 1e-10


def test_ghost_toggle_reveals_the_other_theory_up_to_now():
    h = Harness(V, "default")
    P = _scale(h)
    h.run_to(1.5 * P)
    T = h.sim.t
    h.set(ghost=True)
    g = [b for m, b in h.msgs if m.get("type") == "gtrail"]
    assert g and float(np.max(np.concatenate([b["t"] for b in g]))) <= T * (1 + 1e-12)
    assert float(np.min(np.concatenate([b["t"] for b in g]))) <= 0.01 * P  # from the segment's start
    assert "theories.approx.newton" in h.sim.engine_modules()
    st, _ = h.sim.frame()
    assert st["ghost"] is not None
    h.set(ghost=False)
    st, _ = h.sim.frame()
    assert st["ghost"] is None and len(h.of("segment")) == 1  # display only: the body was not restarted


def test_surface_impact_on_a_neutron_star():
    h = Harness(V, "neutron_star", {"speed": 0.3})
    h.run_to(10 * h.sim.track.dyn * h.sim.T_s)
    assert any(e.get("kind") == "surface" for e in h.of("event"))
    c = {m["id"].split(".")[1]: m for m in h.checks().values()}
    assert abs(c["impact"]["rel"]) < 1e-9 and abs(c["fall_tau"]["rel"]) < 1e-9


def test_new_world_in_the_same_run():
    h = Harness(V, "default")
    h.run_to(0.5 * _scale(h))
    h.cmd("new_world", preset="newton_ellipse")
    assert len(h.of("header")) == 2 and h.sim.law == "newton"
    h.cmd("new_world", params={"gravity": "GR", "radius_km": 5.0, "mass_msun": 10.0})  # R < 2M: refused
    assert "New world not created" in render(h.errors()[-1])


def test_next_event_jumps_to_the_next_apsis():
    h = Harness(V, "default")
    h.cmd("next_event")
    ap = h.of("apsis")
    assert ap[-1]["kind"] == "apo" and h.sim.t == pytest.approx(ap[-1]["t"], rel=1e-12)


def test_mercury_clock_lag_is_resolved():
    """1 - dtau/dt ~ 6e-8 for Mercury: the trail carries it in double precision, between its values at the apsides."""
    h = Harness(V, "mercury")
    h.run_to(1.2 * _scale(h))
    lag = np.concatenate([b["lag"] for m, b in h.msgs if m.get("type") == "trail"])
    info = h.sim.info
    hi = (info["em1"] / (info["e"] + 1) + 2 / info["r_peri"]) / info["e"]  # 1 - (1 - 2M/r)/e at the turning points
    lo = (info["em1"] / (info["e"] + 1) + 2 / info["r_apo"]) / info["e"]
    assert lag.dtype == np.float64 and 2.9e-8 < lo < hi < 5.2e-8
    assert lag.max() == pytest.approx(hi, rel=1e-9) and lag.min() == pytest.approx(lo, rel=1e-4)
    assert np.all(np.diff(lag[: int(np.argmin(lag))]) <= 1e-22)  # perihelion -> aphelion: the lag decreases
    st, _ = h.sim.frame()
    assert st["deficit"] == pytest.approx(1.0 - st["rate"], rel=1e-7)


def test_frame_fields_survive_the_runner():
    """The runner adds its own frame keys (t, cpu_ms, lag = "cannot keep up"): the view's fields must not collide."""
    h = Harness(V, "mercury")
    h.run_to(0.3 * _scale(h))
    h.runner._frame(1.0)
    f = h.of("frame")[-1]
    assert isinstance(f["lag"], bool)
    assert 2.9e-8 < f["deficit"] < 5.2e-8 and f["rate"] < 1.0


def test_a_launch_at_a_turning_point_is_the_first_apsis_in_both_theories():
    for preset in ("default", "newton_ellipse"):
        h = Harness(V, preset)
        first = h.of("apsis")[0]
        assert first["kind"] == "peri" and first["t"] == 0.0 and first["n"] == 1
    h = Harness(V, "newton_ellipse")
    h.run_to(1.02 * h.sim.info["period_ref"])
    assert any(m["id"].endswith(".adv") for m in h.checks().values())


@pytest.mark.parametrize("law", ["GR", "newton"])
def test_escape_in_both_theories(law):
    h = Harness(V, None, {"gravity": law, "r0": 20.0, "speed": 1.5, "angle": 0.0})
    assert h.sim.info["kind"] == "escape"
    te = h.sim.track.next_event_after(0.0, {"escape"}) * h.sim.T_s
    h.run_to(1.01 * te)
    ev = [e for e in h.of("event") if e.get("kind") == "escape"]
    assert ev and ev[0]["t"] == pytest.approx(te, rel=1e-12)
    st, _ = h.sim.frame()
    assert not st["alive"] and st["r"] == pytest.approx(1000 * 20.0, rel=1e-6)
    assert not h.errors() and not _bad_checks(h)


def test_newton_circle_period_and_conservation():
    h = Harness(V, None, {"gravity": "newton", "r0": 50.0, "speed": 1.0, "angle": 0.0})
    assert h.sim.info["kind"] == "circular"
    h.run_to(3.2 * _scale(h))
    c = {m["id"].split(".")[1]: m for m in h.checks().values()}
    assert abs(c["period"]["rel"]) < 1e-9 and c["energy"]["ok"] and c["angmom"]["ok"]


# --- internal physics review 2026-10-23 (V4-1 ... V4-16): each test reuses the reviewer's failing inputs --------------
def _turn(h):
    return 2 * math.pi * h.sim.init["r0"] ** 1.5 * h.sim.T_s


@pytest.mark.parametrize("preset,params,dv,kind,rp,ra", [
    ("bh_isco", {}, -0.05, "plunge", None, 6.2),                       # was «escape»
    ("bh_isco", {}, +0.05, "bound", 6.2, 14.65298876),                  # was circular / r_peri 3.697
    ("default", {"r0": 20.0, "speed": 1.0}, +0.05, "bound", 20.0, 26.02189745),  # was r_peri 2.4297, r_apo 20
    ("default", {"r0": 20.0, "speed": 1.0}, -0.05, "bound", 15.50631304, 20.0),  # was circular or escape
])
def test_v4_1_boost_of_a_circle_gets_the_right_kind(preset, params, dv, kind, rp, ra):
    for frac in (0.37, 0.61, 1.13):
        h = Harness(V, preset, params)
        h.run_to(frac * _turn(h))
        h.action("boost", dv=dv)
        seg = h.of("segment")[-1]
        assert seg["kind"] == kind and seg["init"]["v_r"] == 0.0
        if rp is not None:
            assert seg["r_peri"] == pytest.approx(rp, rel=1e-9)
        assert seg["r_apo"] == pytest.approx(ra, rel=1e-9)


@pytest.mark.parametrize("law,r0,k,angle", [("GR", 3.5, 0.95, 45.0), ("GR", 20.0, 1.6, 89.0),
                                            ("newton", 20.0, 1.6, 89.9999), ("newton", 20.0, 1.5, 89.99999)])
def test_v4_2_outward_unbound_launch_is_an_escape(law, r0, k, angle):
    h = Harness(V, "default", {"gravity": law, "r0": r0, "speed": k, "angle": angle})
    assert h.sim.info["kind"] == "escape"
    assert "periapsis" not in render(h.of("event")[0]["text"])  # the periapsis behind the body is not quoted
    te = h.sim.track.next_event_after(0.0, {"horizon", "escape", "center", "surface"})
    h.run_to(1.0001 * te * h.sim.T_s)
    assert h.sim.track.end_event["kind"] == "escape"
    out = [m for m in h.checks().values() if m["id"].endswith(".outcome")][0]
    assert out["ok"]


@pytest.mark.parametrize("r0", [1e6, 1e8])
def test_v4_3_far_radial_fall_stops_at_the_horizon_in_the_run(r0):
    """Before: from 1e8 M the run stopped at r = 1.99974 M and showed v = 1.0000655 c, dtau/dt < 0."""
    h = Harness(V, "radial", {"r0": r0})
    te = h.sim.track.next_event_after(0.0, {"horizon"})
    h.run_to(1.001 * te * h.sim.T_s)
    h.runner._frame(1.0)
    f = h.of("frame")[-1]
    assert f["r"] == pytest.approx(2.0 / (1 - 1e-6), rel=1e-12) and f["v"] < 1.0 and f["rate"] > 0.0
    rr = np.concatenate([b["r"] for m, b in h.msgs if m.get("type") == "trail"])
    assert rr.min() >= 2.0 / (1 - 1e-6) * (1 - 1e-12)
    assert not _bad_checks(h)


@pytest.mark.parametrize("angle", [-85.0, -89.0, -89.9, -89.99])
def test_v4_4_newton_eccentric_orbits(angle):
    """Before: -360 deg/orbit «advance» from -85 deg, no apsides at -89.99 deg, energy drift beyond the tolerance."""
    h = Harness(V, "newton_ellipse", {"angle": angle, "speed": 1.0, "ghost": False})
    h.run_to(3.3 * h.sim.info["period_ref"])
    assert not _bad_checks(h), [(c["id"], c["value"], c["tol"]) for c in _bad_checks(h)]
    ap = [m for m in h.of("apsis") if m["kind"] == "peri"]
    if h.sim.info["kind"] == "bound":
        assert len(ap) >= 3 and all(abs(a["adv"]) < 1e-6 for a in ap[1:])


def test_v4_4_newton_radial_fall_and_boost_state():
    h = Harness(V, "newton_ellipse", {"speed": 0.0, "ghost": False})  # radial fall into the point mass
    h.run_to(2.0 * h.sim.track.dyn * h.sim.T_s)
    assert h.sim.track.end_event and not _bad_checks(h)
    h = Harness(V, "newton_ellipse", {"ghost": False})
    tr0 = h.sim.track
    h.run_to(0.71 * h.sim.info["period_ref"])
    h.action("boost", dv=0.0)
    tr1 = h.sim.track
    assert tr1.E0 == pytest.approx(tr0.E0, rel=1e-9) and tr1.h0 == pytest.approx(tr0.h0, rel=1e-9)  # was 2.4e-7


@pytest.mark.parametrize("preset,params,boost", [
    ("default", {"r0": 20.0, "speed": 1.0000001, "angle": 0.0}, None),
    ("default", {"r0": 20.0, "speed": 1.0, "angle": 1e-5}, None),
    ("bh_isco", {}, 1e-9),
    ("newton_ellipse", {"r0": 50.0, "speed": 1.0000001, "ghost": False}, None),
    ("newton_ellipse", {"r0": 50.0, "speed": 1.0000004, "ghost": False}, None),
])
def test_v4_5_nearly_circular_orbits(preset, params, boost):
    h = Harness(V, preset, params)
    if boost is not None:
        h.run_to(0.37 * _turn(h))
        h.action("boost", dv=boost)
    h.run_to(h.sim.t + 3.3 * _turn(h))
    assert not _bad_checks(h), [(c["id"], c["value"], c["ref"], c["rel"], c["tol"]) for c in _bad_checks(h)]


@pytest.mark.parametrize("r0", [3.0001, 4.0, 4.5, 5.0])
def test_v4_5_unstable_circles(r0):
    """Before: rate/period rows failed at 2e-10...7e-8 once rounding grew; the fall time was compared with a
    divergent quadrature (rel 1.07-1.11)."""
    h = Harness(V, "bh_isco", {"r0": r0})
    assert h.sim.info["kind"] == "circular"
    h.run_to(40 * _turn(h))
    assert not _bad_checks(h), [(c["id"], c["value"], c["ref"], c["rel"], c["tol"]) for c in _bad_checks(h)]
    ft = [m for m in h.checks().values() if m["id"].endswith(".fall_tau")]
    assert all(c["ref"] is None for c in ft)


@pytest.mark.parametrize("law,k", [("GR", 1.3416), ("newton", 1.4141)])
def test_v4_6_bound_orbit_beyond_1000_r0_is_not_an_escape(law, k):
    h = Harness(V, "default", {"gravity": law, "r0": 20.0, "speed": k})
    assert h.sim.info["kind"] == "bound" and h.sim.info["r_apo"] > 2e4
    te = h.sim.track.next_event_after(0.0, {"apo"})
    h.run_to(1.01 * te * h.sim.T_s)
    assert h.sim.track.end_event is None
    apo = [m for m in h.of("apsis") if m["kind"] == "apo"][-1]
    # Newton: r_apo/r_peri ~ 6e3, E ~ -8e-6: the apoapsis moves with the measured energy drift (dr_a/r_a ~ dE/E)
    drift = h.sim.track.drift["E"] if law == "newton" else 0.0
    assert apo["r"] == pytest.approx(h.sim.info["r_apo"], rel=1e-9 + 2 * drift)


def test_v4_7_turning_point_references_from_e2m1():
    h = Harness(V, "mercury")
    h.run_to(1.2 * _scale(h))
    c = {m["id"].split(".")[1]: m for m in h.checks().values()}
    for k in ("r_peri", "r_apo"):
        assert c[k]["tol"] < 2e-11 and abs(c[k]["rel"]) < 1e-12  # was rel 1.1e-8, 1.7e-8 under tol 1.7e-7
    h = Harness(V, "bh_isco")  # near the ISCO the event was right and the reference 5.3e-9 off
    h.run_to(0.37 * _turn(h))
    h.action("boost", dv=1e-7)
    h.run_to(h.sim.t + 3.3 * h.sim._period_estimate(h.sim.track) * h.sim.T_s)
    assert not _bad_checks(h)


def test_v4_8_v4_9_v4_10_mercury_rows():
    h = Harness(V, "mercury")
    h.run_to(2.2 * _scale(h))
    c = {m["id"].split(".")[1]: m for m in h.checks().values()}
    g = h.sim.S["second"]
    floor = g["binding_floor"]
    assert 5e-9 < floor < 1e-7  # eps/|e^2 - 1| for Mercury: 8.6e-9
    for k in ("drift_e", "drift_n"):  # relative to the binding energy now (was relative to e ~ 1)
        assert c[k]["ok"] and c[k]["tol"] == pytest.approx(max(1e-9, 100 * floor))
    ap = {m["kind"]: m for m in h.of("apsis") if m["n"] == 1}
    rp, ra = ap["peri"]["r"], ap["apo"]["r"]
    assert c["merc_a"]["value"] == pytest.approx(0.5 * (rp + ra) * h.sim.M_m / 1.495978707e11, rel=1e-15)
    assert c["merc_e"]["value"] == pytest.approx((ra - rp) / (ra + rp), rel=1e-15)  # from the run's own events
    assert c["ppn"]["ref"] * math.pi / 180 / 3600 == pytest.approx(h.sim.info["adv_series2"], rel=1e-12)


def test_v4_11_radial_period_has_a_reference():
    h = Harness(V, "default")
    h.run_to(3.2 * _scale(h))
    c = [m for m in h.checks().values() if m["id"].endswith(".period")][0]
    assert c["ref"] is not None and abs(c["rel"]) < 1e-9


def test_v4_12_outcome_can_fail():
    h = Harness(V, "plunge")
    h.sim._check_outcome("escape")  # a plunge that «escaped» would be a contradiction
    c = [m for m in h.checks().values() if m["id"].endswith(".outcome")][0]
    assert c["ok"] is False


def test_v4_13_newton_rows_show_their_verdict_tolerance():
    h = Harness(V, "newton_ellipse")
    h.run_to(2.2 * h.sim.info["period_ref"])
    for k in ("energy", "angmom"):
        c = [m for m in h.checks().values() if m["id"].endswith("." + k)][0]
        assert c["ok"] == (c["value"] <= c["tol"])


def test_v4_14_ghost_end_reported_once():
    h = Harness(V, "radial")
    h.set(ghost=True)
    h.run_to(10 * _scale(h))
    h.set(ghost=False)
    h.set(ghost=True)
    h.run_to(h.sim.t * 1.01)
    ends = [e for e in h.of("event") if e.get("kind") == "ghost"]
    assert len(ends) == 1


def test_v4_15_view_label():
    js = (Path(__file__).resolve().parents[1] / "web" / "view.js").read_text()
    assert 't("at the horizon (r − 2M = 2·10⁻⁶ M; beyond it t → ∞)")' in js and "beyond the horizon" not in js


def test_v4_16_late_ghost_does_not_block():
    """Before: switching the ghost on after 1000 orbits blocked the worker 24 s (default preset)."""
    import time as _time
    h = Harness(V, "default")
    P = _scale(h)
    h.run_to(300 * P)
    w0 = _time.monotonic()
    h.set(ghost=True)
    assert _time.monotonic() - w0 < 1.0
    assert not h.sim.ghost.caught_up
    assert any("computed from the start of the segment in parts" in render(m["text"]) for m in h.of("notice"))
    for _ in range(2000):  # the world goes on; the ghost catches up in slices
        if h.sim.ghost.caught_up:
            break
        h.run_to(h.sim.t + 0.01 * P)
    assert h.sim.ghost.caught_up
    g = np.concatenate([b["t"] for m, b in h.msgs if m.get("type") == "gtrail"])
    assert float(g.max()) <= h.sim.t * (1 + 1e-12) and float(g.max()) > 0.99 * h.sim.t
