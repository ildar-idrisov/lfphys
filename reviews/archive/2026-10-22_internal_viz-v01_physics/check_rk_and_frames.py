"""Independent check of v01 RK geodesic fans (light.trace_gr), their initial conditions, aberration and the
frame matrices (laws.frame_matrix, light.aberrate_sr, Laws.emit_velocities, light.local_velocity_static_frame).

Reviewer script (2026-10-22). Independent routes:
* reference geodesics: scipy solve_ivp DOP853 (rtol 1e-13) of the POLAR second-order equations
  r'' = L^2/r^3 - 1.5 rs L^2/r^4, phi' = L/r^2, (ct)' = 1/f (not the engine's Cartesian central-force form);
  every stored RK vertex is compared with the reference at the same azimuth (r and ct);
* initial conditions: the photon 4-momentum built in the emitter's rest frame, boosted to the static frame by
  an explicit textbook boost (written here), then mapped to coordinate components with the tetrad
  e_t = 1/sqrt(f) d_t, e_r = sqrt(f) d_r, e_phi = (1/r) d_phi;
* aberration: closed form cos(theta_lab) = (cos(theta') + beta)/(1 + beta cos(theta')) for the angle to v;
* linear interpolation in t between stored vertices (what the browser does) vs the exact position at that t.

Run:
  docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server \
      light-funnel-viz python3 /lf/reviews/2026-10-22_internal_viz-v01_physics/check_rk_and_frames.py
"""
from __future__ import annotations

import argparse
import math

import numpy as np
from scipy.integrate import solve_ivp

from v01_light_travel.engine import light
from v01_light_travel.engine.consts import C, GM_SUN
from v01_light_travel.engine.laws import Laws


def boost_textbook(beta_vec):
    """Lorentz boost Lambda(beta) as in Jackson eq. (11.98): maps (ct, x) of frame K to K' moving with +beta."""
    b = np.asarray(beta_vec, float)
    b2 = b @ b
    g = 1 / math.sqrt(1 - b2)
    L = np.eye(3)
    L[0, 0] = g
    L[0, 1:] = L[1:, 0] = -g * b
    if b2 > 0:
        L[1:, 1:] += (g - 1) * np.outer(b, b) / b2
    return L


def reference_ray(P, n_static, rs, lam_max, r_stop):
    r0 = math.hypot(*P)
    ph0 = math.atan2(P[1], P[0])
    rhat = np.array(P) / r0
    phat = np.array([-rhat[1], rhat[0]])
    nr, nph = float(n_static @ rhat), float(n_static @ phat)
    f0 = 1 - rs / r0
    # tetrad: p^t = E_loc/sqrt(f) with E = f p^t = 1 -> E_loc = 1/sqrt(f); p^r = sqrt(f) * E_loc * n_r = n_r;
    # p^phi = E_loc n_phi / r
    L = r0 * r0 * (nph / math.sqrt(f0)) / r0  # r^2 dphi/dlam
    y0 = [r0, nr, ph0, 0.0]

    def rhs(lam, y):
        r = y[0]
        return [y[1], L * L / r**3 - 1.5 * rs * L * L / r**4, L / r**2, 1 / (1 - rs / r)]

    def stop(lam, y):
        return y[0] - r_stop

    stop.terminal = True
    return solve_ivp(rhs, (0, lam_max), y0, method="DOP853", rtol=1e-13, atol=1e-13 * r0, dense_output=True,
                     events=stop)


def compare_ray(T, X, Y, sol, c):
    """Max relative errors of r and ct at the stored vertices, matched by azimuth (unwrapped)."""
    ph = np.unwrap(np.arctan2(Y, X))
    lam = sol.t
    phs = sol.y[2]
    # monotone azimuth along the reference (L != 0)
    sgn = 1 if phs[-1] >= phs[0] else -1
    err_r = err_t = 0.0
    for k in range(1, len(T)):
        target = ph[k]
        # bisection on lambda
        lo, hi = lam[0], lam[-1]
        if not (min(phs[0], phs[-1]) <= target <= max(phs[0], phs[-1])):
            continue
        for _ in range(200):
            m = 0.5 * (lo + hi)
            if sgn * (sol.sol(m)[2] - target) < 0:
                lo = m
            else:
                hi = m
        y = sol.sol(0.5 * (lo + hi))
        r_v = math.hypot(X[k], Y[k])
        err_r = max(err_r, abs(r_v - y[0]) / y[0])
        err_t = max(err_t, abs(T[k] * c - (T[0] * c + y[3])) / max(y[3], 1e-300))
    return err_r, err_t


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    laws = Laws("SR", "GR")
    c = laws.c
    rs = laws.rs(10 * GM_SUN)
    print(f"rs = {rs:.6f} m")

    # --- 1. RK fan against the polar reference, default eta (what the run draws) ------------------------
    P = np.array([-60 * rs, 0.5 * rs])
    v_src = np.array([0.0, 0.0])
    n = light.unit_fan(72, angle0=0.5 * 2 * np.pi / 72)
    rays = light.trace_gr(laws, P[None, :].repeat(len(n), 0), 0.0, n, rs, rs, 81 * rs)
    worst_r = worst_t = 0.0
    n_cmp = 0
    for i in range(rays.n):
        T, X, Y = rays.ray(i)
        if rays.status[i] != 0 or len(T) < 3:
            continue
        nph = float(n[i] @ np.array([-P[1], P[0]]) / np.linalg.norm(P))
        if abs(nph) < 1e-3:
            continue
        sol = reference_ray(P, n[i], rs, 400 * rs, 81 * rs)
        er, et = compare_ray(T, X, Y, sol, c)
        worst_r, worst_t = max(worst_r, er), max(worst_t, et)
        n_cmp += 1
    print(f"1. RK fan (eta = 4e-3, default) vs DOP853 polar reference, {n_cmp} escaping rays: "
          f"max rel err r = {worst_r:.2e}, ct = {worst_t:.2e}")

    # --- 2. initial conditions of a MOVING emitter: engine vs explicit tetrad + textbook boost -----------
    Pm = np.array([12 * rs, 5 * rs])
    vel = np.array([-0.3 * c, 0.45 * c])  # coordinate velocity of the emitter
    r = np.hypot(*Pm)
    f = 1 - rs / r
    rhat = Pm / r
    phat = np.array([-rhat[1], rhat[0]])
    # local velocity measured by the static observer (independent): dr_proper/dtau_static, r dphi/dtau_static
    vr, vt = vel @ rhat, vel @ phat
    v_loc_ref = rhat * (vr / f) + phat * (vt / math.sqrt(f))
    v_loc_eng = light.local_velocity_static_frame(Pm, vel, rs, c)
    print(f"2a. local static-frame velocity: engine {v_loc_eng / c} c, reference {v_loc_ref / c} c, "
          f"diff {np.max(np.abs(v_loc_eng - v_loc_ref)) / c:.1e}")
    n_rest = light.unit_fan(16)
    n_eng = light.aberrate_sr(n_rest, v_loc_eng, c)
    # photon 4-momentum (1, n) in the emitter frame -> static frame: inverse boost = boost with -beta
    Lam_inv = boost_textbook(-v_loc_ref / c)
    k = (Lam_inv @ np.concatenate([np.ones((16, 1)), n_rest], 1).T).T
    n_ref = k[:, 1:] / k[:, :1]
    print(f"2b. aberrated directions in the static frame: max |engine - textbook| = {np.max(np.abs(n_eng - n_ref)):.1e}")
    # closed-form angle check (angle to v): cos th = (cos th' + b)/(1 + b cos th')
    b = np.linalg.norm(v_loc_ref) / c
    vhat = v_loc_ref / np.linalg.norm(v_loc_ref)
    cos_p = n_rest @ vhat
    cos_l = n_eng @ vhat
    print(f"2c. aberration closed form: max |cos_lab - (cos' + b)/(1 + b cos')| = "
          f"{np.max(np.abs(cos_l - (cos_p + b) / (1 + b * cos_p))):.1e}")
    # coordinate components of dx/dlambda from the engine vs from the tetrad
    V_eng = light.static_frame_directions_to_dlambda(Pm[None, :].repeat(16, 0), n_eng, rs)
    nr = n_ref @ rhat
    nph = n_ref @ phat
    V_ref = rhat[None, :] * nr[:, None] + phat[None, :] * (nph / math.sqrt(f))[:, None]
    # null condition with E = 1:  -1/f + (dr/dl)^2/f + r^2 (dphi/dl)^2 = 0  ->  check with V_eng
    drdl = V_eng @ rhat
    rdphidl = V_eng @ phat
    null = -1 / f + drdl**2 / f + rdphidl**2
    print(f"2d. dx/dlambda: max |engine - tetrad| = {np.max(np.abs(V_eng - V_ref)):.1e}; "
          f"null condition residual max = {np.max(np.abs(null)):.1e}")

    # --- 3. flat SR: Laws.emit_velocities keeps |u| = c and matches the textbook boost ------------------
    lawsf = Laws("SR", "none")
    vsrc = np.array([0.6 * c, -0.7 * c])
    u = lawsf.emit_velocities(n_rest, vsrc)
    k = (boost_textbook(-vsrc / c) @ np.concatenate([np.ones((16, 1)), n_rest], 1).T).T
    print(f"3. emit_velocities (SR, |v| = {np.linalg.norm(vsrc) / c:.3f} c): max ||u| - c|/c = "
          f"{np.max(np.abs(np.linalg.norm(u, axis=1) - c)) / c:.1e}, max |u/c - textbook| = "
          f"{np.max(np.abs(u / c - k[:, 1:] / k[:, :1])):.1e}")
    M = lawsf.frame_matrix(vsrc)
    print(f"   frame_matrix vs textbook boost: max diff {np.max(np.abs(M - boost_textbook(vsrc / c))):.1e}")

    # --- 4. drawing interpolation: browser-style linear interpolation in t between stored vertices --------
    P = np.array([-60 * rs, 0.0])
    dirs = np.array([[1.0, 0.0], [math.cos(0.12), math.sin(0.12)], [math.cos(0.2), math.sin(0.2)]])
    rays = light.trace_gr(laws, P[None, :].repeat(3, 0), 0.0, dirs, rs, rs, 81 * rs)
    for i in range(3):
        T, X, Y = rays.ray(i)
        # dense reference of the same ray from the engine itself with a 50x finer step and storage at every step
        fine = light.trace_gr(laws, P[None, :], 0.0, dirs[i][None, :], rs, rs, 81 * rs, eta=4e-5)
        Tf, Xf, Yf = fine.ray(0)
        err = 0.0
        for tq in np.linspace(T[0], min(T[-1], Tf[-1]), 4000):
            k = np.searchsorted(T, tq)
            k = min(max(k, 1), len(T) - 1)
            w = (tq - T[k - 1]) / (T[k] - T[k - 1])
            xi, yi = X[k - 1] + w * (X[k] - X[k - 1]), Y[k - 1] + w * (Y[k] - Y[k - 1])
            xr, yr = np.interp(tq, Tf, Xf), np.interp(tq, Tf, Yf)
            err = max(err, math.hypot(xi - xr, yi - yr))
        print(f"4. ray {i} (status {rays.status[i]}, {len(T)} vertices): max |front(t) linear - exact| = "
              f"{err / rs:.3e} rs")


if __name__ == "__main__":
    main()
