# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Independent routes for the Kerr image tests (review B5-K12): a screen ray integrated by Hamilton's equations from
far away with its equatorial crossings and radial turning point as events, and an equatorial emitter built from the
metric. Shares no closed form with ``kerr_null``/``kerr_shadow`` (no roots, no elliptic function, no Bardeen formula
for the emitter's velocity)."""

import math

import mpmath as mp
import numpy as np

from lfphys.core.gravity import kerr, kerr_geodesics as KG, kerr_null as KN


def hamilton_screen_ray(al, be, theta_o, chi, r0=1e7, rtol=1e-12, tau_max=200.0):
    """The photon reaching the screen point (alpha, beta) of a distant observer at theta_o, integrated backwards in
    Mino time from r = r0 by ``kerr_geodesics.integrate`` (DOP853). The start: the ray from infinity passes r0 at
    theta_o - beta/r0 + O(1/r0^2) (backwards, dtheta/dtau = -beta at the observer and tau(r0) = 1/r0 + O(r0^-3)), with
    the forward momentum (p_r > 0, sign p_theta = sign beta). Returns a dict: ``cross`` (rows t, r, theta, phi, p_r,
    p_theta at each equatorial crossing, in order), ``tau_cross`` (Mino time from infinity), ``tau_turn`` (Mino
    time of the radial turning point from infinity, NaN if none), ``captured``, ``lam``, ``eta``."""
    lam, eta = (float(v) for v in KN.screen_to_constants(al, be, theta_o, chi))
    th0 = theta_o - be / r0
    p0 = KG.null_momentum(r0, th0, lam, eta, chi, 1.0, math.copysign(1.0, be))
    rp = KN.horizon(chi)

    def ev_eq(t, y):
        return math.cos(y[2])

    def ev_turn(t, y):
        return y[4]

    def ev_h(t, y):
        return y[1] - rp - 1e-4
    ev_h.terminal = True

    def ev_far(t, y):
        return y[1] - 2.0 * r0
    ev_far.terminal = True
    sol = KG.integrate(chi, [0.0, r0, th0, 0.0], p0, -tau_max, rtol=rtol, atol=rtol * 1e-2,
                       events=[ev_eq, ev_turn, ev_h, ev_far])
    with mp.workdps(25):  # Mino time from infinity to r0
        a = mp.mpf(chi)
        A, B, C = a * a - eta - lam * lam, 2 * (eta + (lam - chi) ** 2), -a * a * eta
        off = float(mp.quad(lambda u: 1 / mp.sqrt(1 + A * u * u + B * u ** 3 + C * u ** 4), [0, 1 / mp.mpf(r0)]))
    cross = np.reshape(sol.y_events[0], (-1, 6))
    turn = np.asarray(sol.t_events[1])
    return {"cross": cross, "tau_cross": off - np.asarray(sol.t_events[0]),
            "tau_turn": (off - turn[0]) if turn.size else math.nan, "captured": len(sol.t_events[2]) > 0,
            "lam": lam, "eta": eta}


def emitter_four_velocity(r, chi, prograde=True, model="cunningham"):
    """(u^t, u^r, u^theta, u^phi) of the equatorial emitter at r built from the metric: Keplerian
    Omega = +-1/(r^(3/2) +- a) and u^t from the normalisation outside the ISCO; inside it (Cunningham) the ISCO's
    u_t = -E, u_phi = L (``kerr.circular_e_l`` at ``kerr.isco``) raised by the inverse metric and u^r < 0 from the
    normalisation. None where the model has no emitter."""
    a = chi
    s = 1.0 if prograde else -1.0
    r_isco = kerr.isco(chi, prograde)
    if r >= r_isco:
        g = KG.metric(r, math.pi / 2, chi)
        om = s / (r ** 1.5 + s * a)
        ut = 1.0 / math.sqrt(-(g[0, 0] + 2 * g[0, 3] * om + g[3, 3] * om * om))
        return np.array([ut, 0.0, 0.0, om * ut])
    if model == "keplerian":
        return None
    E, L = kerr.circular_e_l(r_isco, chi, prograde)
    gi = KG.inverse_metric(r, math.pi / 2, chi)
    ut = gi[0, 0] * (-E) + gi[0, 3] * L
    up = gi[3, 0] * (-E) + gi[3, 3] * L
    # g_rr (u^r)^2 = -1 - (u_t u^t + u_phi u^phi)
    g = KG.metric(r, math.pi / 2, chi)
    ur2 = (-1.0 - (-E * ut + L * up)) / g[1, 1]
    return np.array([ut, -math.sqrt(max(ur2, 0.0)), 0.0, up])
