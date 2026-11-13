# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u31 physics: every engine route against an independent closed form or a second method."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core.constants import AU, C, GM_SUN, R_SUN  # noqa: E402
from lfphys.core.gravity import rays as light  # noqa: E402
from lfphys.core.gravity import schwarzschild as S  # noqa: E402
from lfphys.i18n import render  # noqa: E402
from lfphys.laws.light import Laws  # noqa: E402
from lfphys.theories.alternatives import newton_light  # noqa: E402
from lfphys.theories.approx import newton as kepler  # noqa: E402
from u31_light_travel.engine import checks  # noqa: E402

V = "u31_light_travel"


# --- frames of the laws -------------------------------------------------------------------------------
@pytest.mark.parametrize("v", [[0.3 * C, 0.0], [0.5 * C, -0.6 * C], [0.0, -0.9 * C]])
def test_lorentz_matrix_preserves_minkowski_metric(v):
    M = Laws("SR", "none").frame_matrix(v)
    eta = np.diag([1.0, -1.0, -1.0])
    assert np.allclose(M.T @ eta @ M, eta, atol=1e-12)
    # the frame's own worldline x = v t maps to x' = 0
    ev = np.array([C * 2.0, 2.0 * v[0], 2.0 * v[1]])
    assert np.allclose((M @ ev)[1:], 0.0, atol=1e-6)


def test_aberrated_light_keeps_speed_c():
    laws = Laws("SR", "none")
    n = light.unit_fan(64)
    u = laws.emit_velocities(n, [0.8 * C, 0.1 * C])
    assert np.allclose(np.linalg.norm(u, axis=1), C, rtol=1e-14)
    # forward beaming: more rays forward than backward
    assert np.sum(u[:, 0] > 0) > 48


# --- Schwarzschild ------------------------------------------------------------------------------------
@pytest.mark.parametrize("r0", [3.2, 4.0, 7.0, 30.0, 1e3])
def test_quadrature_deflection_matches_darwin(r0):
    rs = 1.0
    b = checks.impact_from_closest(r0, rs)
    assert S.deflection_from_quadrature(b, rs) == pytest.approx(checks.darwin_deflection(r0, rs), rel=1e-10)


def test_weak_field_limit():
    rs, b = 1.0, 1e6
    d = S.deflection_from_quadrature(b, rs)
    assert d == pytest.approx(2 * rs / b + 15 * math.pi / 16 * (rs / b) ** 2, rel=1e-6)


def test_radial_connection_time():
    rs, c = 1.0, 1.0
    img = S.connect((5.0, 0.0), (500.0, 0.0), rs, c, rs)
    assert img[0]["branch"] == "out"
    assert img[0]["dt"] == pytest.approx(checks.radial_light_time(5.0, 500.0, rs, c), rel=1e-13)


def test_two_images_symmetric_lens():
    rs, c = 1.0, 1.0
    img = S.connect((-300.0, 0.0), (300.0, 0.0), rs, c, rs)
    # exact symmetry: both images arrive together, impact parameters equal
    assert len(img) >= 2
    assert img[0]["dt"] == pytest.approx(img[1]["dt"], rel=1e-12)
    assert img[0]["b"] == pytest.approx(img[1]["b"], rel=1e-9)


def test_rk_geodesic_matches_quadrature_connection():
    laws = Laws("SR", "GR")
    rs = 1.0
    P1, P2 = (10.0, 0.0), (0.0, 1000.0)
    for im in S.connect(P1, P2, rs, laws.c, rs):
        rays = light.trace_gr(laws, np.array([P1]), 0.0, im["emit_dir"][None, :], rs, rs, 2000.0, eta=1e-3)
        T, X, Y = rays.ray(0)
        R = np.hypot(X, Y)
        b = im["b"]
        rtp = S.turning_point(b, rs) if b > S.b_crit(rs) else None
        # every stored vertex lies on the exact geodesic: compare time at that radius (outgoing part)
        k = np.nonzero(R > 50)[0]
        for i in k[::5]:
            phi_q, t_q = _exact_phi_t(b, P1, R[i], rs, laws.c, im["branch"], rtp)
            assert T[i] * laws.c == pytest.approx(t_q * laws.c, rel=1e-9)


def _exact_phi_t(b, P1, r, rs, c, branch, rtp):
    r1 = math.hypot(*P1)
    if branch == "out":
        return S.integrals(b, r1, r, rs, c, rtp)
    p1, t1 = S.integrals(b, rtp, r1, rs, c, rtp)
    p2, t2 = S.integrals(b, rtp, r, rs, c, rtp)
    return p1 + p2, t1 + t2


def test_capture_below_critical_impact_parameter():
    laws = Laws("SR", "GR")
    rs = 1.0
    ys = np.array([2.4, 2.55, 2.65, 2.8])
    orig = np.stack([np.full(4, -200.0), ys], axis=1)
    rays = light.trace_gr(laws, orig, 0.0, np.tile([1.0, 0.0], (4, 1)), rs, rs, 400.0)
    assert list(rays.status) == [2, 2, 0, 0]  # b_c = 2.598 rs


# --- Newtonian corpuscles -----------------------------------------------------------------------------
def test_kepler_crossing_matches_rk_corpuscle():
    laws = Laws("emission", "newton")
    mu = 10 * GM_SUN
    rs = 2 * mu / C**2
    o = np.array([-300 * rs, 3 * rs])
    v0 = math.sqrt(C**2 + 2 * mu / np.linalg.norm(o)) * np.array([1.0, 0.0])
    cr = kepler.crossings(o, v0, mu, 400 * rs, 1.0)
    dt, pos, _ = cr[-1]
    rays = newton_light.trace_newton(laws, o[None, :], 0.0, v0[None, :], mu, 1.0, 2000 * rs, eta=1e-3)
    T, X, Y = rays.ray(0)
    R = np.hypot(X, Y)
    i = np.nonzero(R >= 400 * rs)[0][0]
    w = (400 * rs - R[i - 1]) / (R[i] - R[i - 1])
    ang = math.atan2(Y[i - 1] + w * (Y[i] - Y[i - 1]), X[i - 1] + w * (X[i] - X[i - 1]))
    assert ang == pytest.approx(math.atan2(pos[1], pos[0]), abs=1e-7)


def test_newtonian_half_deflection():
    """Soldner: weak-field corpuscle deflection is half the GR value, 2GM/(c^2 b) = rs/b."""
    mu = GM_SUN
    rs = 2 * mu / C**2
    b = 1e6 * rs
    o = np.array([-1e12 * rs, b])
    v0 = math.sqrt(C**2 + 2 * mu / np.linalg.norm(o)) * np.array([1.0, 0.0])
    r, h, E, evec, e = kepler._elements(o, v0, mu)
    defl = 2 * math.asin(1 / e)  # hyperbola: total turning angle
    assert defl == pytest.approx(rs / b, rel=1e-5)


# --- whole runs ---------------------------------------------------------------------------------------
def _checks(h):
    return h.checks()


def _all_ok(h):
    bad = []
    for c in h.checks().values():
        if c["ref"] is None or c["rel"] is None:
            continue
        if abs(c["rel"]) > max(c.get("tol") or 1e-9, 1e-9):
            bad.append((c["label"], c["value"], c["ref"], c["rel"]))
    return bad


@pytest.mark.parametrize("preset,horizon", [
    ("sun_earth", 600.0), ("measure_c", 0.04), ("measure_c_lab", 0.04), ("measure_c_ether", 0.04),
    ("measure_c_emission", 0.04), ("michelson", 0.04), ("lensing", 0.2), ("lensing_newton", 0.2),
    ("andromeda", 1e14), ("andromeda_fast", 1e14)])
def test_presets_run_and_all_checks_agree(preset, horizon):
    h = Harness(V, preset)
    for k in range(6):
        h.run_to(horizon * (k + 1) / 6)
        meta, _ = h.sim.frame()  # frames must work at any time
        assert "objects" in meta
    assert not h.errors()
    assert _all_ok(h) == []


def test_measured_speeds_sr_are_c_for_all_observers():
    h = Harness(V, "measure_c")
    h.run_to(0.04)
    speeds = [c["value"] for c in h.checks().values() if "one-way speed" in render(c["label"])]
    assert len(speeds) == 3
    assert np.allclose(speeds, C, rtol=1e-12)


def test_round_trip_measurement_and_boost_resync():
    h = Harness(V, "measure_c")
    h.run_to(0.004)  # after synchronisation (2 L0 / c ~ 2 ms)
    h.action("measure", obj="obs2")
    h.run_to(0.008)  # lab round trip at 0.5 c: 2.31 ms
    rt = [c for c in h.checks().values() if "round-trip speed" in render(c["label"])]
    assert rt and abs(rt[0]["value"] / C - 1) < 1e-12
    # boost: the apparatus is dismantled, rebuilt in the new rest frame and re-synchronised by light
    n_sync_before = len([e for e in h.of("event") if e["kind"] == "sync" and e.get("obj") == "obs2"])
    t_boost = h.sim.t
    h.action("boost", obj="obs2", v=-0.8, unit="c", angle=0.0)
    h.run_to(0.02)
    syncs = [e for e in h.of("event") if e["kind"] == "sync" and e.get("obj") == "obs2"]
    assert len(syncs) > n_sync_before and syncs[-1]["t"] > t_boost
    h.action("measure", obj="obs2")
    h.run_to(0.03)
    one_way = [c for c in h.checks().values() if "one way" in render(c["label"])]
    assert one_way and all(abs(c["value"] / C - 1) < 1e-12 for c in one_way)


def test_michelson_ether_round_trips():
    h = Harness(V, "measure_c_ether")
    h.run_to(0.004)
    h.action("measure", obj="obs2")  # longitudinal rod, v = 0.5 c
    h.run_to(0.01)
    rt = [c for c in h.checks().values() if "round-trip speed" in render(c["label"])][0]
    assert rt["value"] == pytest.approx(C * (1 - 0.25), rel=1e-12)
    h2 = Harness(V, "michelson")
    h2.run_to(0.004)
    h2.action("measure", obj="obs2")  # transverse rod
    h2.run_to(0.01)
    rt2 = [c for c in h2.checks().values() if "round-trip speed" in render(c["label"])][0]
    assert rt2["value"] == pytest.approx(C * math.sqrt(1 - 0.25), rel=1e-12)


def test_doppler_train_sr():
    h = Harness(V, "measure_c")
    h.action("train", obj="src", period=1e-3, count=4)
    h.run_to(0.05)
    dop = [c for c in h.checks().values() if render(c["group"]) == "Doppler effect and redshift"]
    assert dop and _all_ok(h) == []
    by = {render(c["label"]): c["value"] for c in dop}
    # observer 2 recedes at 0.5c: sqrt((1-b)/(1+b)) = 0.5774
    assert any(abs(v - math.sqrt(1 / 3)) < 1e-9 for v in by.values())


def test_gravitational_redshift_train():
    h = Harness(V, "lensing")
    h.action("train", obj="src", period=1e-3, count=3)
    h.run_to(0.2)
    dop = [c for c in h.checks().values() if render(c["group"]) == "Doppler effect and redshift"]
    assert dop and _all_ok(h) == []


def test_andromeda_now_offsets():
    h = Harness(V, "andromeda")
    meta, _ = h.sim.frame()
    na = meta["now_at"]
    day = 86400.0
    assert na["walk_to"]["andromeda"] / day == pytest.approx(4.2642, rel=1e-4)
    assert na["walk_from"]["andromeda"] / day == pytest.approx(-4.2642, rel=1e-4)
    assert na["stay"]["andromeda"] == pytest.approx(0.0, abs=1e-6)


def test_sun_earth_light_time():
    h = Harness(V, "sun_earth")
    h.run_to(600.0)
    st = [e for e in h.of("event") if e["kind"] == "arrival" and e["obj"] == "station"][0]
    ref = checks.radial_light_time(R_SUN * (1 + 1e-9), AU, 2 * GM_SUN / C**2, C)
    assert st["data"]["dt"] == pytest.approx(ref, rel=1e-12)
    # flat-space part (AU - R_sun)/c plus the Shapiro excess of ~50 microseconds
    assert 40e-6 < st["data"]["shapiro"] < 70e-6


def test_events_are_revealed_only_when_time_reaches_them():
    h = Harness(V, "sun_earth")
    h.run_to(400.0)
    assert not [e for e in h.of("event") if e["kind"] == "arrival" and e["obj"] == "station"]
    h.run_to(500.0)
    assert [e for e in h.of("event") if e["kind"] == "arrival" and e["obj"] == "station"]


def test_one_law_changed_from_the_defaults_works_and_two_incompatible_are_refused():
    """Review UX-params P12 (was: such combinations refused at the start, which the player hid). One law changed from
    the defaults: the world takes the other one as the nearest law that goes with it and says so (a notice, the
    scenario text, the header's parameters and modifications); two changed laws that do not go together are refused
    in Russian, saying what to change. The law set the world runs is always a valid one (Laws.validate)."""
    from u31_light_travel.viz import _adjust_laws
    cases = {("sun_earth", "ether", "GR"): ("ether", "none"), ("sun_earth", "emission", "GR"): ("emission", "newton"),
             ("sun_earth", "SR", "newton"): ("emission", "newton"), ("lensing", "ether", "GR"): ("ether", "none"),
             ("measure_c", "SR", "newton"): ("SR", "none"), ("measure_c", "ether", "GR"): ("ether", "none"),
             ("andromeda", "emission", "GR"): ("emission", "none"), ("sun_earth", "SR", "GR"): ("SR", "GR")}
    for (scn, k, g), (k2, g2) in cases.items():
        h = Harness(V, None, {"scenario": scn, "kinematics": k, "gravity": g})
        hp = h.of("header")[-1]["params"]
        assert (hp["kinematics"], hp["gravity"]) == (k2, g2) and not Laws(k2, g2).validate()
        notes = [m["text"] for m in h.of("notice") if "dependent parameters" in render(m["text"])]
        assert bool(notes) == ((k, g) != (k2, g2)), notes
        assert not h.errors()
    for scn in ("sun_earth", "lensing"):
        with pytest.raises(ValueError, match="choose “Kinematics” = emission theory"):
            Harness(V, None, {"scenario": scn, "kinematics": "ether", "gravity": "newton"})
    # a lens of radius 0 is GR's black hole: without GR it is given the horizon's radius of its mass (stated)
    h = Harness(V, None, {"scenario": "lensing", "kinematics": "ether"})
    assert h.of("header")[-1]["params"]["ln_radius_km"] == pytest.approx(2 * GM_SUN * 10.0 / C**2 / 1e3, rel=1e-12)
    assert h.of("header")[-1]["body"]["radius"] == pytest.approx(2 * GM_SUN * 10.0 / C**2, rel=1e-12)
    # idempotent: a world rebuilt from the header's parameters (a resumed run) changes nothing more
    p = dict(h.of("header")[-1]["params"])
    assert _adjust_laws(p) == [] and p == h.of("header")[-1]["params"]


def test_walkers_faster_than_this_worlds_light_are_refused_with_the_numbers():
    """Review UX-params P7: «worldline is not timelike» (English, from the core) for walkers faster than c x factor.
    Now refused before the core, in the owner's terms, with the numbers to change; a Galilean world (ether) takes them."""
    with pytest.raises(ValueError, match="pedestrians cannot be faster than the light of this world") as e:
        Harness(V, None, {"scenario": "andromeda", "c_factor": 0.5, "an_walk": 2e8})
    assert "0.6671" in str(e.value)  # the factor above which the same walkers are slower than light
    Harness(V, None, {"scenario": "andromeda", "c_factor": 0.6672, "an_walk": 2e8})
    h = Harness(V, None, {"scenario": "andromeda", "c_factor": 0.5, "an_walk": 2e8, "kinematics": "ether"})
    h.run_to(1e14)
    assert not h.errors()


# --- regressions from the physics review 2026-10-22 (reviews/archive/2026-10-22_internal_viz-v01_physics) ---------
def _arrivals_of(h, obj):
    return [e for e in h.of("event") if e["kind"] == "arrival" and e.get("obj") == obj]


@pytest.mark.parametrize("preset", ["lensing", "lensing_newton"])
def test_R1_fast_receiver_still_receives(preset):
    h = Harness(V, preset)
    h.action("boost", obj="obs", v=0.9, unit="c", angle=0.0)
    h.run_to(1.0)
    assert len(_arrivals_of(h, "obs")) >= 1


@pytest.mark.parametrize("preset,obj", [("lensing", "obs"), ("sun_earth", "rocket"), ("measure_c", "obs3")])
def test_R2_boost_at_arrival_does_not_repeat_it(preset, obj):
    h = Harness(V, preset)
    for _ in range(40):
        h.cmd("next_event")
        if _arrivals_of(h, obj):
            break
    h.action("boost", obj=obj, v=0.2, unit="c", angle=0.0)
    h.run_to(h.sim.t * 3 + 1.0)
    keys = [(e["pulse"], e["data"]["side"]) for e in _arrivals_of(h, obj)]
    assert len(keys) == len(set(keys))


def test_R3_emission_newton_sun_earth_runs():
    h = Harness(V, None, {"scenario": "sun_earth", "kinematics": "emission", "gravity": "newton"})
    h.run_to(700.0)
    assert not h.errors()
    assert _arrivals_of(h, "station")


def test_R4_B_clock_hidden_until_synchronised():
    h = Harness(V, "measure_c")
    h.run_to(0.0005)
    o = [q for q in h.sim.frame()[0]["objects"] if q["id"] == "obs2"][0]
    assert o["synced"] is False and o["tau_b"] is None
    h.run_to(0.003)
    o = [q for q in h.sim.frame()[0]["objects"] if q["id"] == "obs2"][0]
    assert o["synced"] is True and o["tau_b"] is not None


def test_R5_emission_result_not_before_B_reading_can_arrive():
    h = Harness(V, None, {"scenario": "measure_c", "gravity": "none", "kinematics": "emission",
                          "mc_v1": 0.0, "mc_v2": 0.0, "mc_v3": 0.0})
    w = h.sim.world
    # a source on the far side moving towards the rods at 0.5c: the flash passes B before A
    from u31_light_travel.engine.world import Obj
    from lfphys.core.worldlines import Piecewise
    w.add(Obj("far", "Far source", "beacon", "#000",
              Piecewise.start(w.laws, 0.0, 0.0, [3.0e6, 0.0], [-0.5 * C, 0.0]), receiver=False))
    h.run_to(0.004)
    h.action("flash", obj="far")
    h.run_to(0.05)
    ap = w.objects["obs1"].apparatus
    for e in h.of("event"):
        if e["kind"] == "measure" and e.get("pulse") and "B→A" in e["text"]:
            res = e["data"]
            # the result is revealed no earlier than B's reading can reach A at c relative to B (emission theory)
            t_b = None
            for a in h.of("event"):
                pass
            assert e["t"] >= res["t_known"] - 1e-15
            assert res["t_known"] >= ap.light(e["t"] - 1e-3, "B", "A") - 1.0  # sanity: a finite delivery time


def test_R6_lensing_checks_wait_for_the_rays():
    h = Harness(V, "lensing")
    h.run_to(1e-6)
    assert "bc" not in h.checks() or h.checks()["bc"]["value"] is None
    h.run_to(0.2)
    assert h.checks()["bc"]["value"] is not None and h.checks()["bc"]["t"] > 1e-3


def test_R7_cone_of_observer_moving_along_y_is_c():
    h = Harness(V, "measure_c")
    h.action("boost", obj="obs1", v=0.8, unit="c", angle=90.0)
    cone = h.sim.frame()[0]["cones"]["obs1"]["fut"]
    assert cone[0] == pytest.approx(C, rel=1e-5) and cone[1] == pytest.approx(-C, rel=1e-5)


def test_R8_local_c_check_passes_in_standard_physics():
    h = Harness(V, "lensing")
    h.action("measure", obj="obs")
    h.run_to(0.01)
    loc = [c for c in h.checks().values() if c["id"].startswith("loc_")][0]
    assert abs(loc["rel"]) < 1e-9


def test_R9_doppler_not_paired_across_a_boost():
    h = Harness(V, "measure_c")
    h.action("train", obj="src", period=2e-3, count=6)
    h.run_to(0.012)
    h.action("boost", obj="obs1", v=0.3, unit="c", angle=0.0)
    h.run_to(0.06)
    dop = [c for c in h.of("check") if render(c["group"]) == "Doppler effect and redshift" and c["ref"] is not None]
    assert dop and all(abs(c["rel"]) < 1e-9 for c in dop)


def test_R10_boost_into_the_body_refused():
    h = Harness(V, "lensing")
    h.action("boost", obj="obs", v=0.5, unit="c", angle=180.0)
    assert any("fly into the body" in render(e) or "faster than light" in render(e) for e in h.errors())


def test_R13_measurement_under_way_survives_a_boost():
    h = Harness(V, "measure_c")
    h.run_to(0.004)
    h.action("measure", obj="obs1")
    h.run_to(0.0045)
    h.action("boost", obj="obs1", v=0.5, unit="c", angle=0.0)
    h.run_to(0.02)
    assert any("after the change of speed" in render(e["text"]) or "after A changed its speed" in render(e["text"]) for e in h.of("event") if e["kind"] == "measure")


def test_R21_next_event_at_current_instant():
    h = Harness(V, "measure_c")
    h.run_to(0.003)  # the source flashes at 3 ms: zero-delay events at that instant are revealed in place
    n0 = len(h.of("event"))
    h.cmd("next_event")
    assert len(h.of("event")) >= n0


def test_live_speed_control_reports_current_velocities():
    """Owner, 2026-10-23: the speed of an observer is a live control; after a boost the action carries the speed
    in force, so the control shows what the world has (also after a refused boost)."""
    h = Harness(V, "measure_c")
    h.run_to(1e-4)
    h.action("boost", obj="obs2", v=0.3, angle=180.0)
    acts = h.of("actions")[-1]["actions"]
    b = [a for a in acts if a["name"] == "boost"][0]
    assert b["mode"] == "live" and abs(b["current"]["obs2"]["v"] - 0.3) < 1e-12
    assert abs(abs(b["current"]["obs2"]["angle"]) - 180.0) < 1e-9


def _flash_session(preset, obj):
    """The review's sequence (UX-params repro r_v01_flash): 8 frames, a flash, 8 frames, next event, a flash, 8 frames."""
    h = Harness(V, preset)
    sp = h.runner.speed

    def frames(n):
        for _ in range(n):
            h.run_to(h.sim.t + sp / 20.0)
    frames(8)
    h.action("flash", obj=obj)
    frames(8)
    h.cmd("next_event")
    h.action("flash", obj=obj)
    frames(8)
    h.run_to(h.sim.t + 20 * sp)
    return h


@pytest.mark.parametrize("preset", ["measure_c", "measure_c_lab", "measure_c_ether", "measure_c_emission"])
def test_a_flash_between_the_ends_of_a_rod_is_not_a_speed(preset):
    """Review UX-params P9 [error in earlier]: a flash inside another observer's rod reached A and B running in opposite
    directions, and L0/(tau_B - tau_A) was shown as a measured c = 5.6e8 ... 7.8e9 m/s (checks failed). Now that
    passage is reported as not measurable, and every speed shown is a passage of one light along the rod, equal to
    the closed form (checks.one_way_speed). Second route for the criterion: the flagged flashes are exactly those whose
    emission point lies strictly between the rod's ends at the emission time (positions of the worldlines)."""
    h = _flash_session(preset, "obs1")
    assert _all_ok(h) == []
    w = h.sim.world
    inside_ev = {(e["obj"], e["pulse"]) for e in h.of("event") if "between the ends" in render(e.get("text") or "")}
    measured = {(e["obj"], e["pulse"]) for e in h.of("event") if "measured c" in render(e.get("text") or "")}
    assert inside_ev and not (inside_ev & measured)
    for pulse in w.pulses:
        if pulse["src"] != "obs1":
            continue
        for oid in ("obs2", "obs3"):
            ap = w.objects[oid].apparatus
            xs = pulse["origin"][0]
            xa = w.objects[oid].wl.pos(pulse["t0"])[0]
            xb = ap.wl_b.pos(pulse["t0"])[0]
            between = min(xa, xb) < xs < max(xa, xb)
            if between:
                assert (oid, pulse["id"]) in inside_ev
            else:
                assert (oid, pulse["id"]) not in inside_ev
    speeds = [c for c in h.checks().values() if c["id"].startswith("pass_")]
    assert speeds and all(c["ref"] is not None and abs(c["rel"]) <= 1e-9 for c in speeds)
    assert all(abs(c["value"]) < 2 * C for c in speeds)


def test_flight_times_far_from_the_time_origin_keep_their_precision():
    """Review UX-params P14: in «andromeda» the flash at t = 4e11 s took the flight time as a difference of absolute
    times (1867.9589233398438 s, 3.3e-8 off: the spacing of doubles at 4e11) and the self-consistency checks failed at
    1e-9. Now the flight time is summed from the solved interval (worldlines.sphere_meeting "dt"): the residuals are
    at round-off. Negative control: the old difference fails the same check's tolerance."""
    h = _flash_session("andromeda", "earth")
    flat = {c["id"]: c for c in h.checks().values() if c["id"].startswith("flat_")}
    assert len(flat) >= 6 and _all_ok(h) == []
    worst_old = 0.0
    for e in h.of("event"):
        if e.get("kind") != "arrival" or not e.get("pulse"):
            continue
        c = flat.get(f"flat_{e['pulse']}_{e['obj']}")
        if c is None or c["rel"] is None:
            continue
        assert abs(c["rel"]) <= 1e-14
        t0 = next(p["t0"] for p in h.sim.world.pulses if p["id"] == e["pulse"])
        worst_old = max(worst_old, abs((e["t"] - t0) - c["ref"]) / c["ref"] / c["tol"])
    assert worst_old > 1.0  # the subtraction of absolute times would fail (3e-8 > 1e-9)


# --- the engine's refusals matched by their machine codes (review 2026-11-12 i18n-code F5) ------------------------
@pytest.mark.parametrize("code", ["gr.not_timelike", "kinematics.superluminal"])
def test_superluminal_path_codes_become_the_worlds_refusal(code, monkeypatch):
    """A boost whose path would outrun the local light: the engine's coded ValueError becomes the world's refusal in
    the owner's terms, whatever the engine's wording."""
    from lfphys.codes import coded
    from lfphys.i18n import T
    from lfviz.errors import Refusal
    from u31_light_travel.engine import world as W

    def refuse(*a, **k):
        raise coded(ValueError(T("reworded by the engine")), code)

    h = Harness(V, "lensing")
    monkeypatch.setattr(W, "clock_rate", refuse)
    with pytest.raises(Refusal) as e:
        h.sim.world._validate_path(h.sim.world.objects["obs"], h.sim.t, np.array([0.1 * C, 0.0]))
    assert e.value.text["$t"].startswith("at a constant coordinate speed “{obj}” would move faster than light")


def test_other_clock_rate_codes_are_not_taken_for_superluminal(monkeypatch):
    from lfphys.codes import code_of, coded
    from lfphys.i18n import T
    from u31_light_travel.engine import world as W

    def refuse(*a, **k):
        raise coded(ValueError(T("the clock is inside the horizon")), "gr.inside_horizon")

    h = Harness(V, "lensing")
    monkeypatch.setattr(W, "clock_rate", refuse)
    with pytest.raises(ValueError) as e:
        h.sim.world._validate_path(h.sim.world.objects["obs"], h.sim.t, np.array([0.1 * C, 0.0]))
    assert code_of(e.value) == "gr.inside_horizon"
