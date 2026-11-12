# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review B5, check c07: kerr_orbits on harder orbits than the tests' (near the separatrix at chi = 0.998, nearly
# polar and polar, circular inclined, tiny spin, p up to 1e5, e = 0.95, retrograde at high spin).
#
# References:
#   * E, L, Q: the defining equations R(p/(1+e)) = R(p/(1-e)) = 0 (R = R' = 0 at e = 0), Theta(theta_min) = 0 solved
#     by mpmath findroot at 40 digits (seeded with the engine's values);
#   * frequencies: 40-digit tanh-sinh quadratures over the Mino phases, r = p/(1 + e cos chi) and
#     cos theta = sqrt(z_-) cos psi with z_+- from the reviewer's own quadratic (no elliptic function, no root of the
#     engine): Upsilon_r = pi / int_0^pi (dlambda/dchi) dchi, Upsilon_theta likewise, Gamma and Upsilon_phi as the
#     Mino-time averages of dt/dlambda and dphi/dlambda (Fujita & Hikida 2009 Eqs. 1-2);
#   * KerrGeoPy 0.9.3 (comparison image) where it accepts the orbit.
# Reported: relative errors of the engine's closed-form and averaged frequencies, KerrGeoPy's, and the constants.
#
# Root: engine at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this script in
# /lf/reviews/archive/2026-10-29_internal_B5-kerr-v15/. Run in the comparison image:
#   docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v <engine>:/lf:ro -v <this folder>:<same path rw> \
#     -e PYTHONPATH=/lf/lfphys -e LFPHYS_EXTERNAL=1 light-funnel-ext python3 c07_kerr_orbits_hard.py
import math
import time

import mpmath as mp

from lfphys.core.gravity import kerr_orbits as KO

mp.mp.dps = 40

try:
    from kerrgeopy import constants as kc, frequencies as kf
    kg = True
except Exception:  # noqa: BLE001
    kg = None


def exact_constants(chi, p, e, x, guess):
    a, p_, e_, x_ = mp.mpf(chi), mp.mpf(p), mp.mpf(e), mp.mpf(x)
    z = 1 - x_ ** 2

    def R(r, E, L, Q):
        dl = r * r - 2 * r + a * a
        return (E * (r * r + a * a) - a * L) ** 2 - dl * (r * r + (L - a * E) ** 2 + Q)

    def eqs(E, L, Q):
        if e_ > 0:
            out = [R(p_ / (1 + e_), E, L, Q), R(p_ / (1 - e_), E, L, Q)]
        else:
            out = [R(p_, E, L, Q), mp.diff(lambda r: R(r, E, L, Q), p_)]
        out.append(Q - z * (a * a * (1 - E * E) + L * L / (1 - z)) if x_ != 0 else L)
        return out
    sol = mp.findroot(eqs, [mp.mpf(g) for g in guess], tol=mp.mpf(10) ** -36, maxsteps=200)
    return sol[0], sol[1], sol[2]


def ref_freqs(chi, p, e, E, L, Q):
    a = mp.mpf(chi)
    p, e = mp.mpf(p), mp.mpf(e)

    def R(r):
        dl = r * r - 2 * r + a * a
        return (E * (r * r + a * a) - a * L) ** 2 - dl * (r * r + (L - a * E) ** 2 + Q)

    def Tr(r):
        dl = r * r - 2 * r + a * a
        return (r * r + a * a) * (E * (r * r + a * a) - a * L) / dl

    def Pr(r):
        dl = r * r - 2 * r + a * a
        return a * (E * (r * r + a * a) - a * L) / dl
    if e > 0:
        r1, r2 = p / (1 - e), p / (1 + e)

        # R = (r1 - r)(r - r2) q(r): q by exact polynomial division (no 0/0 at the turning points)
        K = (L - a * E) ** 2 + Q
        c4, c3, c2 = E * E - 1, mp.mpf(2), 2 * E * (E * a * a - a * L) - a * a - K
        s_, P_ = r1 + r2, r1 * r2
        q2 = c4
        q1 = c3 + s_ * q2
        q0 = c2 + s_ * q1 - P_ * q2

        def dlam(c):  # dlambda/dchi = (dr/dchi)/sqrt(R) = sqrt(1 - e^2)/((1 + e cos chi) sqrt(q(r)))
            r = p / (1 + e * mp.cos(c))
            q = -(q2 * r * r + q1 * r + q0)
            return mp.sqrt(1 - e * e) / ((1 + e * mp.cos(c)) * mp.sqrt(q))
        Ir = mp.quad(dlam, [0, mp.pi / 2, mp.pi])
        ups_r = mp.pi / Ir
        avg_Tr = mp.quad(lambda c: Tr(p / (1 + e * mp.cos(c))) * dlam(c), [0, mp.pi / 2, mp.pi]) / Ir
        avg_Pr = mp.quad(lambda c: Pr(p / (1 + e * mp.cos(c))) * dlam(c), [0, mp.pi / 2, mp.pi]) / Ir
    else:
        # circular: the radial frequency from R'' (small oscillations: Upsilon_r = sqrt(-R''(p)/2))
        ups_r = mp.sqrt(-mp.diff(R, p, 2) / 2)
        avg_Tr, avg_Pr = Tr(p), Pr(p)
    beta = a * a * (1 - E * E)
    # beta z^2 - (Q + L^2 + beta) z + Q = 0
    bb = Q + L * L + beta
    if beta > 0:
        zp = (bb + mp.sqrt(bb * bb - 4 * beta * Q)) / (2 * beta)
        zm = Q / (beta * zp)
    else:
        zm = Q / (Q + L * L)
        zp = mp.inf
    if Q == 0:
        ups_th = mp.sqrt(beta * zp) if beta > 0 else mp.sqrt(Q + L * L)  # small oscillations about the equator
        avg_cos2 = mp.mpf(0)
        avg_Lsin = L
    else:
        def dlth(s):  # cos theta = sqrt(z_-) cos psi; dlambda/dpsi = 1/sqrt(beta (z_+ - z_- cos^2 psi))
            if beta > 0:
                return 1 / mp.sqrt(beta * (zp - zm * mp.cos(s) ** 2))
            return 1 / mp.sqrt(Q + L * L)
        Ith = mp.quad(dlth, [0, mp.pi / 2, mp.pi])
        ups_th = mp.pi / Ith
        avg_cos2 = mp.quad(lambda s: zm * mp.cos(s) ** 2 * dlth(s), [0, mp.pi / 2, mp.pi]) / Ith
        avg_Lsin = (mp.quad(lambda s: L / (1 - zm * mp.cos(s) ** 2) * dlth(s), [0, mp.pi / 2, mp.pi]) / Ith
                    if L != 0 else mp.mpf(0))
    gam = avg_Tr - a * a * E * (1 - avg_cos2) + a * L
    ups_phi = avg_Pr + avg_Lsin - a * E
    return {"Upsilon_r": ups_r, "Upsilon_theta": ups_th, "Upsilon_phi": ups_phi, "Gamma": gam}


def main():
    out = []
    cases = []
    if kg is not None:
        for chi, e, x, f in ((0.998, 0.5, 0.5, None), (0.998, 0.9, -0.8, 1.2), (0.99, 0.1, 0.9, 1.001),
                             (0.9, 0.7, 0.3, 1.0005)):
            ps = float(kc.separatrix(chi, e, x))
            p = ps + 0.02 if f is None else ps * f
            cases.append((chi, p, e, x, f"near separatrix p_sep = {ps:.6f}"))
    cases += [(0.9, 8.0, 0.3, 0.01, "nearly polar"), (0.9, 8.0, 0.3, 0.0, "polar"), (0.9, 8.0, 0.0, 0.0, "polar circular"),
              (0.5, 7.0, 0.0, 0.3, "circular inclined"), (1e-4, 10.0, 0.5, 0.5, "tiny spin"),
              (0.7, 1e3, 0.2, 0.6, "p = 1e3"), (0.7, 1e5, 0.2, 0.6, "p = 1e5"), (0.6, 12.0, 0.95, 0.4, "e = 0.95"),
              (0.9, 10.0, 0.4, 1.0, "equatorial pro"), (0.9, 12.0, 0.4, -1.0, "equatorial retro")]
    for chi, p, e, x, label in cases:
        t0 = time.time()
        try:
            orb = KO.KerrOrbit(chi, p, e, x)
        except Exception as ex:  # noqa: BLE001
            out.append(f"{label}: chi={chi} p={p:.10g} e={e} x={x}: engine refused: {ex}")
            continue
        E, L, Q = orb.E, orb.L, orb.Q
        Ex, Lx, Qx = exact_constants(chi, p, e, x, (E, L, Q))
        ce = (abs(E - Ex) / Ex, abs(L - Lx) / max(abs(Lx), mp.mpf(10) ** -30), abs(Q - Qx) / max(abs(Qx), mp.mpf(10) ** -30))
        ref = ref_freqs(chi, p, e, Ex, Lx, Qx)
        f_cl = orb.frequencies("closed")
        f_av = orb.frequencies("average")
        line = [f"{label}: chi={chi} p={p:.10g} e={e} x={x}; constants rel err E {float(ce[0]):.1e} L {float(ce[1]):.1e} "
                f"Q {float(ce[2]):.1e}"]
        for k in ("Upsilon_r", "Upsilon_theta", "Upsilon_phi", "Gamma"):
            rv = ref[k]
            ec = abs(f_cl[k] - rv) / abs(rv) if rv != 0 else abs(f_cl[k])
            ea = abs(f_av[k] - rv) / abs(rv) if rv != 0 else abs(f_av[k])
            line.append(f"    {k}: ref {mp.nstr(rv, 17)}  closed {float(ec):.1e}  average {float(ea):.1e}")
        if kg is not None and x != 0.0:
            try:
                kfr = kf.mino_frequencies(chi, p, e, x)
                names = ("Upsilon_r", "Upsilon_theta", "Upsilon_phi", "Gamma")
                errs = [abs(float(v) - ref[n]) / abs(ref[n]) for v, n in zip(kfr, names)]
                line.append("    KerrGeoPy mino_frequencies rel err: " + ", ".join(f"{n} {float(v):.1e}" for n, v in zip(names, errs)))
            except Exception as ex:  # noqa: BLE001
                line.append(f"    KerrGeoPy: {type(ex).__name__}: {ex}")
        line.append(f"    ({time.time() - t0:.1f} s)")
        out.extend(line)
        print("\n".join(line), flush=True)


if __name__ == "__main__":
    main()
