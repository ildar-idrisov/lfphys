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
