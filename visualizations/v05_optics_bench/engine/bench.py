# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v05 orchestration: the planar structure built from the set-up, the run's own curves and field (every number by
the engine lfphys: transfer matrices, field profile, Snell's law for the drawing) and the single-photon stream
(emission, the Born rule at the structure with the computed R, T, A, detection).

Nothing here adds physics of its own: the probabilities, curves, angles and field come from
``lfphys.core.optics.interfaces``; the ray directions for the drawing from ``lfphys.theories.approx.ray_optics``;
the closed forms the checks compare with live in ``lfphys.core.optics.thin_films``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from lfphys.core.constants import C
from lfphys.i18n import T
from lfphys.core.optics import interfaces
from lfphys.theories.approx import ray_optics

ARM_M = 0.30  # source -> structure and structure -> detector, metres (each arm in its medium)
LAM_MIN, LAM_MAX = 300.0, 1600.0  # spectrum range, nm
TH_MAX = 89.9  # degrees

STRUCTS = [("interface", T("boundary between two media")), ("ar", T("λ/4 anti-reflection layer")),
           ("bragg", T("Bragg mirror")), ("fp", T("Fabry–Pérot (film)")), ("metal", T("metal film")),
           ("tir", T("total internal reflection"))]
STRUCT_LABEL = dict(STRUCTS)
POL_LABEL = {"s": T("s (TE)"), "p": T("p (TM)"), "unpol": T("unpolarised (50/50 s and p)")}


@dataclass
class Structure:
    kind: str
    n_in: float
    n_out: float
    layers: list = field(default_factory=list)  # [(n complex, d nm, name, role)]
    notes: list = field(default_factory=list)
    out_name: T = field(default_factory=lambda: T("exit medium"))

    @property
    def ns(self):
        return [complex(self.n_in)] + [complex(n) for n, *_ in self.layers] + [complex(self.n_out)]

    @property
    def ds(self):
        return [float(d) for _, d, *_ in self.layers]

    @property
    def lossless(self) -> bool:
        return all(complex(n).imag == 0 for n, *_ in self.layers)

    @property
    def thickness(self) -> float:
        return float(sum(self.ds))

    def describe(self) -> list[dict]:
        return [{"n": [complex(n).real, complex(n).imag], "d": d, "name": name, "role": role}
                for n, d, name, role in self.layers]


def build_structure(p: dict) -> Structure:
    """The layer list of the chosen structure (indices, thicknesses in nm) from the set-up parameters."""
    kind = p["structure"]
    n0, ns = float(p["n0"]), float(p["ns"])
    st = Structure(kind, n0, ns)
    if kind == "interface":
        pass
    elif kind == "ar":
        nf, lam0 = float(p["ar_n"]), float(p["lam0_nm"])
        st.layers = [(nf, lam0 / (4 * nf), T("λ/4 film"), "film")]
        ideal = math.sqrt(n0 * ns)
        st.notes.append(T("Thickness λ₀/(4 n_f) = {d:.4g} nm; the ideal index √(n₀ n_s) = {ideal:.6g}.",
                          d=lam0 / (4 * nf), ideal=ideal))
    elif kind == "bragg":
        nH, nL, N, lam0 = float(p["nH"]), float(p["nL"]), int(p["pairs"]), float(p["lam0_nm"])
        for _ in range(N):
            st.layers += [(nH, lam0 / (4 * nH), "H", "H"), (nL, lam0 / (4 * nL), "L", "L")]
        st.notes.append(T("Layer order: the incidence medium, then (H L)×{N:d}, then the substrate; every layer is "
                          "λ₀/4 at λ₀ = {lam0} nm (H: {dH:.4g} nm, L: {dL:.4g} nm).",
                          N=N, lam0=lam0, dH=lam0 / (4 * nH), dL=lam0 / (4 * nL)))
    elif kind == "fp":
        st.layers = [(float(p["fp_n"]), float(p["fp_d_nm"]), T("film"), "film")]
    elif kind == "metal":
        st.layers = [(complex(float(p["metal_n"]), float(p["metal_k"])), float(p["metal_d_nm"]), T("metal"), "metal")]
    elif kind == "tir":
        gap = float(p["tir_gap_nm"])
        if gap > 0:  # a second prism of the same glass behind a gap of the rarer medium: frustrated TIR
            st.layers = [(ns, gap, T("gap"), "gap")]
            st.n_out = n0
            st.out_name = T("second prism (n₀)")
        if n0 <= ns:
            st.notes.append(T("n₀ ≤ n_s: there is no total internal reflection (the light goes into the optically "
                              "denser medium)."))
    else:
        raise ValueError(f"unknown structure {kind!r}")
    return st


# --- the engine's numbers for a structure -----------------------------------------------------------------
def rta(st: Structure, lam: float, theta: float, pol: str) -> dict:
    """r, t, R, T, A of the structure (lfphys transfer matrices)."""
    return interfaces.stack(st.ns, st.ds, lam, theta, pol)


ROUNDOFF = 1e-14


def born_probs(res: dict) -> tuple[float, float, float]:
    """Probabilities of the three fates of one photon from the computed R, T, A. A = 1 - R - T of a lossless structure
    is round-off (|A| ~ 1e-16): below ROUNDOFF it is set to 0 and R = 1 - T; the three always sum to one."""
    R = min(max(res["R"], 0.0), 1.0)
    Tr = min(max(res["T"], 0.0), 1.0 - R)
    A = 1.0 - R - Tr
    if A < ROUNDOFF:
        A, R = 0.0, 1.0 - Tr
    return R, Tr, A


P_5SIGMA = math.erfc(5.0 / math.sqrt(2.0))  # two-sided tail of 5 standard deviations: 5.73e-7


def outcome_test(counts, probs) -> dict:
    """Counts (k_R, k_T, k_A) of n photons against the Born probabilities (p_R, p_T, p_A) of the segment.

    Under the hypothesis each count is Binomial(n, p_j); for every outcome with 0 < p_j < 1 the exact two-sided tail
    P_j = min(1, 2 min(P(K <= k_j), P(K >= k_j))) is computed, and the m tails are combined by Bonferroni:
    p = min(1, m min_j P_j) (valid for dependent tests, so for the multinomial counts). An outcome with p_j = 0 that
    occurred, or with p_j = 1 that did not, has p = 0. The test fails below P_5SIGMA, the false-alarm rate of the
    former 5-sigma binomial test of R (review 2026-10-23, V5-4: R alone let a swap of T and A pass). Exact tails, so
    it holds for small expectations too (one photon with p_j = 1e-6 is not a 220-sigma event). Pearson's chi^2 with
    m - 1 degrees of freedom is returned for information. Returns dict(p, z, chi2, dof, m)."""
    from scipy import stats as sps
    k = [int(x) for x in counts]
    n = sum(k)
    pv, z, chi2, m = [], [], 0.0, 0
    for kj, pj in zip(k, probs):
        pj = float(pj)
        if pj <= 0.0 or pj >= 1.0:
            impossible = (kj > 0) if pj <= 0.0 else (kj < n)
            pv.append(0.0 if impossible else 1.0)
            z.append(math.inf if impossible else 0.0)
            continue
        m += 1
        lo, hi = sps.binom.cdf(kj, n, pj), sps.binom.sf(kj - 1, n, pj)
        pv.append(min(1.0, 2.0 * min(lo, hi)))
        sd = math.sqrt(n * pj * (1 - pj))
        z.append((kj - n * pj) / sd)
        chi2 += (kj - n * pj) ** 2 / (n * pj)
    worst = min(pv) if pv else 1.0
    p = 0.0 if worst == 0.0 else min(1.0, max(m, 1) * worst)
    return {"p": float(p), "z": z, "chi2": float(chi2), "dof": max(m - 1, 0), "m": m}


def mix(a: dict, b: dict) -> dict:
    return {k: 0.5 * (a[k] + b[k]) for k in ("R", "T", "A")}


def critical_from_T(st_like: Structure, lam: float) -> float | None:
    """The angle beyond which the run's transmitted power vanishes (the exit wave is evanescent), found by bisection
    on T(theta) of the transfer matrices (T is exactly 0 there because Re(n_out cos theta_out) = 0). The bisection
    runs to adjacent binary64 angles and returns the first one at which T = 0, so that "theta >= theta_c" is the
    run's own T(theta) = 0 (review 2026-10-23, V5-1: with the midpoint of a 1e-15 bracket, an angle a few ulp above
    theta_c could still transmit, or have a decay constant exactly 0)."""
    lo, hi = 0.0, math.radians(89.999)  # at exactly 90 deg cos(theta0) rounds to 0 and the matrices are singular
    if rta(st_like, lam, hi, "s")["T"] != 0.0:
        return None
    if rta(st_like, lam, lo, "s")["T"] == 0.0:
        return None  # opaque at normal incidence (no boundary to find)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if not lo < mid < hi:  # adjacent floats
            break
        if rta(st_like, lam, mid, "s")["T"] > 0.0:
            lo = mid
        else:
            hi = mid
    return hi


def brewster_from_rp(n_in: float, n_out: float, lam: float, th_hi: float | None) -> float | None:
    """Zero of the run's r_p(theta) for a single boundary (Brent's method on Re r_p of the transfer matrices)."""
    from scipy.optimize import brentq
    if n_in == n_out:
        return None
    face = Structure("interface", n_in, n_out)
    hi = (th_hi - 1e-9) if th_hi is not None else math.radians(89.999)
    f = lambda th: rta(face, lam, th, "p")["r"].real  # noqa: E731
    a, b = f(0.0), f(hi)
    if a * b > 0:
        return None
    return brentq(f, 0.0, hi, xtol=1e-15, rtol=4 * np.finfo(float).eps, maxiter=200)


def grazing_angles(st: Structure) -> list[float]:
    """Angles (rad) at which the wave inside an inner lossless layer grazes its boundaries (n0 sin theta = n_j): the
    gap of the prism set-up at the face's critical angle, a low-index layer seen from a denser medium. The angle curves
    sample them exactly (the engine's characteristic matrices are regular there)."""
    out = []
    for n, *_ in st.layers:
        n = complex(n)
        if n.imag == 0 and 0 < n.real < st.n_in:
            out.append(math.asin(n.real / st.n_in))
    return out


def angle_grid(extra_deg) -> np.ndarray:
    g = list(np.linspace(0.0, TH_MAX, 360))
    for e in extra_deg:
        if e is None:
            continue
        for off in (0.0, 1e-4, 1e-3, 1e-2, 3e-2, 0.1, 0.3):
            for s in (-1, 1):
                v = e + s * off
                if 0.0 <= v <= TH_MAX:
                    g.append(v)
    return np.unique(np.round(np.asarray(g), 12))


def spectrum_grid(st: Structure, extra) -> np.ndarray:
    """Uniform in 1/lambda (the interference phase is linear in it), fine enough for ~20 points per 2 pi of the
    round-trip phase of the whole stack; 300..1600 points."""
    opd = sum(complex(n).real * d for n, d, *_ in st.layers)
    dphi = 4 * math.pi * opd * (1 / LAM_MIN - 1 / LAM_MAX)
    m = int(min(1600, max(300, math.ceil(dphi / (2 * math.pi / 20)))))
    g = 1.0 / np.linspace(1 / LAM_MAX, 1 / LAM_MIN, m)
    g = np.concatenate([g, [e for e in extra if e is not None and LAM_MIN <= e <= LAM_MAX]])
    return np.unique(g), m


def curves(st: Structure, lam: float, theta: float, pol_mode: str, extra_deg, extra_lam):
    """R, T, A against the angle (at lam) and against the wavelength (at theta), for s and p and for the source's
    polarization (s, p or the 50/50 mixture)."""
    th = angle_grid(list(extra_deg) + [math.degrees(g) for g in grazing_angles(st)])
    out = {"th": th}
    for pol in ("s", "p"):
        rows = np.array([[v["R"], v["T"], v["A"]] for v in (rta(st, lam, math.radians(x), pol) for x in th)])
        out["R" + pol], out["T" + pol], out["A" + pol] = rows[:, 0], rows[:, 1], rows[:, 2]
    lg, m_spec = spectrum_grid(st, extra_lam)
    out["lam"] = lg
    for pol in ("s", "p"):
        rows = np.array([[v["R"], v["T"], v["A"]] for v in (rta(st, x, theta, pol) for x in lg)])
        out["lR" + pol], out["lT" + pol], out["lA" + pol] = rows[:, 0], rows[:, 1], rows[:, 2]
    for pre in ("", "l"):
        for q in ("R", "T", "A"):
            s_, p_ = out[pre + q + "s"], out[pre + q + "p"]
            out[pre + q + "c"] = s_ if pol_mode == "s" else p_ if pol_mode == "p" else 0.5 * (s_ + p_)
    return out, m_spec


def field_grid(st: Structure, lam: float):
    """Depths for |E|^2: the stack and a margin on each side (nm); dense enough for the standing waves."""
    D = st.thickness
    zm = max(0.6 * lam, 0.2 * D)
    nmax = max([abs(complex(n).real) for n in st.ns] + [1.0])
    npts = int(min(6000, max(900, 10 * (D + 2 * zm) * 2 * nmax / lam)))
    z = np.linspace(-zm, D + zm, npts)
    edges = np.concatenate([[0.0], np.cumsum(st.ds)]) if st.layers else np.array([0.0])
    z = np.unique(np.concatenate([z, edges]))
    return z


def field(st: Structure, lam: float, theta: float, z) -> np.ndarray:
    return interfaces.field_profile(st.ns, st.ds, lam, theta, z, "s")


def ray_angles(st: Structure, theta: float) -> dict:
    """Directions for the drawing (approximate ray optics, lfphys.theories.approx.ray_optics.snell): in every layer
    (real part of the index; None where the wave is evanescent there) and in the exit medium."""
    layers = []
    for n, *_ in st.layers:
        nr = complex(n).real
        a = ray_optics.snell(st.n_in, nr, theta) if nr > 0 else None
        layers.append(None if a is None else math.degrees(a))
    out = ray_optics.snell(st.n_in, st.n_out, theta)
    return {"theta": math.degrees(theta), "layers": layers, "out": None if out is None else math.degrees(out)}


def flight_times(st: Structure) -> dict:
    """Flight times along the arms at the speed c/n (non-dispersive media: phase = group velocity)."""
    t_in = ARM_M * st.n_in / C
    return {"t_in": t_in, "t_R": ARM_M * st.n_in / C, "t_T": ARM_M * st.n_out / C, "arm_m": ARM_M}


# --- the photon stream ------------------------------------------------------------------------------------
FIELDS = {"pid": np.int64, "te": np.float64, "ts": np.float64, "lam": np.float64, "pol": np.int8, "sege": np.int32,
          "stage": np.int8, "out": np.int8, "seg": np.int32, "tR": np.float64, "tT": np.float64, "wR": np.float64,
          "wT": np.float64, "tdet": np.float64}


class Stream:
    """Photons under way (struct of arrays). stage 0: flying to the structure; stage 1: fate drawn at the
    structure, flying to its detector (absorbed ones are revealed at the structure itself)."""

    def __init__(self):
        self.a = {k: np.zeros(0, dt) for k, dt in FIELDS.items()}

    def __len__(self):
        return len(self.a["pid"])

    def add(self, **cols):
        n = len(next(iter(cols.values())))
        for k, dt in FIELDS.items():
            v = cols.get(k)
            col = np.zeros(n, dt) if v is None else np.asarray(v, dt)
            if v is None and k in ("out", "seg"):
                col[:] = -1
            self.a[k] = np.concatenate([self.a[k], col])

    def keep(self, mask):
        for k in self.a:
            self.a[k] = self.a[k][mask]
