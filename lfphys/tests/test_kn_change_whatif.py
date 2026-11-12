# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The declared "what if" of a Kerr-Newman hole's spin or charge changed at an instant
(``theories.alternatives.kn_change_whatif``; review LB1-physics P5, P6): the rule's invariants against independent
routes of the core — the ZAMO-measured velocity read back by ``Geodesics.zamo_velocity`` (through E, L, p_r, p_theta),
a photon's ZAMO frequency, the mass shell; a closed form (a body at rest for its ZAMO in Schwarzschild carried into
Reissner-Nordstrom: E = sqrt(1 - 2/r + Q^2/r^2)); the identity (the same metric gives the same state); no limit below
c (the clamp at 0.999 c that the world's former rule applied is a negative control); the refusals."""

import math

import numpy as np
import pytest

from lfphys.core.gravity import kerr_newman as KN
from lfphys.theories.alternatives import kn_change_whatif as WI

U = 2.0 ** -53


def _world(chi=0.5, q=0.2):
    g = KN.Geodesics(chi, q, capture_eps=1e-4)
    g.add_body(6.0, 1.3, 0.2, v=[0.1, -0.05, 0.4], key="a")
    g.add_body(9.0, 1.9, 2.0, v=[-0.3, 0.1, 0.2], key="b")
    g.add_photon(12.0, 1.1, 0.5, n=[-0.7, 0.2, 0.4], key="ray", nu=2.5)
    g.advance(15.0)
    return g


def _shell_tol(g):
    """Per body, how far the rule's frame energy sqrt(mu^2 + |p^(i)|^2) may lie from the integrated one: the body's own
    mass-shell drift dmu2 (e_old^2 - e^2 = dmu2, so |e_old - e| <= |dmu2| / (2 e)), plus rounding."""
    c = g.constants()
    e = np.array([KN.zamo_frame_momentum(*g.bl()[i, :2], g.chi, g.q, g.momenta()[i])[0] for i in range(g.n)])
    return np.abs(c["dmu2"]) / (2 * e) * 1.01 + 64 * U * e, e


def test_the_same_metric_gives_back_the_same_state():
    """(a, Q) unchanged: positions, proper times and statuses bit for bit; the spatial momenta to rounding (the frame and
    back); the energy re-taken from the mass shell, so E moves by the body's own shell drift (the integration's, within
    its budget: ~1e-10 for the photon here) and no more; L, K to rounding; the old Geodesics untouched."""
    g = _world()
    y0 = g.state_dict()
    tol, _ = _shell_tol(g)
    out = WI.carry(g, g.chi, g.q)
    h = out["geodesics"]
    assert h.keys == g.keys and h.t == g.t and h.status() == g.status()
    assert np.array_equal(h.bl(), g.bl()) and np.array_equal(h.proper_time(), g.proper_time())
    dp = np.abs(h.momenta() - g.momenta())
    assert np.all(dp[:, 1:] <= 16 * U * (np.abs(g.momenta()[:, 1:]) + 1.0))
    assert np.all(dp[:, 0] <= tol), (dp[:, 0], tol)
    for b in out["bodies"]:
        assert abs(b["L_new"] - b["L"]) <= 16 * U * (1 + abs(b["L"])) and b["varpi_new"] == b["varpi"]
    assert g.state_dict() == y0


@pytest.mark.parametrize("chi1,q1", [(0.9, 0.0), (0.2, 0.6), (0.0, 0.0), (0.7, 0.7)])
def test_the_zamo_velocity_and_a_photons_frequency_are_kept(chi1, q1):
    """The rule keeps the ZAMO-measured momentum (energy from the shell): ``zamo_velocity`` of the new geodesics — an
    independent route through the new E, L, p_r, p_theta — equals the old to the body's own shell drift (|dv| <=
    |v| |dmu2| / (2 e^2): 4e-11 for the photon here) and rounding; the photon's ZAMO frequency (E - omega L)/alpha stays
    its integrated value; the new mass shells are 1 and 0 to rounding; E and L do change (the metric did)."""
    g = _world()
    v0 = g.zamo_velocity()
    tol, e = _shell_tol(g)
    out = WI.carry(g, chi1, q1)
    h = out["geodesics"]
    dv = np.max(np.abs(h.zamo_velocity() - v0), axis=1)
    assert np.all(dv <= tol / e + 64 * U), (dv, tol / e)
    c = h.constants()
    assert np.max(np.abs(c["dmu2"]) / c["shell_scale"]) <= 64 * U
    i = h.keys.index("ray")
    r, th = h.bl()[i, :2]
    z = KN.zamo(r, th, chi1, q1)
    nu = (c["E"][i] - z["omega"] * c["L"][i]) / z["alpha"]
    assert abs(nu - e[i]) <= tol[i], (nu, e[i])  # its frequency at the change (2.5 at its start; it fell since)
    assert out["max_dE"] > 1e-4


def test_closed_form_schwarzschild_to_reissner_nordstrom():
    """A body at rest for its ZAMO (v = 0) in Schwarzschild at r = 5 carried into Reissner-Nordstrom with Q = 0.8 keeps
    v = 0, so E = alpha = sqrt(1 - 2/r + Q^2/r^2) (the static observer's lapse; closed form), L = 0; a body moving
    tangentially with v_phi = 0.3 gets L = r gamma v_phi (varpi = r at a = 0) and E = alpha gamma."""
    g = KN.Geodesics(0.0, 0.0)
    g.add_body(5.0, 1.2, 0.0, v=[0.0, 0.0, 0.0], key="rest")
    g.add_body(5.0, math.pi / 2, 1.0, v=[0.0, 0.0, 0.3], key="moving")
    q = 0.8
    out = WI.carry(g, 0.0, q)
    c = out["geodesics"].constants()
    al = math.sqrt(1 - 2 / 5 + q * q / 25)
    gam = 1 / math.sqrt(1 - 0.09)
    assert abs(c["E"][0] - al) <= 8 * U and c["L"][0] == 0.0
    assert abs(c["E"][1] - al * gam) <= 16 * U and abs(c["L"][1] - 5 * gam * 0.3) <= 16 * U * 5


def test_no_limit_below_c_near_the_horizon():
    """Review LB1-physics P6: a body falling at gamma = 22.4 just outside the horizon of a = 0.9 (r - r+ = 4.1e-4), carried
    into a = 0.95, keeps its gamma and |v| to 1e-12 (the former world rule clamped |v| to 0.999 and reported nothing:
    gamma 22.37; the control below shows that clamp moves |v| by 3e-6, far outside what is held here)."""
    g = KN.Geodesics(0.9, 0.0, capture_eps=1e-4)
    rp = KN.horizons(0.9, 0.0)[0]
    v = 0.999003
    g.add_body(rp + 4.1e-4, math.pi / 2, 0.0, v=[-v, 0.0, 0.0], key="faller")
    gam = 1 / math.sqrt(1 - v * v)
    out = WI.carry(g, 0.95, 0.0)
    b = out["bodies"][0]
    assert abs(b["gamma"] - gam) <= 1e-9 * gam and abs(b["v"] - v) <= 1e-12
    vz = out["geodesics"].zamo_velocity()[0]
    assert abs(np.linalg.norm(vz) - v) <= 1e-12
    clamped = v * min(1.0, 0.999 / v)  # the former rule: v * min(1, 0.999/|v|)
    assert abs(clamped - v) > 1e-6


def test_refusals_leave_the_world_as_it_was():
    """No horizon (a^2 + Q^2 >= 1) and an active body inside the new capture radius are refused (``Refused`` naming the
    body); the old geodesics are untouched; a captured body stays captured just outside the new, larger horizon."""
    g = KN.Geodesics(0.9, 0.0, capture_eps=1e-4)
    rp = KN.horizons(0.9, 0.0)[0]
    g.add_body(rp + 0.05, math.pi / 2, 0.0, v=[-0.2, 0.0, 0.0], key="near")
    g.add_body(8.0, 1.0, 0.0, key="far")
    d0 = g.state_dict()
    with pytest.raises(WI.Refused) as e:
        WI.carry(g, 0.9, 0.5)
    assert e.value.key is None and "горизонт" in str(e.value)
    with pytest.raises(WI.Refused) as e:
        WI.carry(g, 0.0, 0.0)  # r+ = 2 > the body's r
    assert e.value.key == "near" and e.value.hint
    assert g.state_dict() == d0
    g.advance(200.0)
    assert g.status()[0] == "captured"
    out = WI.carry(g, 0.0, 0.0)
    h = out["geodesics"]
    assert h.status()[0] == "captured" and h.bl()[0, 0] == 2.0 + 1e-4


def test_observer_refusal():
    """A static observer inside the new ergosurface, a circular one inside the new ISCO, any inside the new horizon."""
    assert WI.observer_refusal("static", 1.9, math.pi / 2, 0.9, 0.0) is not None  # ergosurface r = 2 at the equator
    assert WI.observer_refusal("static", 2.1, math.pi / 2, 0.9, 0.0) is None
    assert WI.observer_refusal("circular", 5.0, math.pi / 2, 0.0, 0.0) is not None  # ISCO 6
    assert WI.observer_refusal("circular", 5.0, math.pi / 2, 0.5, 0.0) is None  # ISCO 4.233
    assert WI.observer_refusal("zamo", 1.5, math.pi / 2, 0.0, 0.0) is not None
    assert WI.observer_refusal("zamo", 1.5, math.pi / 2, 0.9, 0.0) is None
