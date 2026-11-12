# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review B5, check c03: the image pipeline end to end (kerr_shadow.trace_screen: fate, r_n, g_n for n = 0, 1, 2)
# against a route that shares no code with the engine:
#   * the photon: Hamilton's equations in Mino time with the reviewer's own inverse Boyer-Lindquist metric; the
#     derivatives dH/dr, dH/dtheta by the complex-step method (exact to round-off, no hand-derived formula); DOP853
#     started at r0 = 1e7 at theta_o - beta/r0 (where the ray from infinity passes r0) with the photon's forward momentum (p^theta sign = sign beta),
#     integrated backwards; equatorial crossings by events, in order;
#   * the gas: Keplerian circular orbits by Omega = +-1/(r^1.5 +- a) and u^t from the normalisation with the reviewer's
#     metric; inside the ISCO the plunge with the ISCO's u_t, u_phi raised by the reviewer's inverse metric and u^r
#     from the normalisation (r_isco found as the minimum of the circular-orbit energy by brentq, not from the BPT
#     formula); for prograde gas also the closed form of Gralla, Lupsasca & Marrone 2020 App. B (B9-B14) as a cross
#     check;
#   * g = 1/(-p.u).
# The two routes are compared pixel by pixel (relative difference of r_n and g_n; the start at finite r0 and the
# integrator tolerance give ~1e-7).
#
# Root: engine at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this script in
# /lf/reviews/archive/2026-10-29_internal_B5-kerr-v15/. CPU. Run as c02 (see its header).
import math

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, minimize_scalar

from lfphys.core.gravity import kerr_shadow as KS


def ginv(r, th, a):
    s2 = np.sin(th) ** 2
    sig = r * r + a * a * np.cos(th) ** 2
    dl = r * r - 2 * r + a * a
    G = {}
    G["tt"] = -((r * r + a * a) ** 2 - a * a * dl * s2) / (sig * dl)
    G["tp"] = -2 * a * r / (sig * dl)
    G["rr"] = dl / sig
    G["hh"] = 1 / sig
    G["pp"] = (dl - a * a * s2) / (sig * dl * s2)
    return G


def gcov(r, th, a):
    s2 = np.sin(th) ** 2
    sig = r * r + a * a * np.cos(th) ** 2
    return {"tt": -(1 - 2 * r / sig), "tp": -2 * a * r * s2 / sig,
            "pp": (r * r + a * a + 2 * a * a * r * s2 / sig) * s2, "rr": sig / (r * r - 2 * r + a * a)}


def H(r, th, pr, ph, E, L, a):
    G = ginv(r, th, a)
    return 0.5 * (G["tt"] * E * E - 2 * G["tp"] * E * L + G["pp"] * L * L + G["rr"] * pr * pr + G["hh"] * ph * ph)


def rhs(a, E, L):
    h = 1e-20

    def f(tau, y):
        t, r, th, phi, pr, ph = y
        sig = r * r + a * a * math.cos(th) ** 2
        G = ginv(r, th, a)
        dHr = H(complex(r, h), th, pr, ph, E, L, a).imag / h
        dHt = H(r, complex(th, h), pr, ph, E, L, a).imag / h
        return [sig * (-G["tt"] * E + G["tp"] * L), sig * G["rr"] * pr, sig * G["hh"] * ph,
                sig * (-G["tp"] * E + G["pp"] * L), -sig * dHr, -sig * dHt]
    return f


def photon_crossings(al, be, th_o, a, r0=1e7):
    flip = th_o > math.pi / 2
    lam = -al * math.sin(th_o)
    eta = (al * al - a * a) * math.cos(th_o) ** 2 + be * be
    # forward momentum at the observer: p_r > 0 (outgoing), p_theta sign = sign(beta)
    dl = r0 * r0 - 2 * r0 + a * a
    Rr = (r0 * r0 + a * a - a * lam) ** 2 - dl * (eta + (lam - a) ** 2)
    # the ray from infinity is at theta = theta_o - beta/r0 + O(1/r0^2) when it passes r0 (dtheta/dtau = -beta
    # backwards, Mino time ~ 1/r0 from infinity): start there, so that the start adds no O(beta/r0) offset
    th0 = th_o - be / r0
    c, s = math.cos(th0), math.sin(th0)
    Th = eta + a * a * c * c - lam * lam * c * c / (s * s)
    pr = math.sqrt(Rr) / dl
    ph = math.copysign(math.sqrt(max(Th, 0.0)), be)
    rp = 1 + math.sqrt(1 - a * a)

    def ev_eq(t, y):
        return math.cos(y[2])

    def ev_h(t, y):
        return y[1] - rp - 1e-4
    ev_h.terminal = True

    def ev_far(t, y):
        return y[1] - 2 * r0
    ev_far.terminal = True
    sol = solve_ivp(rhs(a, 1.0, lam), (0, -100.0), [0, r0, th0, 0, pr, ph], method="DOP853", rtol=1e-12,
                    atol=1e-14, events=[ev_eq, ev_h, ev_far])
    cr = np.reshape(sol.y_events[0], (-1, 6))
    captured = len(sol.t_events[1]) > 0
    return lam, eta, cr, captured


def circ(r, a, s):
    om = s / (r ** 1.5 + s * a)
    g = gcov(r, math.pi / 2, a)
    ut = 1 / math.sqrt(-(g["tt"] + 2 * g["tp"] * om + g["pp"] * om * om))
    return ut, om * ut


def circ_energy(r, a, s):
    ut, up = circ(r, a, s)
    g = gcov(r, math.pi / 2, a)
    return -(g["tt"] * ut + g["tp"] * up), g["tp"] * ut + g["pp"] * up


def r_isco(a, s):
    rph = 2 * (1 + math.cos(2 / 3 * math.acos(-s * a)))
    res = minimize_scalar(lambda r: circ_energy(r, a, s)[0], bounds=(rph * 1.001 + 0.01, 12.0), method="bounded",
                          options={"xatol": 1e-12})
    # polish: dE/dr = 0 by brentq on a central difference
    h = 1e-6
    d = lambda r: (circ_energy(r + h, a, s)[0] - circ_energy(r - h, a, s)[0]) / (2 * h)  # noqa: E731
    return brentq(d, res.x - 0.05, res.x + 0.05, xtol=1e-13)


def emitter(r, a, s, model, risco):
    if r >= risco:
        ut, up = circ(r, a, s)
        return ut, 0.0, up
    if model == "keplerian":
        return None
    E, L = circ_energy(risco, a, s)
    G = ginv(r, math.pi / 2, a)
    ut = -G["tt"] * E + G["tp"] * L
    up = -G["tp"] * E + G["pp"] * L
    ur2 = (-1 - (G["tt"] * E * E - 2 * G["tp"] * E * L + G["pp"] * L * L)) / G["rr"]
    ur_low = -math.sqrt(max(ur2, 0.0))  # covariant u_r
    return ut, G["rr"] * ur_low, up


def glm_plunge(r, a, risco):
    """Gralla, Lupsasca & Marrone 2020 App. B (B8-B14), prograde, M = 1."""
    lms = (risco ** 2 - 2 * a * math.sqrt(risco) + a * a) / (risco ** 1.5 - 2 * math.sqrt(risco) + a)
    gms = math.sqrt(1 - 2 / (3 * risco))
    dl = r * r - 2 * r + a * a
    Hh = (2 * r - a * lms) / dl
    ur = -math.sqrt(2 / (3 * risco)) * (risco / r - 1) ** 1.5
    up = gms / r ** 2 * (lms + a * Hh)
    ut = gms * (1 + 2 / r * (1 + Hh))
    return ut, ur, up


def main():
    out = []
    worst = {"r": 0.0, "g": 0.0, "fate": 0, "count": 0, "glm": 0.0}
    rng = np.random.default_rng(12)
    cases = [(0.9, 17.0, "cunningham", True), (0.9, 60.0, "cunningham", True), (0.998, 89.0, "cunningham", True),
             (0.9, 163.0, "cunningham", True), (0.7, 45.0, "keplerian", False), (0.95, 75.0, "cunningham", False),
             (0.3, 30.0, "keplerian", True)]
    for chi, thd, model, pro in cases:
        th = math.radians(thd)
        s = 1.0 if pro else -1.0
        risco = r_isco(chi, s)
        if pro:
            rh = 1 + math.sqrt(1 - chi * chi)
            for r in (rh + 0.05 * (risco - rh), rh + 0.5 * (risco - rh), rh + 0.95 * (risco - rh)):
                mine = emitter(r, chi, s, "cunningham", risco)
                glm = glm_plunge(r, chi, risco)
                worst["glm"] = max(worst["glm"], max(abs(x - y) for x, y in zip(mine, glm)) / abs(glm[0]))
        pts = [(rng.uniform(-9, 9), rng.uniform(-9, 9)) for _ in range(14)]
        al = np.array([p[0] for p in pts])
        be = np.array([p[1] for p in pts])
        eng = KS.trace_screen(al, be, th, chi, 2, model, pro)
        for i in range(len(pts)):
            lam, eta, cr, cap = photon_crossings(al[i], be[i], th, chi)
            worst["count"] += 1
            if cap != bool(eng["captured"][i]):
                worst["fate"] += 1
                out.append(f"FATE differs: chi={chi} th={thd} ({al[i]:.4f}, {be[i]:.4f}) engine {eng['captured'][i]} ode {cap}")
            for n in range(3):
                rn = eng["r_n"][n][i]
                if n >= len(cr):
                    if not math.isnan(rn):
                        out.append(f"  engine has crossing n={n} r={rn:.6g}, ODE none ({al[i]:.4f},{be[i]:.4f})")
                    continue
                r_ode = cr[n][1]
                pr_ode = cr[n][4]
                if math.isnan(rn):
                    out.append(f"  ODE crossing n={n} r={r_ode:.6g} missing in engine ({al[i]:.4f},{be[i]:.4f})")
                    continue
                worst["r"] = max(worst["r"], abs(rn - r_ode) / r_ode)
                if abs(rn - r_ode) / r_ode > 1e-6:
                    out.append(f"  r_n differs: chi={chi} th={thd} ({al[i]:.6f},{be[i]:.6f}) n={n} engine {rn:.10g} "
                               f"ODE {r_ode:.10g} (ray lambda {lam:.6g}, eta {eta:.6g})")
                u = emitter(r_ode, chi, s, model, risco)
                g_eng = eng["g_n"][n][i]
                if u is None:
                    if not math.isnan(g_eng):
                        out.append(f"  engine g at r={rn:.6g} inside ISCO for Keplerian gas")
                    continue
                ut, ur, up = u
                # covariant p: p_t = -1, p_phi = lam, p_r from the state (forward momentum)
                g_ode = 1.0 / (ut - lam * up - pr_ode * ur)
                rel = abs(g_eng - g_ode) / g_ode
                worst["g"] = max(worst["g"], rel)
                if rel > 1e-5:
                    out.append(f"  g differs: chi={chi} th={thd} {model} pro={pro} ({al[i]:.4f},{be[i]:.4f}) n={n} "
                               f"r={r_ode:.6g} engine {g_eng:.10g} ode {g_ode:.10g} (p_r {pr_ode:+.3g})")
        out.append(f"case chi={chi} th={thd} {model} {'pro' if pro else 'retro'}: r_isco(review) {risco:.12g}; done")
    out.append(f"pixels {worst['count']}; fate mismatches {worst['fate']}; max rel |r_n engine - ODE| {worst['r']:.2e}; "
               f"max rel |g_n engine - ODE| {worst['g']:.2e}; reviewer plunge vs GLM 2020 App. B (max |du|/u^t): {worst['glm']:.2e}")
    print("\n".join(out))


if __name__ == "__main__":
    main()
