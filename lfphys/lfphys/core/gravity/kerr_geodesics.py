# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Kerr and Kerr-Newman geodesics in Boyer-Lindquist coordinates: the metric, the constants of motion of a state, and a
general Hamiltonian integrator (plan P7; the hole's charge q since P15.1, review B6-G17) - the independent second route
for the closed-form null and timelike geodesics (``kerr_null``, ``kerr_orbits``) and the integrator for any initial
state.

Units G = c = M = 1, a = chi. Sigma = r^2 + a^2 cos^2 theta, Delta = r^2 - 2 r + a^2 + q^2, where q is the charge of
the hole (Kerr-Newman; q = 0, the default, is Kerr; every function takes ``q``; Adamo & Newman 2014, Scholarpedia
9(10), 31791, arXiv:1410.6626, Eq. 2.19 and the definitions below it). Neutral test bodies and photons only: the
electromagnetic field of the hole does not act on them, and the charge enters only through Delta (and g_t phi, g_tt
through 2 r - q^2 = r^2 + a^2 - Delta). With covariant momentum p = (p_t, p_r, p_theta, p_phi), E = -p_t, L = p_phi:

    2 Sigma H = Sigma g^{mu nu} p_mu p_nu = Delta p_r^2 + p_theta^2 - P^2/Delta + W^2/sin^2 theta,
    P = (r^2 + a^2) E - a L,  W = L - a E sin^2 theta,

(Carter 1968; the separated Hamilton-Jacobi form; with q: Hackmann & Xu 2013, PRD 87, 124030, Eqs. 11-16 at e = 0),
H = -mu^2/2 on shell (mu = 1 timelike, 0 null). Carter's constant
Q = p_theta^2 + cos^2 theta [a^2 (mu^2 - E^2) + L^2/sin^2 theta]. In Mino time (d/dtau = Sigma d/dsigma):

    dr/dtau = Delta p_r,  dtheta/dtau = p_theta,  dphi/dtau = a P/Delta + W/sin^2 theta,
    dt/dtau = (r^2 + a^2) P/Delta + a W,  dp_r/dtau = -Sigma dH/dr,  dp_theta/dtau = -Sigma dH/dtheta,

integrated by DOP853 (SciPy) with tolerances set by the caller. E and L are constant by construction (t and phi are
cyclic); H and Q drift only with the integration error and are monitored: that is the check of conservation.
This route uses no root, no elliptic function and no separation constant other than E and L, so it is independent of
the closed forms it checks.
"""

from __future__ import annotations

import math

import numpy as np

ABOUT = {
    "layer": "core", "kind": "numerical solution",
    "title": "Геодезические Керра и Керра–Ньюмена: метрика, интегралы движения, гамильтоново интегрирование",
    "statement": "Метрика Керра–Ньюмена (спин a, заряд дыры q; q = 0 — Керр) в координатах Бойера–Линдквиста, E, "
                 "L_z и постоянная Картера Q по состоянию (x, p), гамильтоновы уравнения движения во времени Мино "
                 "для любых геодезических нейтральных тел и света (светоподобных и времениподобных), интегрирование "
                 "DOP853 — независимый второй путь для замкнутых решений.",
    "validity": "вакуумное решение ОТО, |a| < M (с зарядом q дыры — решение Керра–Ньюмена, a² + q² < M², "
                "нейтральные пробные тела и фотоны), внешняя область r > r₊; ошибка — допуск интегратора DOP853 "
                "(контролируется сохранением H и Q)",
    "basis": ["Kerr, PRL 11, 237 (1963)", "Carter, Phys. Rev. 174, 1559 (1968)",
              "Hairer, Nørsett, Wanner, Solving ODE I (DOP853)",
              "Adamo & Newman, Scholarpedia 9, 31791 (2014), arXiv:1410.6626 (метрика Керра–Ньюмена)"],
    "conflicts": [],
}


def metric(r, theta, chi, q=0.0):
    """Covariant g_{mu nu} (t, r, theta, phi) at (r, theta): 4 x 4 (scalar r, theta)."""
    a = chi
    s2 = math.sin(theta) ** 2
    sig = r * r + a * a * math.cos(theta) ** 2
    dl = r * r - 2.0 * r + a * a + q * q
    m2 = 2.0 * r - q * q
    g = np.zeros((4, 4))
    g[0, 0] = -(1.0 - m2 / sig)
    g[0, 3] = g[3, 0] = -a * m2 * s2 / sig
    g[1, 1] = sig / dl
    g[2, 2] = sig
    g[3, 3] = (r * r + a * a + a * a * m2 * s2 / sig) * s2
    return g


def inverse_metric(r, theta, chi, q=0.0):
    a = chi
    s2 = math.sin(theta) ** 2
    sig = r * r + a * a * math.cos(theta) ** 2
    dl = r * r - 2.0 * r + a * a + q * q
    g = np.zeros((4, 4))
    g[0, 0] = -((r * r + a * a) ** 2 - a * a * dl * s2) / (sig * dl)
    g[0, 3] = g[3, 0] = -a * (2.0 * r - q * q) / (sig * dl)
    g[1, 1] = dl / sig
    g[2, 2] = 1.0 / sig
    g[3, 3] = (dl - a * a * s2) / (sig * dl * s2)
    return g


def two_sigma_h(r, theta, p_r, p_th, E, L, chi, q=0.0):
    """N = 2 Sigma H (= -mu^2 Sigma on shell)."""
    a = chi
    s2 = np.sin(theta) ** 2
    dl = r * r - 2.0 * r + a * a + q * q
    P = (r * r + a * a) * E - a * L
    W = L - a * E * s2
    return dl * p_r * p_r + p_th * p_th - P * P / dl + W * W / s2


def constants(r, theta, p_r, p_th, E, L, chi, mu2=None, q=0.0):
    """(mu^2, Q) of a state: mu^2 = -2H, Q = p_theta^2 + cos^2 theta [a^2 (mu^2 - E^2) + L^2/sin^2 theta]
    (mu2 given: that value is used in Q)."""
    a = chi
    sig = r * r + a * a * np.cos(theta) ** 2
    m2 = -two_sigma_h(r, theta, p_r, p_th, E, L, chi, q) / sig
    use = m2 if mu2 is None else mu2
    c2 = np.cos(theta) ** 2
    return m2, p_th * p_th + c2 * (a * a * (use - E * E) + L * L / np.sin(theta) ** 2)


def _rhs(chi, E, L, q=0.0):
    a = chi
    q2 = q * q

    def f(tau, y):
        t, r, th, ph, pr, pth = y
        s, c = math.sin(th), math.cos(th)
        s2 = s * s
        sig = r * r + a * a * c * c
        dl = r * r - 2.0 * r + a * a + q2
        P = (r * r + a * a) * E - a * L
        W = L - a * E * s2
        N = dl * pr * pr + pth * pth - P * P / dl + W * W / s2
        dN_dr = (2.0 * r - 2.0) * pr * pr - 2.0 * P * (2.0 * r * E) / dl + P * P * (2.0 * r - 2.0) / (dl * dl)
        dN_dth = 2.0 * W * (-2.0 * a * E * s * c) / s2 - 2.0 * W * W * c / (s2 * s)
        dsig_dr = 2.0 * r
        dsig_dth = -2.0 * a * a * s * c
        # Sigma dH/dx = dN/dx / 2 - N dSigma/dx / (2 Sigma)
        return [(r * r + a * a) * P / dl + a * W,
                dl * pr,
                pth,
                a * P / dl + W / s2,
                -(0.5 * dN_dr - 0.5 * N * dsig_dr / sig),
                -(0.5 * dN_dth - 0.5 * N * dsig_dth / sig)]
    return f


def integrate(chi, x0, p0, tau_max, rtol=1e-12, atol=1e-14, events=None, dense=False, max_step=np.inf, q=0.0):
    """Integrate the geodesic from x0 = (t, r, theta, phi) with covariant p0 = (p_t, p_r, p_theta, p_phi) over Mino
    time [0, tau_max] (tau_max < 0: backwards). ``events``: callables ev(tau, y) with y = (t, r, theta, phi, p_r,
    p_theta) (SciPy's event protocol). Returns the SciPy solution with E, L attached."""
    from scipy.integrate import solve_ivp
    E, L = -float(p0[0]), float(p0[3])
    y0 = [float(x0[0]), float(x0[1]), float(x0[2]), float(x0[3]), float(p0[1]), float(p0[2])]
    sol = solve_ivp(_rhs(chi, E, L, q), (0.0, tau_max), y0, method="DOP853", rtol=rtol, atol=atol, events=events,
                    dense_output=dense, max_step=max_step)
    sol.E, sol.L = E, L
    return sol


def null_momentum(r, theta, lam, eta, chi, sign_r, sign_theta, E=1.0, q=0.0):
    """Covariant momentum of a photon with (lambda, eta) at (r, theta): p_r = sign_r sqrt(R)/Delta,
    p_theta = sign_theta sqrt(Theta) (times E)."""
    a = chi
    dl = r * r - 2.0 * r + a * a + q * q
    R = (r * r + a * a - a * lam) ** 2 - dl * (eta + (lam - a) ** 2)
    c = math.cos(theta)
    Th = eta + a * a * c * c - lam * lam * c * c / math.sin(theta) ** 2
    return np.array([-E, sign_r * math.sqrt(max(R, 0.0)) / dl * E, sign_theta * math.sqrt(max(Th, 0.0)) * E,
                     lam * E])
