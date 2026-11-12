# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""``lfphys.core.optics.interfaces`` and ``core.optics.thin_films`` against tmm 0.2.0 (plan item P13).

Compared: Fresnel coefficients of one interface (``interfaces.fresnel``), multilayers (``interfaces.stack``: r, t, R,
T, s and p), and the thin-film closed forms (``thin_films.single_film``, ``airy``, ``quarter_wave_R``,
``quarter_wave_stack_R``, ``ftir_T``, ``evanescent_length``, ``joule_absorption_s``, and ``interfaces.field_profile``)
against tmm's ``coh_tmm``, ``absorp_in_each_layer`` and ``position_resolved``. Cases include normal, Brewster,
grazing (89.9-89.999 deg) incidence, the critical angle, total internal reflection, metals (n = 0.2 + 3.3i), surface
plasmon resonance (Kretschmann), frustrated TIR across gaps up to 20 um (T down to 1e-143), a 20-layer Bragg mirror
and an absorbing 4-layer stack. Conventions agree (tmm: Byrnes, arXiv:1603.02720; time factor e^{-i omega t}, Im n > 0
absorbing, the same p sign); the engine's method is the characteristic (Abeles) matrices, tmm's the interface-by-
interface transfer matrices: two algorithms.

Exact reference: the characteristic-matrix solution in 40-digit mpmath for the same binary64 inputs (r, t, R, T,
per-layer absorption from the Poynting flux at the layer boundaries, |E|^2 at given depths): eng_err, lib_err.

Tolerance "TMM rounding" (derived; per row the sum over the two sides, plus 4u|F| for the final operations):
* backward error: both sides compute the Snell cosines, the admittances eta_j (n cos, or n/cos for p) and the phases
  delta_j = 2 pi n_j cos_j d_j/lambda with at most 16 roundings (n0 sin th0: 2; (s0/n)^2: 7 for a complex division and
  square; 1 - q and sqrt: 3; the products: 4), i.e. exactly for inputs and per-layer eta_j, delta_j perturbed by at
  most 16u relative; tmm moreover takes the incidence angle as arcsin(n0 sin th0 / n0), which perturbs th0 by
  u |tan th0|. Bound: 16u S_F per side, S_F = sum over n_j (real and imaginary part), d_j, lambda, eta_j, delta_j
  (complex, both directions) of |dF/d ln x| + |dF/d th0| (|th0| + |tan th0|), the derivatives taken in mpmath.
  tmm's cosines are cos(arcsin(x_j)) of a complex angle: besides the above, each carries an absolute error up to
  u |sin_j| (1 + |theta_j|) (beyond total reflection Re cos = cos(fl(pi/2)) cosh(y) = 6e-17 cosh(y) where the exact
  value is 0); this adds 16u sum_j |dF/d cos_j| |sin_j| (1 + |theta_j|) on tmm's side.
* chain of 2x2 products: the engine forms [B, C] = M_1 ... M_N [1, eta_out] with the entries of each M_j within 8u
  and each product adding 6u (14u per layer, 12u for the last step); tmm forms (1/t_01)[[1, r],[r, 1]]
  prod_j diag(e^{-i delta_j}, e^{i delta_j}) (1/t)[[1, r],[r, 1]] with 20u per layer. The rounding of a product
  of matrices is bounded by the product of their entrywise moduli |M_1|...|M_N| (Higham, section 3.5), so the
  relative error of the denominator is c u kappa with kappa = (|eta0| B_abs + C_abs)/|eta0 B + C| (engine) or
  |M|_abs,00/|M_00| (tmm), and r, t, T, A_j, |E|^2 inherit it (twice for squared moduli); tmm's absorption is a
  difference of two fluxes, so it carries kappa (|P_in| + |P_out|) rather than kappa A_j.
* the engine's own stated bounds replace the chain where it provides them: ``single_film`` err_r, err_t and ``airy``
  err_T (first-order rounding of the closed forms, thin_films.py); ``quarter_wave_*`` and ``ftir_T`` are bounded by
  running them with ``_common.Fe``; ``evanescent_length`` is within one rounding (thin_films.py); the Gauss-Legendre
  rule of ``joule_absorption_s`` has a stated remainder of 2.5e-26 of max|f| w per sub-interval (negligible) and its
  sum adds log2(nodes) u.
Known disagreement (strict xfail): tmm resets the attenuation of an "almost perfectly opaque" layer, Im(delta) > 35,
to 35 ("allowing 1 photon in 10^30 to pass through", tmm_core.coh_tmm); the transmitted t and T of such a stack are
then tmm's modification, not the solution of Maxwell's equations.
"""

from __future__ import annotations

import contextlib
import functools
import math
import warnings

import mpmath as mp
import numpy as np
import pytest
import tmm

from lfphys.core.optics import interfaces, thin_films as tf

from _common import FMATH, U, Fe, Row, check, params

GROUP = "optics (tmm)"
INF = float("inf")
DPS = 40  # digits of the exact reference (set per function, not globally)
HSTEP = mp.mpf(10) ** -20
K_BACK = 16  # backward-error roundings per input (module docstring)
TMM_OPAQUE = 35.0  # tmm_core.coh_tmm: Im(delta) > 35 is reset to 35


def _m(z):
    z = complex(z)
    return mp.mpc(z.real, z.imag)


# --- exact reference: characteristic matrices in mpmath -------------------------------------------------------------

def mp_solve(ns, ds, lam, th0, pol, eta_f=None, delta_f=None, zs=(), c_add=None):
    """r, t, R, T (and for s: per-layer absorption A, |E|^2 at (layer, depth) points zs) of the stack, in mpmath.
    eta_f, delta_f: optional complex factors on each medium's admittance and each layer's phase (for the backward-error
    sensitivities). Also the engine-side chain condition kappa_E."""
    ns = [n if isinstance(n, mp.mpc) else _m(n) for n in ns]
    N = len(ds)
    s0 = ns[0] * mp.sin(th0)
    cs = []
    for n in ns:
        c = mp.sqrt(1 - (s0 / n) ** 2)
        nc = n * c
        if nc.imag < 0 or (nc.imag == 0 and nc.real < 0):
            c = -c
        cs.append(c)
    if c_add:
        cs = [c + a for c, a in zip(cs, c_add)]
    etas = [n * c if pol == "s" else n / c for n, c in zip(ns, cs)]
    if eta_f:
        etas = [e * f for e, f in zip(etas, eta_f)]
    deltas = [None] + [2 * mp.pi * ns[j] * cs[j] * ds[j - 1] / lam for j in range(1, N + 1)]
    if delta_f:
        deltas = [None] + [deltas[j] * delta_f[j] for j in range(1, N + 1)]

    def M(j, frac=None):
        d = deltas[j] if frac is None else deltas[j] * frac
        cd, sd = mp.cos(d), mp.sin(d)
        return [[cd, -1j * sd / etas[j]], [-1j * etas[j] * sd, cd]]

    def mv(A, v):
        return [A[0][0] * v[0] + A[0][1] * v[1], A[1][0] * v[0] + A[1][1] * v[1]]

    vec, vabs = [mp.mpc(1), etas[-1]], [mp.mpf(1), abs(etas[-1])]
    ends = [None] * (N + 2)
    for j in range(N, 0, -1):
        ends[j] = vec
        Mj = M(j)
        vec = mv(Mj, vec)
        vabs = mv([[abs(x) for x in row] for row in Mj], vabs)
    B, C = vec
    e0 = etas[0]
    den = e0 * B + C
    r = (e0 * B - C) / den
    t = 2 * e0 / den
    if pol == "p":
        r, t = -r, t * cs[0] / cs[-1]
    T = 4 * e0.real * etas[-1].real / abs(den) ** 2
    out = {"r": r, "t": t, "R": abs(r) ** 2, "T": T, "kappa_E": (abs(e0) * vabs[0] + vabs[1]) / abs(den)}
    if pol == "s":
        tau = 2 * e0 / den
        flux = lambda v: (tau * v[0] * mp.conj(tau * v[1])).real / e0.real  # noqa: E731
        P = [flux(vec)] + [flux(ends[j]) for j in range(1, N + 1)]  # at the entrance of layers 1..N, and the exit
        P.append(T)
        out["A"] = [P[j - 1] - P[j] for j in range(1, N + 1)]
        out["P"] = P
        E2 = []
        for (layer, zeta) in zs:
            if layer == 0:
                k0 = 2 * mp.pi * ns[0] * cs[0] / lam
                E2.append(abs(mp.exp(1j * k0 * zeta) + r * mp.exp(-1j * k0 * zeta)) ** 2)
            else:
                Mr = M(layer, (ds[layer - 1] - zeta) / ds[layer - 1])
                E2.append(abs(tau * mv(Mr, ends[layer])[0]) ** 2)
        out["E2"] = E2
    return out


def _inputs(ns, ds, lam, th0):
    return [_m(n) for n in ns], [mp.mpf(d) for d in ds], mp.mpf(lam), mp.mpf(th0)


def sensitivities(ns, ds, lam, th0, pol, zs=()):
    """(base, S, Sc): base = mp_solve at the inputs, S[key] = sum over the backward-error directions of |dF/d ln x|
    (module docstring), for keys r, t, R, T and (s) the lists A, E2, P; Sc[key] the same for tmm's absolute error in
    each cosine, cos(arcsin(x)) with |delta cos_j| <= |sin_j| (1 + |theta_j|) per unit round-off (tmm only)."""
    n_, d_, l_, t_ = _inputs(ns, ds, lam, th0)
    base = mp_solve(n_, d_, l_, t_, pol, zs=zs)
    keys = [k for k in ("r", "t", "R", "T") if k in base]
    lists = [k for k in ("A", "E2", "P") if k in base]
    S = {k: mp.mpf(0) for k in keys}
    S.update({k: [mp.mpf(0)] * len(base[k]) for k in lists})
    N = len(ds)

    def acc(res):
        for k in keys:
            S[k] += abs(res[k] - base[k]) / HSTEP
        for k in lists:
            S[k] = [s + abs(a - b) / HSTEP for s, a, b in zip(S[k], res[k], base[k])]

    for j, n in enumerate(n_):
        for part in ((1, abs(n.real)), (1j, abs(n.imag))):
            if part[1] == 0:
                continue
            nn = list(n_)
            nn[j] = n + part[0] * HSTEP * part[1]
            acc(mp_solve(nn, d_, l_, t_, pol, zs=zs))
    for j in range(N):
        dd = list(d_)
        dd[j] = d_[j] * (1 + HSTEP)
        acc(mp_solve(n_, dd, l_, t_, pol, zs=zs))
    acc(mp_solve(n_, d_, l_ * (1 + HSTEP), t_, pol, zs=zs))
    w = abs(t_) + abs(mp.tan(t_))
    if w:
        acc(mp_solve(n_, d_, l_, t_ + HSTEP * w, pol, zs=zs))
    for k in range(N + 2):
        for f in (1 + HSTEP, 1 + 1j * HSTEP):
            ef = [mp.mpc(1)] * (N + 2)
            ef[k] = f
            acc(mp_solve(n_, d_, l_, t_, pol, eta_f=ef, zs=zs))
    for k in range(1, N + 1):
        for f in (1 + HSTEP, 1 + 1j * HSTEP):
            df = [mp.mpc(1)] * (N + 1)
            df[k] = f
            acc(mp_solve(n_, d_, l_, t_, pol, delta_f=df, zs=zs))
    S_common = S
    S = {k: mp.mpf(0) for k in keys}
    S.update({k: [mp.mpf(0)] * len(base[k]) for k in lists})
    s0 = n_[0] * mp.sin(t_)
    for k in range(N + 2):
        sk = s0 / n_[k]
        w = abs(sk) * (1 + abs(mp.asin(sk)))
        for f in (HSTEP * w, 1j * HSTEP * w):
            ca = [mp.mpc(0)] * (N + 2)
            ca[k] = f
            acc(mp_solve(n_, d_, l_, t_, pol, zs=zs, c_add=ca))
    return base, S_common, S


def tmm_kappa(out):
    """tmm's chain condition: (A_00 |t|, (A_10 + |r| A_00) |t|) with A = the product of the entrywise moduli of tmm's
    factors (from its own angles, phases and interface coefficients), and whether it capped an opaque layer."""
    n, th, kz, d, pol = out["n_list"], out["th_list"], out["kz_list"], out["d_list"], out["pol"]
    num = len(n)
    rr = lambda i: abs(tmm.interface_r(pol, n[i], n[i + 1], th[i], th[i + 1]))  # noqa: E731
    it = lambda i: 1 / abs(tmm.interface_t(pol, n[i], n[i + 1], th[i], th[i + 1]))  # noqa: E731
    A = it(0) * np.array([[1.0, rr(0)], [rr(0), 1.0]])
    capped = False
    for i in range(1, num - 1):
        im = (kz[i] * d[i]).imag
        if im > TMM_OPAQUE:
            im, capped = TMM_OPAQUE, True
        P = np.array([[math.exp(im), 0.0], [0.0, math.exp(-im)]])
        A = A @ (it(i) * (P @ np.array([[1.0, rr(i)], [rr(i), 1.0]])))
    at, ar = abs(out["t"]), abs(out["r"])
    return A[0, 0] * at, (A[1, 0] + ar * A[0, 0]) * at, capped


def run_tmm(ns, ds, lam, th0, pol):
    with warnings.catch_warnings(), contextlib.redirect_stdout(None):
        warnings.simplefilter("ignore")
        return tmm.coh_tmm(pol, [complex(n) for n in ns], [INF] + list(ds) + [INF], th0, lam)


def _f(x):
    return float(x) if not isinstance(x, mp.mpc) else complex(x)


# --- rows -----------------------------------------------------------------------------------------------------------

def _stack_rows(label, ns, ds, lam, th0, pol, eng=None, quantity="stack", closed_form=False):
    """Rows r, t, R, T of interfaces.stack (or fresnel for one interface) against tmm. closed_form: the engine side is
    a closed form whose rounding the caller bounds (Fe) from the binary64 inputs, so only tmm's terms enter here."""
    N = len(ds)
    base, S, Sc = sensitivities(ns, ds, lam, th0, pol)
    out = run_tmm(ns, ds, lam, th0, pol)
    k_t, k_r, capped = tmm_kappa(out)
    kE = float(base["kappa_E"])
    cE, cT = (14 * N + 12) * U, (20 * N + 12) * U
    if eng is None:
        eng = interfaces.stack(ns, ds, lam, th0, pol)
    rows = []
    for key in ("r", "t", "R", "T"):
        F = base[key]
        aF = float(abs(F))
        chain_e = {"r": cE * (1 + aF) * kE, "t": cE * aF * kE, "R": 2 * cE * math.sqrt(aF) * (1 + math.sqrt(aF)) * kE,
                   "T": 2 * cE * aF * kE}[key]
        ar = float(abs(base["r"]))
        chain_t = {"r": cT * k_r, "t": cT * aF * k_t, "R": 2 * ar * cT * k_r, "T": 2 * cT * aF * k_t}[key]
        if closed_form:
            tol = K_BACK * U * float(S[key] + Sc[key]) + chain_t + 4 * U * aF
        else:
            tol = K_BACK * U * float(2 * S[key] + Sc[key]) + chain_e + chain_t + 4 * U * aF
        row = Row(GROUP, f"{quantity} {key} ({pol})", f"{label}, th0={math.degrees(th0):.6g} deg", eng[key], out[key],
                  tol, "TMM rounding", float(abs(eng[key] - F)), float(abs(out[key] - F)))
        if capped and key in ("t", "T"):
            row.xfail = (f"tmm resets an opaque layer's Im(delta) > 35 to 35: measured {key} engine {eng[key]:.4g}, "
                         f"tmm {abs(out[key]):.4g}, exact {float(abs(F)):.4g} (|engine - exact| = {row.eng_err:.2g}, "
                         f"|tmm - exact| = {row.lib_err:.2g}, tolerance {tol:.2g})")
        rows.append(row)
    return rows


FRESNEL = {
    "air/glass": (1.0, 1.5, (0.0, 30.0, math.degrees(math.atan(1.5)), 70.0, 89.0, 89.9, 89.999)),
    "glass/air": (1.5, 1.0, (0.0, 30.0, math.degrees(math.asin(1 / 1.5)) - 1e-6, math.degrees(math.asin(1 / 1.5))
                             + 1e-6, 45.0, 60.0, 89.9)),
    "air/metal": (1.0, 0.2 + 3.3j, (0.0, 45.0, 80.0, 89.99)),
}
BRAGG = ([1.0] + [2.3, 1.38] * 10 + [1.52], [633 / 4 / 2.3, 633 / 4 / 1.38] * 10)
STACKS = [
    ("AR MgF2 on glass", [1.0, 1.38, 1.5], [633 / 4 / 1.38], 633.0, (0.0, 45.0)),
    ("Bragg (2.3/1.38)^10 on 1.52", BRAGG[0], BRAGG[1], 633.0, (0.0, 20.0, 60.0, 89.9)),
    ("Kretschmann 50 nm metal", [1.5, 0.2 + 3.3j, 1.0], [50.0], 633.0, (40.0, 43.0, 44.0, 45.0, 50.0, 70.0)),
    ("FTIR gap 100 nm", [1.5, 1.0, 1.5], [100.0], 633.0, (60.0,)),
    ("FTIR gap 1 um", [1.5, 1.0, 1.5], [1000.0], 633.0, (60.0,)),
    ("FTIR gap 5 um", [1.5, 1.0, 1.5], [5000.0], 633.0, (60.0,)),
    ("FTIR gap 20 um", [1.5, 1.0, 1.5], [20000.0], 633.0, (60.0,)),
    ("absorbing 4 layers", [1.0, 1.45 + 0.01j, 2.0 + 0.5j, 1.38, 3.5 + 0.02j, 1.5], [120.0, 35.0, 200.0, 80.0], 800.0,
     (0.0, 40.0, 85.0, 89.99)),
    ("opaque metal 2 um", [1.0, 0.2 + 3.3j, 1.5], [2000.0], 633.0, (17.18873385,)),
]


def _fresnel_rows():
    out = []
    for label, (n1, n2, angles) in FRESNEL.items():
        for deg in angles:
            th = math.radians(deg)
            for pol in ("s", "p"):
                r, t, R, T = interfaces.fresnel(n1, n2, th, pol)
                out += _stack_rows(label, [n1, n2], [], 633.0, th, pol, {"r": r, "t": t, "R": R, "T": T}, "fresnel")
    return out


def _multilayer_rows():
    out = []
    for label, ns, ds, lam, angles in STACKS:
        for deg in angles:
            for pol in ("s", "p"):
                out += _stack_rows(label, ns, ds, lam, math.radians(deg), pol)
    return out


@contextlib.contextmanager
def thin_films_bounded():
    saved = tf.math
    tf.math = FMATH
    try:
        yield
    finally:
        tf.math = saved


def _closed_form_rows():
    out = []
    # one film: the Airy sum with complex Fresnel coefficients (engine's stated err_r, err_t)
    films = [("AR film", 1.0, 1.38, 1.5, 99.6, (0.0, 60.0)), ("free-standing n=2.3", 1.0, 2.3, 1.0, 2000.0, (0.0, 45.0, 80.0)),
             ("metal film", 1.0, 0.2 + 3.3j, 1.5, 30.0, (0.0, 60.0)), ("Kretschmann", 1.5, 0.2 + 3.3j, 1.0, 50.0, (44.0,)),
             ("gap beyond TIR", 1.5, 1.0, 1.5, 300.0, (60.0,))]
    for label, n0, n1, n2, d, angles in films:
        for deg in angles:
            th = math.radians(deg)
            for pol in ("s", "p"):
                sf = tf.single_film(n0, n1, n2, d, 633.0, th, pol)
                base, S, Sc = sensitivities([n0, n1, n2], [d], 633.0, th, pol)
                res = run_tmm([n0, n1, n2], [d], 633.0, th, pol)
                k_t, k_r, _ = tmm_kappa(res)
                cT = 32 * U
                for key, err, ch in (("r", sf["err_r"], cT * k_r), ("t", sf["err_t"], cT * abs(res["t"]) * k_t)):
                    F = base[key]
                    tol = err + K_BACK * U * float(2 * S[key] + Sc[key]) + ch + 4 * U * float(abs(F))
                    out.append(Row(GROUP, f"single_film (Airy sum) {key} ({pol})", f"{label}, th0={deg:g} deg",
                                   sf[key], res[key], tol, "TMM rounding + stated err", float(abs(sf[key] - F)),
                                   float(abs(res[key] - F))))
    # Airy intensity formula of a lossless film (engine's stated err_T)
    for n0, n1, n2 in ((1.0, 2.3, 1.0), (1.0, 2.3, 1.52), (1.33, 1.6, 1.0), (1.0, 1.45, 3.5)):
        for lam in (450.0, 633.0, 1064.0, 1550.0):
            for pol in ("s", "p"):
                th = math.radians(25.0)
                a = tf.airy(n0, n1, n2, 1700.0, lam, th, pol)
                base, S, Sc = sensitivities([n0, n1, n2], [1700.0], lam, th, pol)
                res = run_tmm([n0, n1, n2], [1700.0], lam, th, pol)
                k_t, _, _ = tmm_kappa(res)
                F = base["T"]
                tol = (a["err_T"] + K_BACK * U * float(2 * S["T"] + Sc["T"]) + 2 * 32 * U * float(F) * k_t
                       + 4 * U * float(F))
                out.append(Row(GROUP, f"airy T ({pol})", f"{n0}/{n1}/{n2}, d=1700 nm, lam={lam:g}, th0=25 deg",
                               a["T"], res["T"], tol, "TMM rounding + stated err", float(abs(a["T"] - F)),
                               float(abs(res["T"] - F))))
    # quarter-wave layer and stack at the design wavelength (closed forms, bounded with Fe)
    for n0, n1, n2 in ((1.0, 1.38, 1.5), (1.0, math.sqrt(1.5), 1.5), (1.0, 2.0, 1.5), (1.33, 1.6, 1.52)):
        eng = tf.quarter_wave_R(n0, n1, n2)
        fe = tf.quarter_wave_R(Fe(n0), Fe(n1), Fe(n2))
        assert fe.v == eng
        rows = _stack_rows(f"quarter-wave {n0}/{n1:.6g}/{n2}", [n0, n1, n2], [633.0 / 4 / n1], 633.0, 0.0, "s",
                           {"r": 0j, "t": 0j, "R": eng, "T": 0.0}, "quarter_wave_R", closed_form=True)
        row = rows[2]
        row.tol += fe.e
        row.basis = "TMM rounding + running error"
        out.append(row)
    for pairs in (1, 5, 15):
        ns = [1.0] + [2.3, 1.38] * pairs + [1.52]
        ds = [633 / 4 / 2.3, 633 / 4 / 1.38] * pairs
        eng = tf.quarter_wave_stack_R(1.0, 2.3, 1.38, 1.52, pairs)
        fe = tf.quarter_wave_stack_R(Fe(1.0), Fe(2.3), Fe(1.38), Fe(1.52), pairs)
        assert fe.v == eng
        row = _stack_rows(f"(2.3/1.38)^{pairs} on 1.52", ns, ds, 633.0, 0.0, "s", {"r": 0j, "t": 0j, "R": eng,
                                                                                 "T": 0.0}, "quarter_wave_stack_R",
                          closed_form=True)[2]
        row.tol += fe.e
        row.basis = "TMM rounding + running error"
        out.append(row)
    # frustrated TIR through a gap (closed form, bounded with Fe)
    for d, deg in ((100.0, 45.0), (300.0, 60.0), (1000.0, 60.0), (300.0, 41.81031489577862)):
        th = math.radians(deg)
        for pol in ("s", "p"):
            eng = tf.ftir_T(1.5, 1.0, d, 633.0, th, pol)
            with thin_films_bounded():
                fe = tf.ftir_T(Fe(1.5), Fe(1.0), Fe(d), Fe(633.0), Fe(th), pol)
            assert fe.v == eng, (fe, eng)
            row = _stack_rows(f"FTIR gap {d:g} nm", [1.5, 1.0, 1.5], [d], 633.0, th, pol,
                              {"r": 0j, "t": 0j, "R": 0.0, "T": eng}, "ftir_T", closed_form=True)[3]
            row.tol += fe.e
            row.basis = "TMM rounding + running error"
            out.append(row)
    # evanescent decay length beyond the critical angle: 1/Im(kz) in the exit medium of tmm
    thc = math.asin(1 / 1.5)
    for dth in (1e-9, 1e-6, 1e-3, 0.1, 0.5):
        th = thc + dth
        eng = tf.evanescent_length(1.5, 1.0, 633.0, th)
        res = run_tmm([1.5, 1.0], [], 633.0, th, "s")
        lib = 1 / res["kz_list"][-1].imag

        def L(n1, n2, lam, t):
            return lam / (2 * mp.pi * mp.sqrt((n1 * mp.sin(t)) ** 2 - n2 ** 2))
        n1, n2, lam_, t_ = mp.mpf(1.5), mp.mpf(1.0), mp.mpf(633.0), mp.mpf(th)
        exact = L(n1, n2, lam_, t_)
        S = sum(abs(L(*[v * (1 + HSTEP) if i == k else v for i, v in enumerate((n1, n2, lam_))], t_) - exact) / HSTEP
                for k in range(3))
        S += abs(L(n1, n2, lam_, t_ + HSTEP * (abs(t_) + abs(mp.tan(t_)))) - exact) / HSTEP
        # and tmm's absolute error in cos(theta_out) = cos(arcsin(x)): |dL/dc| |sin| (1 + |theta|), L = lam/(2 pi n2 Im c)
        x = n1 * mp.sin(t_) / n2
        c = mp.sqrt(x * x - 1)  # |Im cos(theta_out)|
        S += exact / c * abs(x) * (1 + abs(mp.asin(mp.mpc(x))))
        tol = U * eng + K_BACK * U * float(S) + 4 * U * eng
        out.append(Row(GROUP, "evanescent_length 1/kappa", f"glass/air, th0 = th_c + {dth:g} rad", eng, lib, tol,
                       "one rounding + TMM rounding", float(abs(eng - exact)), float(abs(lib - exact))))
    return out


def _field_rows():
    """Absorption per layer (Joule heating vs tmm's flux differences) and |E|^2 inside the layers (s polarization)."""
    out = []
    cases = [("absorbing 4 layers", [1.0, 1.45 + 0.01j, 2.0 + 0.5j, 1.38, 3.5 + 0.02j, 1.5], [120.0, 35.0, 200.0, 80.0],
              800.0, (0.0, 40.0, 85.0)),
             ("metal film 30 nm", [1.0, 0.2 + 3.3j, 1.5], [30.0], 633.0, (0.0, 60.0)),
             ("Kretschmann 50 nm", [1.5, 0.2 + 3.3j, 1.0], [50.0], 633.0, (44.0,)),
             ("weak absorber 500 nm", [1.0, 1.0 + 0.05j, 1.0], [500.0], 633.0, (0.0, 70.0))]
    for label, ns, ds, lam, angles in cases:
        N = len(ds)
        zs = [(0, -100.0)] + [(j, f * ds[j - 1]) for j in range(1, N + 1) for f in (0.0, 0.3, 0.999)]
        for deg in angles:
            th = math.radians(deg)
            base, S, Sc = sensitivities(ns, ds, lam, th, "s", zs=zs)
            res = run_tmm(ns, ds, lam, th, "s")
            k_t, _, _ = tmm_kappa(res)
            kE = float(base["kappa_E"])
            cE, cT = (14 * N + 12) * U, (20 * N + 12) * U
            ja = tf.joule_absorption_s(ns, ds, lam, th)
            lib_a = tmm.absorp_in_each_layer(res)
            for j in range(1, N + 1):
                A = float(base["A"][j - 1])
                Pin, Pout = float(abs(base["P"][j - 1])), float(abs(base["P"][j]))
                tol = (K_BACK * U * float(2 * S["A"][j - 1] + Sc["A"][j - 1]) + 2 * cE * kE * A
                       + math.log2(max(ja["nodes"], 2)) * U * A + 2 * cT * k_t * (Pin + Pout) + 4 * U * A)
                out.append(Row(GROUP, f"absorption in layer {j} (s)", f"{label}, th0={deg:g} deg",
                               ja["per_layer"][j - 1], float(lib_a[j]), tol, "TMM rounding (fluxes)",
                               abs(ja["per_layer"][j - 1] - A), abs(float(lib_a[j]) - A)))
            z_abs = [z if layer == 0 else sum(ds[:layer - 1]) + z for layer, z in zs]
            prof = interfaces.field_profile(ns, ds, lam, th, z_abs, "s")
            for i, (layer, zeta) in enumerate(zs):
                pr = tmm.position_resolved(layer, zeta, res)
                lib = abs(pr["Ey"]) ** 2
                E2 = float(base["E2"][i])
                tol = K_BACK * U * float(2 * S["E2"][i] + Sc["E2"][i]) + 2 * (cE * kE + cT * k_t) * E2 + 4 * U * E2
                out.append(Row(GROUP, "|E|^2 (s)", f"{label}, th0={deg:g} deg, layer {layer}, depth {zeta:.5g} nm",
                               float(prof[i]), float(lib), tol, "TMM rounding", abs(float(prof[i]) - E2),
                               abs(float(lib) - E2)))
    return out


@functools.lru_cache(maxsize=None)
@mp.workdps(DPS)
def rows() -> list[Row]:
    return _fresnel_rows() + _multilayer_rows() + _closed_form_rows() + _field_rows()


@pytest.mark.parametrize("row", params(rows()))
def test_optics(row):
    check(row)


@mp.workdps(DPS)
def test_reference_reproduces_closed_forms():
    """The mpmath reference agrees with closed forms where they exist: Fresnel at normal incidence, the quarter-wave
    layer and the quarter-wave stack (exact phases pi/2 are not representable in the binary64 thicknesses, so compare
    in mpmath with exact quarter-wave thicknesses)."""
    for n1, n2 in ((1.0, 1.5), (1.5, 1.0)):
        res = mp_solve([_m(n1), _m(n2)], [], mp.mpf(633), mp.mpf(0), "s")
        assert abs(res["r"] - (mp.mpf(n1) - n2) / (mp.mpf(n1) + n2)) < mp.mpf(10) ** -35
    n1 = mp.mpf("1.38")
    res = mp_solve([_m(1.0), mp.mpc(n1), _m(1.5)], [mp.mpf(633) / 4 / n1], mp.mpf(633), mp.mpf(0), "s")
    assert abs(res["R"] - ((1.5 - n1 ** 2) / (1.5 + n1 ** 2)) ** 2) < mp.mpf(10) ** -35
    assert abs(sum(res.get("A", [])) + res["R"] + res["T"] - 1) < mp.mpf(10) ** -35
