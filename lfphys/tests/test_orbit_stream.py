# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.core.gravity.orbit_stream: every route against a closed form or an independent second method."""

import math

import numpy as np
import pytest

from lfphys.core.constants import AU, C, GM_SUN
from lfphys.core.gravity import orbit_stream as osm
from lfphys.core.gravity import orbits


def _launch(r0, k, alpha_deg=0.0):
    v = k * min(math.sqrt(1.0 / (r0 - 2.0)), 1.0)
    a = math.radians(alpha_deg)
    return v * math.sin(a), v * math.cos(a)


def _peris(st, n, chunk=None):
    out = []
    t = 0.0
    while len(out) < n and not st.done:
        if chunk is None:
            ch = st.advance(1e300, 2.0)
        else:
            t += chunk
            ch = st.advance(t, 2.0)
        out += [e for e in ch["events"] if e["kind"] == "peri"]
    return out


def test_constants_from_local_velocity_without_cancellation():
    for r0, vr, vp in ((10.0, 0.1, 0.3), (6.0, -0.2, 0.4), (3.1e7, 0.0, 1.9e-4)):
        k = osm.local_velocity_to_constants(r0, vr, vp)
        e, l = orbits.from_local_velocity(r0, vr, vp)
        assert k["e"] == e and k["l"] == l
        # e^2 - 1 from gamma^2 (v^2 - 2/r): equal to the direct difference where that is well conditioned
        if r0 < 100:
            assert k["em1"] == pytest.approx(e * e - 1.0, rel=1e-13)
        assert k["em1"] < 0


@pytest.mark.parametrize("r0,k,alpha", [(20.0, 1.2, 0.0), (10.0, 1.12, 0.0), (12.0, 1.05, 25.0), (1e5, 1.1, -30.0)])
def test_periapsis_advance_matches_the_elliptic_integral(r0, k, alpha):
    st = osm.OrbitStream(r0, *_launch(r0, k, alpha))
    assert st.info["kind"] == "bound"
    P = _peris(st, 4)
    exact = orbits.periapsis_advance(st.e, abs(st.l))
    adv = np.diff([p["psi"] for p in P]) - 2 * math.pi
    assert np.allclose(adv, exact, rtol=1e-9, atol=2e-12)
    # the periapsis radius is the turning point (root of f(u)) and the first integral is kept
    el = orbits.elements(st.e, abs(st.l))
    for p in P:
        assert p["r"] == pytest.approx(el["r_peri"], rel=1e-9)
        assert p["em1_state"] == pytest.approx(st.em1, rel=1e-10)


def test_mercury_weak_field_advance_and_century():
    """Mercury (a = 0.38709893 AU, e = 0.20563069, NASA NSSDCA): the integrated orbit gives the exact advance to the
    integration error (~1e-12 rad absolute) and 42.98"/century (Will 2014, Eq. 65) to the reference's digits."""
    M = GM_SUN / C**2
    a, ecc = 0.38709893 * AU, 0.20563069
    r0 = a * (1 - ecc) / M
    st = osm.OrbitStream(r0, 0.0, math.sqrt((1 + ecc) / (r0 - 2.0)))
    P = _peris(st, 3)
    exact = orbits.periapsis_advance(st.e, abs(st.l))
    adv = np.diff([p["psi"] for p in P]) - 2 * math.pi
    assert np.allclose(adv, exact, rtol=2e-5)
    period_s = np.mean(np.diff([p["t"] for p in P])) * M / C
    century = np.mean(adv) * 36525 * 86400 / period_s * 180 / math.pi * 3600
    assert century == pytest.approx(42.98, abs=0.006)


def test_stream_matches_the_engine_orbit_integrator():
    """Independent route: lfphys.core.gravity.orbits.integrate_orbit (unscaled u, one call, its own sign of du/dphi)
    compared at psi = pi, 2 pi, 3 pi, 4 pi (chunk ends of the stream, grid points of integrate_orbit)."""
    r0, k = 15.0, 1.15
    vr, vp = _launch(r0, k, 10.0)  # moving outward: du/dphi < 0
    st = osm.OrbitStream(r0, vr, vp, n_turn=240)
    ends = []
    while len(ends) < 4:
        ch = st.advance(1e300, 0.5)  # chunks of exactly pi in psi
        ends.append((ch["t"][-1], ch["tau"][-1], ch["r"][-1]))
    o = orbits.integrate_orbit(st.e, st.l, 1.0 / r0, -1.0, 4 * math.pi, n_out=1921)
    for j, (t, tau, r) in enumerate(ends, start=1):
        i = 480 * j
        assert o["phi"][i] == pytest.approx(j * math.pi, rel=1e-14)
        assert r == pytest.approx(o["r"][i], rel=1e-9)
        assert t == pytest.approx(o["t"][i], rel=1e-9)
        assert tau == pytest.approx(o["tau"][i], rel=1e-9)


def test_chunking_is_seamless():
    r0, k = 20.0, 1.2
    a = osm.OrbitStream(r0, *_launch(r0, k))
    b = osm.OrbitStream(r0, *_launch(r0, k))
    pa = _peris(a, 4)
    pb = _peris(b, 4, chunk=37.0)  # many short chunks ended by the time event
    assert [p["psi"] for p in pb] == pytest.approx([p["psi"] for p in pa], abs=1e-11)
    assert [p["t"] for p in pb] == pytest.approx([p["t"] for p in pa], rel=1e-11)


def test_retrograde_orbit_mirrors_the_prograde_one():
    r0, k = 20.0, 1.2
    vr, vp = _launch(r0, k, 10.0)
    a = osm.OrbitStream(r0, vr, vp)
    b = osm.OrbitStream(r0, vr, -vp)
    pa, pb = _peris(a, 2), _peris(b, 2)
    assert [p["phi"] for p in pb] == pytest.approx([-p["phi"] for p in pa], abs=1e-11)
    assert [p["t"] for p in pb] == pytest.approx([p["t"] for p in pa], rel=1e-12)


@pytest.mark.parametrize("r", [6.5, 10.0, 50.0])
def test_circular_orbit_clock_rate_and_period(r):
    """Circular geodesic: dtau/dt = sqrt(1 - 3M/r) and the period 2 pi sqrt(r^3/M) in t, exactly."""
    st = osm.OrbitStream(r, 0.0, math.sqrt(1.0 / (r - 2.0)))
    assert st.info["kind"] == "circular"
    laps = []
    while len(laps) < 3:
        laps += [e for e in st.advance(1e300, 2.0)["events"] if e["kind"] == "lap"]
    L = laps[2]
    assert L["t"] / 3 == pytest.approx(2 * math.pi * r**1.5, rel=1e-11)
    assert L["tau"] / L["t"] == pytest.approx(math.sqrt(1 - 3 / r), rel=1e-11)
    assert L["r"] == pytest.approx(r, rel=1e-11)


def test_radial_fall_from_rest_is_the_cycloid():
    r0 = 20.0
    st = osm.OrbitStream(r0, 0.0, 0.0)
    assert st.radial and st.info["kind"] == "radial_fall"
    while not st.done:
        ch = st.advance(1e300, 2.0)
    stop = [e for e in ch["events"] if e["kind"] == "horizon"][0]
    eta = math.acos(2 * stop["r"] / r0 - 1)
    assert stop["tau"] == pytest.approx(math.sqrt(r0**3 / 8) * (eta + math.sin(eta)), rel=1e-11)
    assert stop["r"] == pytest.approx(2.0 / (1 - osm.HORIZON_GAP), rel=1e-12)


def test_radial_throw_reaches_the_apex():
    """Thrown up with e < 1: the top of the flight at r = 2/(1 - e^2), then the fall."""
    r0 = 10.0
    st = osm.OrbitStream(r0, 0.3, 0.0)
    evs = []
    while not st.done:
        evs += st.advance(1e300, 2.0)["events"]
    top = [e for e in evs if e["kind"] == "apo"][0]
    assert top["r"] == pytest.approx(-2.0 / st.em1, rel=1e-10)


@pytest.mark.parametrize("r0,k,alpha", [(5.5, 0.995, 0.0), (8.0, 0.9, 20.0), (30.0, 0.3, -40.0)])
def test_plunge_proper_time_matches_the_quadrature(r0, k, alpha):
    vr, vp = _launch(r0, k, alpha)
    st = osm.OrbitStream(r0, vr, vp)
    assert st.info["kind"] == "plunge"
    evs = []
    while not st.done:
        evs += st.advance(1e300, 2.0)["events"]
    stop = evs[-1]
    assert stop["kind"] == "horizon"
    ref = osm.plunge_proper_time(st.em1, st.l, r0, vr, stop["r"], st.info["r_apo"])
    assert stop["tau"] == pytest.approx(ref, rel=1e-9)


def test_surface_impact_speed():
    r0, R = 10.0, 5.8
    vr, vp = _launch(r0, 0.3)
    st = osm.OrbitStream(r0, vr, vp, r_stop=R)
    evs = []
    while not st.done:
        evs += st.advance(1e300, 2.0)["events"]
    hit = evs[-1]
    assert hit["kind"] == "surface" and hit["r"] == pytest.approx(R, rel=1e-12)
    v = math.hypot(hit["v_r"], hit["v_phi"])
    assert v == pytest.approx(osm.local_speed_from_e(R, st.e), rel=1e-10)


def test_state_at_a_time_is_on_the_orbit():
    r0, k = 20.0, 1.2
    vr, vp = _launch(r0, k, 15.0)
    st = osm.OrbitStream(r0, vr, vp)
    ch = st.advance(3000.0, 4.0)
    for t in (100.0, 1234.5, 2999.0):
        s = st.state_at(t)
        assert s["t"] == t
        e, l = orbits.from_local_velocity(s["r"], s["v_r"], s["v_phi"])  # the constants from the state
        assert e == pytest.approx(st.e, rel=1e-11) and l == pytest.approx(st.l, rel=1e-11)
        assert s["r"] == pytest.approx(np.interp(t, ch["t"], ch["r"]), rel=2e-3)


def test_second_scheme_conserves_and_agrees():
    for r0, k, alpha in ((10.0, 1.12, 0.0), (20.0, 1.2, 20.0)):
        vr, vp = _launch(r0, k, alpha)
        st = osm.OrbitStream(r0, vr, vp)
        exact = orbits.periapsis_advance(st.e, abs(st.l))
        g = osm.geodesic_tau(r0, vr, vp, 3 * 2 * math.pi * (2 * r0) ** 1.5)
        adv = np.diff(g["peri_phi"]) - 2 * math.pi
        assert np.allclose(adv, exact, rtol=1e-8)
        assert g["e0"] == pytest.approx(st.e, rel=1e-14) and g["l0"] == pytest.approx(st.l, rel=1e-14)
        assert g["e_drift"] < 1e-11 and g["l_drift"] < 1e-10 and g["norm_drift"] < 1e-11


def test_ppn_next_order_term():
    """The relative correction to 6 pi M/p is (18 + ecc^2)/4 * M/p + O((M/p)^2) (p, ecc from the turning points);
    v04 uses it as the tolerance of the leading-order reference."""
    for ecc in (0.0, 0.2, 0.6, 0.9):
        for p in (1e4, 1e5):
            rp, ra = p / (1 + ecc), p / (1 - ecc)
            exact = (orbits.advance_from_turning(1 / ra, 1 / rp) if ecc > 0
                     else 2 * math.pi / math.sqrt(1 - 6 / p) - 2 * math.pi)
            rel = exact / (6 * math.pi / p) - 1
            assert rel * p == pytest.approx((18 + ecc**2) / 4, abs=30.0 / p)


def test_classification():
    assert osm.OrbitStream(6.2, 0.0, math.sqrt(1 / 4.2)).info["kind"] == "circular"
    assert osm.OrbitStream(5.5, *_launch(5.5, 0.995)).info["kind"] == "plunge"
    assert osm.OrbitStream(7.0, *_launch(7.0, 0.995)).info["kind"] == "bound"
    assert osm.OrbitStream(20.0, *_launch(20.0, 1.5)).info["kind"] == "escape"
    with pytest.raises(ValueError):
        osm.OrbitStream(20.0, 0.0, 1.0)
    with pytest.raises(ValueError):
        osm.OrbitStream(5.0, 0.0, 0.1, r_stop=6.0)


def test_clock_lag_without_cancellation():
    """1 - dtau/dt: equal to 1 - clock_rate where that is well conditioned; on a weak-field circular orbit equal to
    1 - sqrt(1 - 3M/r) = (3M/r)/(1 + sqrt(1 - 3M/r)) to full precision (the single-precision rate cannot resolve it)."""
    st = osm.OrbitStream(10.0, *_launch(10.0, 1.1, 10.0))
    r = np.array([8.0, 10.0, 40.0])
    assert np.allclose(st.clock_lag(r), 1.0 - st.clock_rate(r), rtol=1e-13)
    r0 = 3.1e7
    c = osm.OrbitStream(r0, 0.0, math.sqrt(1.0 / (r0 - 2.0)))
    x = 3.0 / r0
    assert float(c.clock_lag(r0)) == pytest.approx(x / (1.0 + math.sqrt(1.0 - x)), rel=1e-12)


# --- review 2026-10-23 (internal, viz-v04): classification, far radial falls, far apoapses, weak-field drifts -------
def _mp_kind(r0, vr, vp, circ=osm.CIRCULAR_SPREAD):
    """Independent 40-digit classification (reviewer's 11_classify_scan.py): roots of F(y) at 40 digits from the same
    float launch data, the allowed interval containing y = 1, the direction of motion when no turning point exists."""
    import mpmath as mp
    mp.mp.dps = 40
    R0, VR, VP = mp.mpf(r0), mp.mpf(vr), mp.mpf(vp)
    v2 = VR**2 + VP**2
    g2 = 1 / (1 - v2)
    EM1, L = g2 * (v2 - 2 / R0), mp.sqrt(g2) * VP * R0
    us = 1 / R0
    A, B = 1 / (L**2 * us), EM1 / (L**2 * us**2)

    def F(y):
        return 2 * us * y**3 - y**2 + 2 * A * y + B
    ys = sorted(mp.re(z) for z in mp.polyroots([2 * us, -1, 2 * A, B], maxsteps=400, extraprec=400)
                if abs(mp.im(z)) < mp.mpf(10) ** -25)
    eps = mp.mpf(10) ** -30
    lo = max([y for y in ys if y < 1 - eps] + [y for y in ys if abs(y - 1) <= eps and F(1 - mp.mpf(10) ** -20) < 0],
             default=None)
    hi = min([y for y in ys if y > 1 + eps] + [y for y in ys if abs(y - 1) <= eps and F(1 + mp.mpf(10) ** -20) < 0],
             default=None)
    y_stop = R0 / (2 / (1 - mp.mpf(osm.HORIZON_GAP)))
    r_peri = R0 / hi if hi is not None and hi < y_stop else None
    r_apo = R0 / lo if lo is not None and lo > 0 else None
    if r_peri is not None and r_apo is not None:
        return ("circular" if r_apo - r_peri <= circ * r_peri else "bound"), r_peri, r_apo
    if r_peri is not None:
        return "escape", r_peri, r_apo
    if r_apo is not None:
        return "plunge", r_peri, r_apo
    return ("escape" if vr > 0 else "plunge"), r_peri, r_apo


def test_kind_of_tangential_launches_near_circular_speed():
    """V4-1: a start at a turning point (v_r = 0) near the circular speed: before the fix 20 of these 64 kinds were
    wrong (the start re-found as a root and compared with 1 +- 1e-12)."""
    bad = []
    for r0 in (6.01, 6.1, 6.5, 7.0, 10.0, 20.0, 100.0, 1e4):
        for dk in (-1e-3, -1e-4, -1e-5, -1e-6, 1e-6, 1e-5, 1e-4, 1e-3):
            vp = (1 + dk) * math.sqrt(1 / (r0 - 2))
            st = osm.OrbitStream(r0, 0.0, vp)
            kind, rp, ra = _mp_kind(r0, 0.0, vp)
            ok = st.info["kind"] == kind
            if ok and kind in ("bound", "circular"):
                ok = abs(st.info["r_peri"] / float(rp) - 1) < 1e-12 and abs(st.info["r_apo"] / float(ra) - 1) < 1e-12
            if not ok:
                bad.append((r0, dk, st.info, kind))
    assert not bad, bad


def test_kind_after_a_boost_of_a_circular_orbit():
    """V4-1: boosts of a circular state (v_r ~ +-3e-17 from the dense output): before the fix 32 of 48 had the wrong
    kind or turning points (a plunge called escape, r_peri = 2.43 M instead of 20 M...)."""
    bad = []
    for r0 in (6.2, 8.0, 20.0, 1e3):
        vc = math.sqrt(1 / (r0 - 2))
        for dv in (-0.3, -0.05, -1e-3, 1e-3, 0.05, 0.3):
            for vr in (3e-17, -3e-17):
                vp = vc * (1 + dv)
                st = osm.OrbitStream(r0, vr * (1 + dv), vp)
                kind, rp, ra = _mp_kind(r0, 0.0, vp)  # the snapped start: v_r = 0
                ok = st.info["kind"] == kind
                if ok and kind == "bound":
                    ok = abs(st.info["r_peri"] / float(rp) - 1) < 1e-12 and abs(st.info["r_apo"] / float(ra) - 1) < 1e-12
                if not ok:
                    bad.append((r0, dv, vr, st.info["kind"], kind))
    assert not bad, bad


@pytest.mark.parametrize("r0,k,angle", [(5.0, 1.6, 30.0), (3.5, 0.95, 45.0), (20.0, 1.6, 89.0)])
def test_outward_unbound_launch_is_an_escape(r0, k, angle):
    """V4-2: moving outward with no apoapsis the body escapes (before: «plunge», then an escape event)."""
    v = k * min(math.sqrt(1 / (r0 - 2)), 1.0)
    st = osm.OrbitStream(r0, v * math.sin(math.radians(angle)), v * math.cos(math.radians(angle)))
    assert st.info["kind"] == "escape" and st.info["r_apo"] is None
    while not st.done:
        st.advance(1e300, 2.0)
    assert st.done == "escape"


@pytest.mark.parametrize("r0", [1e6, 1e7, 1e8])
def test_radial_fall_from_far_stops_at_the_horizon(r0):
    """V4-3: the radial scheme in one scale s = tau/r0^{3/2} could not resolve the last 1e-4 M of the fall: from 1e8 M
    the stop was at r = 1.99974 M (v > c). Chunks rescaled to their own start radius: the stop is at
    2M/(1 - HORIZON_GAP), the speed below c, the proper time the cycloid's."""
    for chunked in (False, True):
        st = osm.OrbitStream(r0, 0.0, 0.0)
        t, evs = 0.0, []
        while not st.done:
            t += 2 * math.pi * r0**1.5 / 8
            evs += st.advance(t if chunked else 1e300, 2.0)["events"]
        e = evs[-1]
        assert e["kind"] == "horizon"
        assert e["r"] == pytest.approx(2.0 / (1 - osm.HORIZON_GAP), rel=1e-12)
        assert -1.0 < e["v_r"] < 0.0
        eta = math.acos(2 * e["r"] / r0 - 1)
        assert e["tau"] == pytest.approx(math.sqrt(r0**3 / 8) * (eta + math.sin(eta)), rel=1e-11)


def test_bound_orbit_beyond_1000_r0_reaches_its_apoapsis():
    """V4-6: a bound orbit with r_apo = 2.96e5 M from r0 = 20 M ended as an «escape» at 1000 r0."""
    r0 = 20.0
    st = osm.OrbitStream(r0, 0.0, 1.3416 * math.sqrt(1 / (r0 - 2)))
    assert st.info["kind"] == "bound" and st.info["r_apo"] > 1e3 * r0 and st.r_far > st.info["r_apo"]
    evs = []
    while len([e for e in evs if e["kind"] == "peri"]) < 2 and not st.done:
        evs += st.advance(1e300, 2.0)["events"]
    assert st.done is None
    apo = [e for e in evs if e["kind"] == "apo"][0]
    assert apo["r"] == pytest.approx(st.info["r_apo"], rel=1e-9)
    st2 = osm.OrbitStream(10.0, 0.4, 0.0)  # a radial throw: the same rule (it rises to its apex and falls)
    assert st2.info["kind"] == "radial_fall" and st2.r_far > st2.info["r_apex"]


def test_second_scheme_drifts_relative_to_the_binding_energy():
    """V4-8: for Mercury |e^2 - 1| = 2.55e-8; the drifts are reported relative to it, with the attainable floor."""
    M = GM_SUN / C**2
    a, ecc = 0.38709893 * AU, 0.20563069
    r0 = a * (1 - ecc) / M
    vp = math.sqrt((1 + ecc) / (r0 - 2.0))
    g = osm.geodesic_tau(r0, 0.0, vp, 2 * math.pi * (a / M) ** 1.5 * 1.2)
    k = osm.local_velocity_to_constants(r0, 0.0, vp)
    assert g["em1"] == pytest.approx(k["em1"], rel=1e-15)
    assert g["binding_floor"] == pytest.approx(2.2e-16 / abs(k["em1"]), rel=1e-12)
    assert g["e_drift_binding"] < 100 * g["binding_floor"] and g["norm_drift_binding"] < 100 * g["binding_floor"]


# --- inside the horizon: the body's proper time on to r = 0 (EX2 design §11 item 34, §7 «E34») -------------------------
def _fall(r0, vr, vp):
    st = osm.OrbitStream(r0, vr, vp)
    while not st.done:
        st.advance(1e300, 2.0)
    assert st.done == "horizon"
    return st


def _cycloid_rest(r0, r):
    """The cycloid's proper time from r to r = 0 (a fall from rest at r0) without the cancellation of
    τ(0) − τ(r) for r ≪ r0: √(r0³/8)(ζ − sin ζ), ζ = π − η = 2 asin √(r/r0), at 40 digits (mpmath)."""
    import mpmath as mp

    with mp.workdps(40):
        z = 2 * mp.asin(mp.sqrt(mp.mpf(r) / r0))
        return float(mp.sqrt(mp.mpf(r0) ** 3 / 8) * (z - mp.sin(z)))


@pytest.mark.parametrize("r0", [2.5, 3.0, 10.0, 20.0, 1e4, 1e8])
def test_radial_fall_from_rest_reaches_the_centre_after_pi_sqrt_r0_cubed_over_8m(r0):
    """τ from rest at r0 to r = 0: π√(r0³/8M) (Blau, eqs. (26.25)-(26.29)), by the quadrature through the horizon; the
    cycloid r = (r0/2)(1 + cos η), τ = √(r0³/8)(η + sin η) at intermediate radii inside the horizon, and Guth's form
    τ(r) = √(r0/2M)(r0 tan⁻¹√((r0 − r)/r) + √(r(r0 − r))) (MIT 8.286 (2013), lecture 15), transcribed separately."""
    ref = math.pi * math.sqrt(r0**3 / 8.0)
    em1 = -2.0 / r0  # e² − 1 at rest at r0: e² = 1 − 2/r0
    assert osm.proper_time_to_centre(em1, 0.0, r0) == pytest.approx(ref, rel=1e-11)
    assert osm.cycloid_proper_time(r0) == pytest.approx(ref, rel=1e-15)
    for r in (1.999, 1.5, 0.5, 1e-3):
        guth = math.sqrt(r0 / 2.0) * (r0 * math.atan(math.sqrt((r0 - r) / r)) + math.sqrt(r * (r0 - r)))
        assert osm.cycloid_proper_time(r0, r) == pytest.approx(guth, rel=1e-13)
        # quad's target is 1e-11; measured 1.1e-11 for r0 = 1e4 down to r = 1e-3 (seven decades in one integral)
        assert osm.proper_time_to_centre(em1, 0.0, r0, r) == pytest.approx(guth, rel=3e-11)
        assert osm.proper_time_to_centre(em1, 0.0, r, 0.0) == pytest.approx(_cycloid_rest(r0, r), rel=1e-10)
        assert _cycloid_rest(r0, r) == pytest.approx(ref - guth, rel=1e-15 * ref / (ref - guth) + 1e-14)


@pytest.mark.parametrize("r0", [10.0, 20.0, 1e6])
def test_the_stream_of_a_radial_fall_goes_on_to_the_centre(r0):
    """The stream stops 2e-6 M above the horizon; interior() carries the body's clock to r = 0: the cycloid's π√(r0³/8)."""
    st = _fall(r0, 0.0, 0.0)
    I = st.interior()
    assert I["r_stop"] == pytest.approx(2.0 / (1 - osm.HORIZON_GAP), rel=1e-12) and I["tau_stop"] == st.tau
    assert I["tau_horizon"] == pytest.approx(osm.cycloid_proper_time(r0, 2.0), rel=1e-11)
    assert I["tau_centre"] == pytest.approx(math.pi * math.sqrt(r0**3 / 8.0), rel=1e-11)
    assert I["dtau_inside"] == pytest.approx(_cycloid_rest(r0, 2.0), rel=1e-10)
    assert I["tau_stop"] < I["tau_horizon"] < I["tau_centre"]


def _tau_by_the_radial_equation(r0, rdot0, l, r_marks):
    """A second method, no quadrature: d²r/dτ² = −1/r² + l²/r³ − 3l²/r⁴ (R'(r)/2, regular at r = 2M) from the start
    (r0, dr/dτ = e v_r) by DOP853, the proper times at which r crosses each of r_marks going inward."""
    from scipy import integrate

    def rhs(tau, Y):
        r = Y[0]
        return [Y[1], -1.0 / r**2 + l * l / r**3 - 3.0 * l * l / r**4]

    evs = []
    for m in r_marks:
        def ev(tau, Y, m=m):
            return Y[0] - m
        ev.direction = -1.0
        evs.append(ev)
    evs[-1].terminal = True
    sol = integrate.solve_ivp(rhs, (0.0, 1e7), [r0, rdot0], method="DOP853", rtol=1e-13, atol=1e-15, events=evs)
    return [float(t[0]) for t in sol.t_events]


@pytest.mark.parametrize("r0,k,alpha", [(7.0, 0.95, 0.0), (5.5, 0.995, 0.0), (8.0, 0.9, 20.0), (30.0, 0.3, -40.0),
                                        (12.0, 0.5, 60.0)])
def test_plunge_proper_time_to_the_centre_three_ways(r0, k, alpha):
    """A plunge with angular momentum (u34's story: from 7 M at 0.95 of the circular speed): the stream to its stop,
    then interior(), against (a) the quadrature from the start to r = 0 (plunge_proper_time, no differential equation),
    (b) mpmath's tanh-sinh quadrature at 30 digits from the stop to r = 0 (another implementation), (c) the radial
    geodesic equation in proper time integrated from the start through the horizon (no quadrature)."""
    import mpmath as mp

    vr, vp = _launch(r0, k, alpha)
    st = _fall(r0, vr, vp)
    assert st.info["kind"] == "plunge" and st.l != 0.0
    I = st.interior()
    # (a) the quadrature from the start: an outward leg to the apoapsis first when v_r > 0
    ref_a = osm.plunge_proper_time(st.em1, st.l, r0, vr, 0.0, st.info["r_apo"])
    assert I["tau_centre"] == pytest.approx(ref_a, rel=1e-9)
    # (b) mpmath from the stop: ∫ dr/√R over [0, 2] and [2, r_stop]
    with mp.workdps(30):
        em1, l = mp.mpf(st.em1), mp.mpf(st.l)

        def f(r):
            return 1 / mp.sqrt(em1 + 2 / r - l * l / r**2 + 2 * l * l / r**3)

        inside = mp.quad(f, [0, 2])
        edge = mp.quad(f, [2, mp.mpf(I["r_stop"])])
    assert I["dtau_inside"] == pytest.approx(float(inside), rel=1e-11)
    assert I["tau_horizon"] - I["tau_stop"] == pytest.approx(float(edge), rel=1e-8)
    # (c) the radial equation in τ, through r = 2M without a stop, to r = 1 and r = 0.01
    t2, t1, t001 = _tau_by_the_radial_equation(r0, st.e * vr, st.l, [2.0, 1.0, 0.01])
    assert t2 == pytest.approx(I["tau_horizon"], rel=1e-9)
    assert t1 == pytest.approx(I["tau_stop"] + osm.proper_time_to_centre(st.em1, st.l, I["r_stop"], 1.0), rel=1e-9)
    assert t001 == pytest.approx(I["tau_stop"] + osm.proper_time_to_centre(st.em1, st.l, I["r_stop"], 0.01), rel=1e-9)
    # and the last 0.01 M takes about (2/5)·0.01^{5/2}/(√2 |l|) (R ≈ 2l²/r³ near r = 0)
    tail = osm.proper_time_to_centre(st.em1, st.l, 0.01, 0.0)
    assert tail == pytest.approx(0.4 * 0.01**2.5 / (math.sqrt(2.0) * abs(st.l)), rel=0.05)


def test_no_fall_inside_the_horizon_lasts_longer_than_pi_m():
    """Inside, R = e² + (2/r − 1)(1 + l²/r²) ≥ 2/r − 1, so τ(2M → 0) ≤ ∫_0^2 dr/√(2/r − 1) = π M (the radial fall
    with e → 0, the cycloid from r0 = 2M); any energy or angular momentum shortens it."""
    assert osm.proper_time_to_centre(1e-12 - 1.0, 0.0, 2.0) == pytest.approx(math.pi, rel=1e-6)
    prev = math.pi
    for e in (0.1, 0.5, 0.9, 1.0, 1.5, 3.0):
        d = osm.proper_time_to_centre(e * e - 1.0, 0.0, 2.0)
        assert d < prev
        prev = d
        for l in (1.0, 3.5, 4.0, 10.0):
            assert osm.proper_time_to_centre(e * e - 1.0, l, 2.0) < d
    # the radial fall from rest: what is left after the horizon, by the cycloid
    for r0 in (3.0, 10.0, 100.0):
        d = osm.proper_time_to_centre(-2.0 / r0, 0.0, 2.0)
        assert d == pytest.approx(_cycloid_rest(r0, 2.0), rel=1e-10)
        assert d < math.pi


def test_interior_refusals_and_where_it_does_not_apply():
    from lfphys.codes import code_of

    # a bound orbit: from its apoapsis inward the body turns at the periapsis, it never reaches r = 0
    st = osm.OrbitStream(20.0, *_launch(20.0, 1.2))
    el = orbits.elements(st.e, abs(st.l))
    with pytest.raises(ValueError) as ex:
        osm.proper_time_to_centre(st.em1, st.l, el["r_apo"], 0.0)
    assert code_of(ex.value) == "orbit.no_fall" and ex.value.data["r"] == pytest.approx(el["r_peri"], rel=1e-9)
    # between the turning points it does
    assert osm.proper_time_to_centre(st.em1, st.l, el["r_apo"], el["r_peri"]) == pytest.approx(
        osm.proper_time_between(st.em1, st.l, el["r_peri"], el["r_apo"]), rel=1e-9)
    for bad in ((10.0, 10.0), (10.0, 12.0), (10.0, -1.0), (math.inf, 0.0)):
        with pytest.raises(ValueError):
            osm.proper_time_to_centre(-0.2, 0.0, *bad)
    with pytest.raises(ValueError):
        osm.cycloid_proper_time(2.0)
    assert st.interior() is None  # not stopped
    hit = osm.OrbitStream(10.0, *_launch(10.0, 0.3), r_stop=5.8)  # a star's surface: nothing inside
    while not hit.done:
        hit.advance(1e300, 2.0)
    assert hit.done == "surface" and hit.interior() is None


@pytest.mark.parametrize("r0", [7.0, 12.0, 20.0, 30.0, 50.0, 100.0])
def test_every_turn_is_counted_once_when_chunks_end_within_a_rounding_of_it(r0):
    """A chunk that ends within a rounding of a full turn (the screens' frame clock does that on a circle: frames every
    T/32, each chunk computed 1/8 of a period ahead) lost the turn or counted it twice: the old bounds floor(psi / 2 pi)
    and the test 0 < p <= p_end rounded two ways (EX2 W34, CI 2026-11-19: 7 of 150 starts perturbed by ulps lost a turn,
    so a circle's period came out 4/3 or 3/2 of Kepler's). Every turn now comes once, in order, at its angle."""
    T_s = 10 * GM_SUN / C**3  # the world's seconds per GM/c³ (10 M☉): its frame times are seconds, converted back
    for j in range(25):
        r = r0 * (1 + j * 2.2e-16)
        v = math.sqrt(1.0 / (r - 2.0))
        T = 2 * math.pi * r**1.5
        step = T * T_s / 8.0 / 4.0  # a period in 8 played seconds at 4 frames per second, in world seconds
        s = osm.OrbitStream(r, 0.0, v)
        laps = [e for e in s.advance(T / 8, max_turns=2.0)["events"] if e["kind"] == "lap"]
        for k in range(1, 4 * 32 + 3):
            t = k * step / T_s
            while s.t < t and not s.done:
                laps += [e for e in s.advance(max(t, s.t) + T / 8, max_turns=2.0)["events"] if e["kind"] == "lap"]
        assert [e["n"] for e in laps] == list(range(1, len(laps) + 1)) and len(laps) >= 4, (j, [e["n"] for e in laps])
        for e in laps:
            assert e["psi"] == pytest.approx(2 * math.pi * e["n"], abs=1e-9)
            assert e["t"] == pytest.approx(e["n"] * T, rel=1e-10)
