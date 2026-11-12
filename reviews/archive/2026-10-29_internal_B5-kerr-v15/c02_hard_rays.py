# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review B5 (Kerr half of P7 + v15), check c02: the closed-form screen tracer (kerr_null.trace_back) on hard rays.
#
# Independent reference (mpmath, 40 digits, no elliptic function, no Ferrari formula):
#   * the Mino time of the n-th equatorial crossing from the polar integral (cos theta = sqrt(u+) sin psi, smooth);
#   * the Mino time from infinity to the ENGINE's radius r_n on the branch the engine reports (before / after r4),
#     by tanh-sinh quadrature of 1/sqrt(R) with the substitutions r = r4 + s^2 (turning point) and u = 1/r (tail),
#     breakpoints clustered at the near-double root (rays grazing the critical curve).
#   The error of r_n is then dtau * |dr/dtau| = dtau * sqrt(R(r_n)) (first order), for the SAME binary64 (lambda, eta)
#   the engine used, so the input rounding of (alpha, beta) is not counted against the engine.
# Cases: chi = 0.5 / 0.94 / 0.998 / 0.9999; theta_o = 1e-4 deg, 17, 60, 89.9, 90 deg; rays at relative distance
#   d = 1e-1 .. 1e-12 outside and inside the critical curve along several screen directions; n up to 8;
#   large screens (alpha, beta ~ 100-1000 M).
# The claimed accuracy (tests/test_kerr_null.py docstring): 64u per input propagated with the closed form's own
#   sensitivities; tests compare at most n = 2 and |d| >~ 1e-2 (the SCREEN_POINTS).
#
# Root: engine mounted at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this script in
# /lf/reviews/archive/2026-10-29_internal_B5-kerr-v15/. CPU only.
# Run:
#   docker run --rm --user "$(id -u):$(id -g)" -e LFPHYS_NO_GPU=1 -v <engine>:/lf:ro -v <this folder>:<same path rw> \
#     -e PYTHONPATH=/lf/lfphys light-funnel-viz python3 /lf/reviews/archive/2026-10-29_internal_B5-kerr-v15/c02_hard_rays.py
import math
import sys
import time

import mpmath as mp
import numpy as np

from lfphys.core.gravity import kerr_null as KN

mp.mp.dps = 40
U = 2.0 ** -53


def ref_setup(lam, eta, chi):
    a = mp.mpf(chi)
    lam, eta = mp.mpf(lam), mp.mpf(eta)
    A = a * a - eta - lam * lam
    B = 2 * (eta + (lam - a) ** 2)
    C = -a * a * eta
    roots = mp.polyroots([1, 0, A, B, C], maxsteps=400, extraprec=400)
    rp = 1 + mp.sqrt(1 - a * a)
    real = sorted([mp.re(z) for z in roots if abs(mp.im(z)) < mp.mpf(10) ** -30])
    r4 = real[-1] if real and real[-1] > rp else None
    return dict(a=a, lam=lam, eta=eta, A=A, B=B, C=C, roots=roots, rp=rp, r4=r4)


def R(S, r):
    a = S["a"]
    return (r * r + a * a - a * S["lam"]) ** 2 - (r * r - 2 * r + a * a) * (S["eta"] + (S["lam"] - a) ** 2)


def near_root(S):
    """Real part of the root (pair) closest to the photon shell: where the integrand nearly blows up."""
    best = None
    for z in S["roots"]:
        if mp.re(z) > S["rp"] * mp.mpf("0.99"):
            if best is None or abs(mp.im(z)) < abs(mp.im(best)):
                best = z
    return best


def tail(S, r):
    """int_r^inf dr/sqrt(R) by u = 1/r: du / sqrt(1 + A u^2 + B u^3 + C u^4)."""
    A, B, C = S["A"], S["B"], S["C"]
    f = lambda u: 1 / mp.sqrt(1 + A * u * u + B * u ** 3 + C * u ** 4)  # noqa: E731
    return mp.quad(f, [0, 1 / r])


def I_from_r4(S, r):
    """int_{r4}^{r} dr/sqrt(R) with r = r4 + s^2; breakpoints at the near-double root."""
    r4 = S["r4"]
    others = [z for z in S["roots"] if abs(z - r4) > mp.mpf(10) ** -35]

    def rest(x):
        p = mp.mpf(1)
        for z in others:
            p *= (x - z)
        return mp.re(p)
    f = lambda s: 2 / mp.sqrt(rest(r4 + s * s))  # noqa: E731
    smax = mp.sqrt(r - r4)
    gap = min([abs(r4 - z) for z in others])
    pts = [mp.mpf(0)]
    g = mp.sqrt(gap)
    for k in (-3, -2, -1, 0, 1, 2, 3, 4, 5, 6):
        x = g * mp.mpf(10) ** k
        if x < smax:
            pts.append(x)
    pts.append(smax)
    return mp.quad(f, pts)


def I_inf_to(S, r):
    """int_r^inf for a captured ray (no turning point outside the horizon); breakpoints near the shell root."""
    z = near_root(S)
    A, B, C = S["A"], S["B"], S["C"]
    f = lambda u: 1 / mp.sqrt(1 + A * u * u + B * u ** 3 + C * u ** 4)  # noqa: E731
    pts = [mp.mpf(0)]
    if z is not None:
        u0 = 1 / mp.re(z)
        w = abs(mp.im(z)) / mp.re(z) ** 2 + mp.mpf(10) ** -38
        for k in (6, 5, 4, 3, 2, 1, 0, -1, -2):
            for sgn in (-1, 1):
                x = u0 + sgn * w * mp.mpf(10) ** k
                if 0 < x < 1 / r:
                    pts.append(x)
        if 0 < u0 < 1 / r:
            pts.append(u0)
    pts.append(1 / r)
    pts = sorted(set(pts))
    return mp.quad(f, pts)


def tau_to_r(S, r, after_turn):
    """Mino time from the observer (infinity) to radius r, before or after the radial turning point r4."""
    if S["r4"] is None:
        return I_inf_to(S, r)
    big = max(S["r4"] * 4, mp.mpf(40))
    T4 = I_from_r4(S, big) + tail(S, big)  # infinity -> r4
    if r <= big:
        I4r = I_from_r4(S, r)
    else:
        I4r = T4 - tail(S, r)
    return T4 + I4r if after_turn else T4 - I4r


def tau_polar(S, theta_o, beta, n):
    a, lam, eta = S["a"], S["lam"], S["eta"]
    h = (eta + lam * lam - a * a) / 2
    Am = h + mp.sqrt(h * h + a * a * eta)
    up = eta / Am
    f = lambda p: 1 / mp.sqrt(Am + a * a * up * mp.sin(p) ** 2)  # noqa: E731
    co = mp.cos(mp.mpf(theta_o))
    x = co / mp.sqrt(up)
    if x > 1:
        x = mp.mpf(1)
    psio = mp.asin(x)
    half = mp.quad(f, [-mp.pi / 2, 0, mp.pi / 2])
    if theta_o == math.pi / 2:  # edge-on: the observer's own crossing does not count
        return (n + 1) * half
    first = mp.quad(f, [0, psio]) if beta <= 0 else mp.quad(f, [psio, mp.pi / 2]) + mp.quad(f, [0, mp.pi / 2])
    return first + n * half


def check(chi, th_deg, al, be, n_max, label, out):
    th = math.radians(th_deg) if th_deg != 90.0 else math.pi / 2
    res = KN.trace_back(np.array([al]), np.array([be]), th, chi, n_max=n_max)
    lam, eta = float(res["lam"][0]), float(res["eta"][0])
    S = ref_setup(lam, eta, chi)
    cap_ref = S["r4"] is None
    cap = bool(res["captured"][0])
    worst_rel = 0.0
    rows = []
    for n in range(n_max + 1):
        tn = float(res["tau_n"][n][0])
        rn = float(res["r_n"][n][0])
        tp = tau_polar(S, th, be, n)
        if math.isnan(tn):
            # the engine says there is no n-th crossing: check against the reference total Mino time
            if cap_ref:
                tot = I_inf_to(S, S["rp"])
            else:
                big = max(S["r4"] * 4, mp.mpf(40))
                tot = 2 * (I_from_r4(S, big) + tail(S, big))
            ok = tp >= tot
            rows.append(f"    n={n}: engine none; ref tau_n={float(tp):.6g} vs total {float(tot):.6g} -> {'ok' if ok else 'MISSING CROSSING'}")
            if not ok:
                worst_rel = max(worst_rel, 1.0)
            continue
        after = (float(res["kr_sign_n"][n][0]) < 0)
        tr = tau_to_r(S, mp.mpf(rn), after)
        dtau = float(tr - tp)
        dr = abs(dtau) * math.sqrt(max(float(R(S, mp.mpf(rn))), 0.0))
        dt_rel = abs(float(tn - tp)) / float(tp)
        worst_rel = max(worst_rel, dr / rn)
        rows.append(f"    n={n}: r_n={rn:.15g}  tau_n err {dt_rel:.2e} rel;  r_n err {dr:.3e} M ({dr / rn:.2e} rel)"
                    f"  [{'after' if after else 'before'} turn]")
    out.append(f"{label}: chi={chi} th={th_deg} alpha={al!r} beta={be!r} lam={lam:.17g} eta={eta:.17g} "
               f"captured={cap} (ref {cap_ref}) n_cross={int(res['n_cross'][0])}")
    out.extend(rows)
    if cap != cap_ref:
        out.append("    FATE DIFFERS")
        worst_rel = max(worst_rel, 1.0)
    return worst_rel


def main():
    out = []
    t0 = time.time()
    summary = []
    # (1) rays grazing the critical curve, along several directions, both sides
    for chi, th_deg in ((0.94, 17.0), (0.998, 60.0), (0.998, 90.0), (0.9999, 89.9), (0.5, 1e-4)):
        th = math.radians(th_deg) if th_deg != 90.0 else math.pi / 2
        cc = KN.critical_curve(chi, th, 801)
        cx = 0.5 * (cc["alpha"].max() + cc["alpha"].min())
        for ang in (0.2, 1.7, 3.1, 4.4):
            rc, rb = KN.critical_radius_at(chi, th, ang, (cx, 0.0))
            for d in (1e-1, 1e-3, 1e-6, 1e-9, 1e-12, -1e-3, -1e-9, -1e-12):
                rho = rc * (1 + d)
                al, be = cx + rho * math.cos(ang), rho * math.sin(ang)
                w = check(chi, th_deg, al, be, 8, f"[graze d={d:+.0e} ang={ang}]", out)
                summary.append((w, chi, th_deg, ang, d))
    # (2) large screens and on-axis / near-axis observers
    for chi, th_deg, al, be in ((0.9, 60.0, 300.0, -200.0), (0.9, 60.0, -800.0, 500.0), (0.998, 89.9, 1000.0, 3.0),
                                (0.5, 1e-4, 40.0, -30.0), (0.998, 17.0, -150.0, 60.0), (0.9, 0.0, 5.3, 2.4)):
        w = check(chi, th_deg, al, be, 3, "[large/axis]", out)
        summary.append((w, chi, th_deg, al, be))
    out.append("")
    out.append("== summary: worst relative r_n error per ray (sorted, top 15) ==")
    for s in sorted(summary, key=lambda s: -s[0])[:15]:
        out.append("  " + repr(s))
    out.append(f"rays: {len(summary)}; wall {time.time() - t0:.0f} s")
    print("\n".join(out))


if __name__ == "__main__":
    main()
