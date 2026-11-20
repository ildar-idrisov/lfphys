# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u35 orchestration: the planar structure built from the set-up (real materials of ``lfphys.core.optics.materials``,
or a model medium of a given index), the run's own curves and field (every number by the engine lfphys: transfer
matrices, field profile, Snell's law for the drawing), the polarisation of the light through the structure and the
analysers (``lfphys.core.optics.polarization``), the single-photon stream (emission from the source's line, the Born
rule at the structure on the photon's density matrix, the analysers' ports) and the detectors (efficiency, dark
counts, dead time and jitter of ``lfphys.theories.models.photodetector``).

Nothing here adds physics of its own but one relation: the probabilities, curves, angles, field, phases and group delays
come from ``lfphys.core.optics.interfaces`` and ``polarization``; the indices from ``materials``; the glass blocks'
internal transmittance exp(−4πκL/λ) is computed here from ``materials``' κ (Beer–Lambert, the relation that module
derives the SCHOTT glasses' κ from; an engine function for it was asked of the engine's processor); the detectors'
closed forms from ``photodetector``; the ray directions for the drawing from ``lfphys.theories.approx.ray_optics``; the
closed forms the checks compare with live in ``lfphys.core.optics.thin_films`` and ``polarization``.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field

import numpy as np

from lfphys.core.constants import C
from lfphys.core.optics import interfaces, materials, polarization as pol_
from lfphys.i18n import T
from lfphys.theories.approx import ray_optics
from lfphys.theories.models import photodetector as pd

ARM_M = 0.30  # source -> structure and structure -> detector, metres (each arm in its medium)
LAM_MIN, LAM_MAX = 300.0, 1600.0  # spectrum range, nm (narrowed to the materials' own ranges)
TH_MAX = 89.9  # degrees

STRUCTS = [("none", T("no boundary (the beam goes straight on)")), ("interface", T("boundary between two media")),
           ("ar", T("λ/4 anti-reflection layer")), ("bragg", T("Bragg mirror")), ("fp", T("Fabry–Pérot (film)")),
           ("metal", T("metal film")), ("tir", T("total internal reflection"))]
STRUCT_LABEL = dict(STRUCTS)
POL_LABEL = {"s": T("s (TE)"), "p": T("p (TM)"), "lin": T("linear at the angle ψ"),
             "unpol": T("unpolarised (ρ = I/2)")}
#: a photon's polarisation code for the drawing (frames, clicks): s, p, linear at ψ, unpolarised; a dark count
POL_CODE = {"s": 0, "p": 1, "lin": 2, "unpol": 3}
DARK_CODE = 9

# --- the media and the layers' materials (core.optics.materials) -------------------------------------------------
#: the bulk materials a medium may be (each relative to air at the wavelength in air for the SCHOTT glasses)
GLASSES = ("schott_n_bk7", "schott_n_f2", "schott_n_sf11")
BULK = GLASSES + ("sio2_malitson", "mgf2_dodge_o")
MATERIAL_NAME = {
    "air": T("air"),
    "schott_n_bk7": T("N-BK7 glass (SCHOTT)"), "schott_n_f2": T("N-F2 glass (SCHOTT)"),
    "schott_n_sf11": T("N-SF11 glass (SCHOTT)"), "sio2_malitson": T("fused silica (Malitson)"),
    "mgf2_dodge_o": T("MgF₂ crystal, ordinary ray (Dodge)"),
    "mgf2_film_rodriguez": T("MgF₂ film (Rodríguez-de Marcos et al.)"),
    "sio2_film_gao": T("SiO₂ film (Gao et al.)"), "ta2o5_film_gao": T("Ta₂O₅ film (Gao et al.)"),
    "au_johnson_christy": T("gold (Johnson and Christy)"), "ag_johnson_christy": T("silver (Johnson and Christy)"),
    "al_rakic": T("aluminium (Rakić)"), "model": T("model medium"),
}
SHORT = {"air": "air", "schott_n_bk7": "N-BK7", "schott_n_f2": "N-F2", "schott_n_sf11": "N-SF11",
         "sio2_malitson": "SiO₂", "mgf2_dodge_o": "MgF₂", "mgf2_film_rodriguez": "MgF₂", "sio2_film_gao": "SiO₂",
         "ta2o5_film_gao": "Ta₂O₅", "au_johnson_christy": "Au", "ag_johnson_christy": "Ag", "al_rakic": "Al"}
MEDIA = [("air", T("air (n = 1)"))] + [(m, MATERIAL_NAME[m]) for m in BULK] + [("model", T("model medium, index n"))]


def medium_index(mid: str, model_n: float, lam: float) -> float:
    """The (real) index of a medium at the wavelength lam (nm): air 1 exactly (the SCHOTT glasses are relative to
    air), a bulk material's n by ``materials.index`` (its kappa, <= 4e-8 for the glasses at the visible lines, is left
    out: README «Approximations»), a model medium its given n."""
    if mid == "air":
        return 1.0
    if mid == "model":
        return float(model_n)
    return float(materials.index(mid, lam).real)


def medium_dindex(mid: str, lam: float) -> float:
    """dn/dlam (per nm) of a medium: 0 for air and a model medium (no dispersion)."""
    if mid in ("air", "model"):
        return 0.0
    return float(materials.dindex(mid, lam).real)


def material_range(mid: str) -> tuple[float, float]:
    if mid in ("air", "model", None):
        return (0.0, math.inf)
    return tuple(materials.info(mid)["range_nm"])


@dataclass
class Structure:
    """A planar structure at one wavelength: the indices (numbers) and thicknesses, and what they are made of."""
    kind: str
    n_in: float
    n_out: float
    layers: list = field(default_factory=list)  # [(n complex, d nm, name, role, material id or None)]
    notes: list = field(default_factory=list)
    out_name: T = field(default_factory=lambda: T("exit medium"))
    lam: float = 632.8
    med_in: str = "model"
    med_out: str = "model"
    dns: list = field(default_factory=list)  # dn/dlam (per nm) of every medium: [incidence, layers..., exit]

    @property
    def ns(self):
        return [complex(self.n_in)] + [complex(L[0]) for L in self.layers] + [complex(self.n_out)]

    @property
    def ds(self):
        return [float(L[1]) for L in self.layers]

    @property
    def lossless(self) -> bool:
        return all(complex(L[0]).imag == 0 for L in self.layers)

    @property
    def thickness(self) -> float:
        return float(sum(self.ds))

    def describe(self) -> list[dict]:
        return [{"n": [complex(L[0]).real, complex(L[0]).imag], "d": L[1], "name": L[2], "role": L[3],
                 "mat": L[4] if len(L) > 4 else None} for L in self.layers]


def _layer_index(mat: str | None, model, lam: float) -> complex:
    """A layer's complex index at lam: a material's n + i kappa, or the model's number."""
    if mat in (None, "model"):
        return complex(model)
    return complex(materials.index(mat, lam))


def _layer_dindex(mat: str | None, lam: float) -> complex:
    if mat in (None, "model"):
        return 0j
    return complex(materials.dindex(mat, lam))


def quarter(mat: str | None, model, lam0: float) -> float:
    """A quarter-wave thickness at the design wavelength lam0 from the material's own index there (nm)."""
    return lam0 / (4.0 * _layer_index(mat, model, lam0).real)


def build_structure(p: dict, lam: float | None = None) -> Structure:
    """The layer list of the chosen structure (complex indices of real materials or model media at the wavelength lam,
    thicknesses in nm) from the set-up parameters."""
    kind = p["structure"]
    lam = float(p["lam_nm"]) if lam is None else float(lam)
    mi, mo = p["med_in"], p["med_out"]
    n0 = medium_index(mi, p["n0"], lam)
    ns = medium_index(mo, p["ns"], lam)
    dn0, dns = medium_dindex(mi, lam), medium_dindex(mo, lam)
    st = Structure(kind, n0, ns, lam=lam, med_in=mi, med_out=mo)
    layer_d = []
    if kind == "none":  # no boundary: the beam goes straight on in the incidence medium
        st.n_out = n0
        st.med_out = mi
        dns = dn0
        st.out_name = T("the same medium (no boundary)")
    elif kind == "interface":
        pass
    elif kind == "ar":
        mat, lam0 = p["ar_mat"], float(p["lam0_nm"])
        d = quarter(mat, p["ar_n"], lam0)
        st.layers = [(_layer_index(mat, p["ar_n"], lam), d, T("λ/4 film"), "film", None if mat == "model" else mat)]
        layer_d = [_layer_dindex(mat, lam)]
        nf0 = _layer_index(mat, p["ar_n"], lam0).real
        ideal = math.sqrt(medium_index(mi, p["n0"], lam0) * medium_index(mo, p["ns"], lam0))
        st.notes.append(T("Thickness λ₀/(4 n_f(λ₀)) = {d:.4g} nm with n_f(λ₀) = {nf:.6g}; the index that would cancel "
                          "the reflection at λ₀: √(n₀ n_s) = {ideal:.6g}.", d=d, nf=nf0, ideal=ideal))
    elif kind == "bragg":
        N, lam0 = int(p["pairs"]), float(p["lam0_nm"])
        if p["bragg_mat"] == "ta2o5_sio2":
            mH, mL, nHm, nLm = "ta2o5_film_gao", "sio2_film_gao", None, None
        else:
            mH, mL, nHm, nLm = "model", "model", p["nH"], p["nL"]
        dH, dL = quarter(mH, nHm, lam0), quarter(mL, nLm, lam0)
        nH, nL = _layer_index(mH, nHm, lam), _layer_index(mL, nLm, lam)
        for _ in range(N):
            st.layers += [(nH, dH, "H", "H", None if mH == "model" else mH),
                          (nL, dL, "L", "L", None if mL == "model" else mL)]
            layer_d += [_layer_dindex(mH, lam), _layer_dindex(mL, lam)]
        st.notes.append(T("Layer order: the incidence medium, then (H L)×{N:d}, then the substrate; every layer is "
                          "λ₀/4 at λ₀ = {lam0} nm with its own index there (H: {dH:.4g} nm, L: {dL:.4g} nm).",
                          N=N, lam0=lam0, dH=dH, dL=dL))
    elif kind == "fp":
        mat = p["fp_mat"]
        st.layers = [(_layer_index(mat, p["fp_n"], lam), float(p["fp_d_nm"]), T("film"), "film",
                      None if mat == "model" else mat)]
        layer_d = [_layer_dindex(mat, lam)]
    elif kind == "metal":
        mat = p["metal_mat"]
        st.layers = [(_layer_index(mat, complex(float(p["metal_n"]), float(p["metal_k"])), lam),
                      float(p["metal_d_nm"]), T("metal"), "metal", None if mat == "model" else mat)]
        layer_d = [_layer_dindex(mat, lam)]
    elif kind == "tir":
        gap = float(p["tir_gap_nm"])
        if gap > 0:  # a second prism of the same glass behind a gap of the rarer medium: frustrated TIR
            st.layers = [(ns, gap, T("gap"), "gap", None if mo == "model" else mo)]
            layer_d = [complex(dns)]
            st.n_out = n0
            st.out_name = T("second prism (n₀)")
            dns = dn0
        if n0 <= ns:
            st.notes.append(T("n₀ ≤ n_s: there is no total internal reflection (the light goes into the optically "
                              "denser medium)."))
    else:
        raise ValueError(f"unknown structure {kind!r}")
    st.dns = [complex(dn0)] + [complex(x) for x in layer_d] + [complex(dns)]
    return st


def materials_of(p: dict) -> list[str]:
    """Every material (dataset id) of the set-up: the media and the layers."""
    out = [m for m in (p["med_in"], p["med_out"]) if m not in ("air", "model")]
    k = p["structure"]
    if k == "ar" and p["ar_mat"] != "model":
        out.append(p["ar_mat"])
    if k == "bragg" and p["bragg_mat"] == "ta2o5_sio2":
        out += ["ta2o5_film_gao", "sio2_film_gao"]
    if k == "fp" and p["fp_mat"] != "model":
        out.append(p["fp_mat"])
    if k == "metal" and p["metal_mat"] != "model":
        out.append(p["metal_mat"])
    seen = []
    for m in out:
        if m not in seen:
            seen.append(m)
    return seen


def lam_range(p: dict) -> tuple[float, float]:
    """The wavelengths (nm) where every material of the set-up has data."""
    lo, hi = 0.0, math.inf
    for m in materials_of(p):
        a, b = material_range(m)
        lo, hi = max(lo, a), min(hi, b)
    if p["structure"] in ("ar", "bragg"):  # the design wavelength's own indices
        pass
    return lo, hi


# --- the glass blocks: half-cylinders centred on the rotary table -------------------------------------------------
#: the blocks' radius by default, mm: every medium other than air is a half-cylinder (a D-shaped block) whose flat face
#: is the structure's; a beam through the table's axis crosses it along a radius and meets its curved face at normal
#: incidence (the laboratory manuals' semicircular samples: Rutgers, «Fresnel Equations and Electromagnetic Boundary
#: Conditions»; Carnegie Mellon 33-353 Lab 1; Toronto PHY293/PHY294's D-lens)
BLOCK_MM = 25.0
#: the outcomes of one photon from the source to the detectors: the face's five (``polarization.OUTCOMES``) and the
#: three losses in the blocks: on the way in (reflected back by the entry's curved face or absorbed before the face),
#: in the reflection arm and in the transmission arm (absorbed along the radius or reflected back by the curved face)
LOSSES = ("L_in", "L_R", "L_T")


def side_media(p: dict) -> tuple[tuple[str, float], tuple[str, float]]:
    """The media of the two sides of the structure as the beams cross them, each (material, model index): no boundary
    leaves the beam in the incidence medium; a prism with a gap has a second prism of the incidence glass behind it."""
    inc = (p["med_in"], float(p["n0"]))
    if p["structure"] == "none" or (p["structure"] == "tir" and float(p["tir_gap_nm"]) > 0):
        return inc, inc
    return inc, (p["med_out"], float(p["ns"]))


def block_crossing(mid: str, model_n: float, lam: float, radius_mm: float, inward: bool) -> dict | None:
    """A beam's crossing of a half-cylinder of the medium ``mid`` along its radius (``inward``: from the curved face to
    the flat one; else outward): None where there is no block (air, or radius 0: a half-space). The curved face at
    normal incidence by the engine's transfer matrices (``interfaces.stack``, air n = 1, the medium by the real part of
    its index as at the face), for s and p; the bulk's internal transmittance exp(−4πκL/λ) along the radius L with the
    material's κ at λ (``materials.index``; Beer–Lambert, the law SCHOTT's κ comes from; a model medium has κ = 0)."""
    if mid == "air" or not radius_mm > 0:
        return None
    nz = complex(model_n) if mid == "model" else complex(materials.index(mid, lam))
    ns = [1.0, nz.real] if inward else [nz.real, 1.0]
    face = {q: float(interfaces.stack(ns, [], lam, 0.0, q)["T"]) for q in ("s", "p")}
    tau = math.exp(-4.0 * math.pi * nz.imag * radius_mm * 1e6 / lam)  # the radius in nm, as λ
    return {"n": nz.real, "kappa": nz.imag, "Tc": face, "tau": tau, "L_mm": float(radius_mm)}


def crossing_T(cr: dict | None, rho=None) -> float:
    """The share of a beam of state rho (its p, s weights; any state when None) that crosses a block: 1 without one.
    At normal incidence T_s = T_p (a check of the run), so the crossing does not change the beam's polarisation."""
    if cr is None:
        return 1.0
    if rho is None:
        Tc = 0.5 * (cr["Tc"]["s"] + cr["Tc"]["p"])
    else:
        wp, ws = float(np.real(rho[0, 0])), float(np.real(rho[1, 1]))
        Tc = (wp * cr["Tc"]["p"] + ws * cr["Tc"]["s"]) / (wp + ws) if wp + ws > 0 else cr["Tc"]["s"]
    return Tc * cr["tau"]


def blocks(p: dict, lam: float) -> dict:
    """The three crossings of the set-up at the wavelength lam: the way in (the incidence medium's block, inward), the
    reflection arm (the same block, outward) and the transmission arm (the exit side's block, outward)."""
    (mi, n0), (mo, no) = side_media(p)
    r = float(p["block_mm"])
    return {"in": block_crossing(mi, n0, lam, r, True), "R": block_crossing(mi, n0, lam, r, False),
            "T": block_crossing(mo, no, lam, r, False), "radius_mm": r}


def outcomes8(face: dict, bl: dict, rho, rho_R, rho_T) -> list[float]:
    """The eight outcomes of a photon from the source (``polarization.OUTCOMES`` then ``LOSSES``): the face's Born
    probabilities ``face`` (of a photon that reaches it) times the way in and each arm's crossing; they add to one."""
    p_in = crossing_T(bl["in"], rho)
    tR, tT = crossing_T(bl["R"], rho_R), crossing_T(bl["T"], rho_T)
    PR, PT = face["R_pass"] + face["R_reject"], face["T_pass"] + face["T_reject"]
    return [p_in * face["R_pass"] * tR, p_in * face["R_reject"] * tR, p_in * face["T_pass"] * tT,
            p_in * face["T_reject"] * tT, p_in * face["A"], 1.0 - p_in, p_in * PR * (1.0 - tR), p_in * PT * (1.0 - tT)]


# --- the engine's numbers for a structure -----------------------------------------------------------------
def rta(st: Structure, lam: float, theta: float, pol: str) -> dict:
    """r, t, R, T, A of the structure (lfphys transfer matrices). ``lam`` must be the structure's own wavelength for a
    structure of dispersive materials (``build_structure`` at that lam); the curves rebuild it per wavelength."""
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
    """Counts (k_1 … k_m) of n photons against the Born probabilities (p_1 … p_m) of the segment.

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


def poisson_two_sided(k: int, mu: float) -> float:
    """The exact two-sided tail of a Poisson count k of mean mu: min(1, 2 min(P(K <= k), P(K >= k)))."""
    from scipy import stats as sps
    if mu <= 0:
        return 1.0 if k == 0 else 0.0
    return float(min(1.0, 2.0 * min(sps.poisson.cdf(k, mu), sps.poisson.sf(k - 1, mu))))


def binom_two_sided(k: int, n: int, p: float) -> float:
    from scipy import stats as sps
    if n == 0:
        return 1.0
    if p <= 0.0 or p >= 1.0:
        return 1.0 if (k == 0 if p <= 0.0 else k == n) else 0.0
    return float(min(1.0, 2.0 * min(sps.binom.cdf(k, n, p), sps.binom.sf(k - 1, n, p))))


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
    for L in st.layers:
        n = complex(L[0])
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


def spectrum_grid(st: Structure, extra, lo: float = LAM_MIN, hi: float = LAM_MAX):
    """Uniform in 1/lambda (the interference phase is linear in it), fine enough for ~20 points per 2 pi of the
    round-trip phase of the whole stack; 300..1600 points, within [lo, hi] (the materials' common range)."""
    opd = sum(complex(L[0]).real * L[1] for L in st.layers)
    dphi = 4 * math.pi * opd * (1 / lo - 1 / hi)
    m = int(min(1600, max(300, math.ceil(dphi / (2 * math.pi / 20)))))
    g = 1.0 / np.linspace(1 / hi, 1 / lo, m)
    g = np.concatenate([g, [e for e in extra if e is not None and lo <= e <= hi]])
    return np.unique(g), m


def curves(p: dict, st: Structure, lam: float, theta: float, rho, extra_deg, extra_lam, spectrum: bool = True):
    """R, T, A against the angle (at lam) and against the wavelength (at theta; every wavelength with its own indices),
    for s and p and for the source's state rho (R_c = rho_pp R_p + rho_ss R_s: no cross term through an isotropic
    structure). Returns (the curves, the spectrum's grid size, which wavelengths have only lossless materials: a film
    may absorb at some wavelengths of its data and not at others)."""
    th = angle_grid(list(extra_deg) + [math.degrees(g) for g in grazing_angles(st)])
    out = {"th": th}
    for pol in ("s", "p"):
        rows = np.array([[v["R"], v["T"], v["A"]] for v in (rta(st, lam, math.radians(x), pol) for x in th)])
        out["R" + pol], out["T" + pol], out["A" + pol] = rows[:, 0], rows[:, 1], rows[:, 2]
    lo, hi = lam_range(p)
    lo, hi = max(LAM_MIN, lo), min(LAM_MAX, hi)
    # the grid's density from the stack at its design wavelength (a coating's grid is then the same at every λ)
    st_grid = build_structure(p, float(p["lam0_nm"])) if p["structure"] in ("ar", "bragg") else st
    lg, m_spec = spectrum_grid(st_grid, extra_lam, lo, hi)
    out["lam"] = lg
    lossless_l = np.ones(len(lg), bool)
    if spectrum:
        sxs = [build_structure(p, x) for x in lg]
        lossless_l = np.array([sx.lossless for sx in sxs], bool)
        for pol in ("s", "p"):
            rows = []
            for x, sx in zip(lg, sxs):
                v = rta(sx, x, theta, pol)
                rows.append([v["R"], v["T"], v["A"]])
            rows = np.array(rows)
            out["lR" + pol], out["lT" + pol], out["lA" + pol] = rows[:, 0], rows[:, 1], rows[:, 2]
    wp, ws = float(np.real(rho[0, 0])), float(np.real(rho[1, 1]))
    for pre in ("", "l") if spectrum else ("",):
        for q in ("R", "T", "A"):
            out[pre + q + "c"] = wp * out[pre + q + "p"] + ws * out[pre + q + "s"]
    return out, m_spec, lossless_l


def field_grid(st: Structure, lam: float):
    """Depths for |E|^2: the stack and a margin on each side (nm); dense enough for the standing waves. Each interface
    appears twice: at its depth (the deeper medium's side, as ``field_profile`` takes it) and one float before it (the
    shallower side), so that the jump of the p field's E_z at a boundary is drawn as a jump (E35's note)."""
    D = st.thickness
    zm = max(0.6 * lam, 0.2 * D)
    nmax = max([abs(complex(n).real) for n in st.ns] + [1.0])
    npts = int(min(6000, max(900, 10 * (D + 2 * zm) * 2 * nmax / lam)))
    z = np.linspace(-zm, D + zm, npts)
    edges = np.concatenate([[0.0], np.cumsum(st.ds)]) if st.layers else np.array([0.0])
    if st.kind == "none":
        edges = np.zeros(0)
    before = np.nextafter(edges, -np.inf)
    z = np.unique(np.concatenate([z, edges, before]))
    return z


def field(st: Structure, lam: float, theta: float, z, rho=None) -> np.ndarray:
    """|E|^2 relative to the incident light, for the source's polarisation state rho (s light when None):
    ``interfaces.field_intensity`` (rho_pp |E|^2_p + rho_ss |E|^2_s, exact: no cross term)."""
    if rho is None:
        return interfaces.field_profile(st.ns, st.ds, lam, theta, z, "s")
    return interfaces.field_intensity(st.ns, st.ds, lam, theta, z, rho)


def ray_angles(st: Structure, theta: float) -> dict:
    """Directions for the drawing (approximate ray optics, lfphys.theories.approx.ray_optics.snell): in every layer
    (real part of the index; None where the wave is evanescent there) and in the exit medium."""
    layers = []
    for L in st.layers:
        nr = complex(L[0]).real
        a = ray_optics.snell(st.n_in, nr, theta) if nr > 0 else None
        layers.append(None if a is None else math.degrees(a))
    out = ray_optics.snell(st.n_in, st.n_out, theta)
    return {"theta": math.degrees(theta), "layers": layers, "out": None if out is None else math.degrees(out)}


def group_index(n: float, dn: float, lam: float) -> float:
    """The group index n_g = n - lam dn/dlam of a lossless medium (the speed of a wave packet is c/n_g)."""
    return float(n - lam * dn)


def flight_times(st: Structure, theta: float, rho, radius_mm: float = 0.0) -> dict:
    """Flight times along the arms at the group velocity c/n_g of each medium (its dispersion from the dataset), plus
    the structure's group delays of reflection and transmission (``interfaces.group_delay`` with each material's
    dn/dlam; for a state with both s and p the intensity-weighted mean of the two delays in each arm: they differ by
    femtoseconds, far below the detectors' jitter). t_in: the source to the structure; t_R, t_T: the structure to the
    reflection and the transmission detectors. Each arm is ``ARM_M`` long: in a medium other than air, its radius
    ``radius_mm`` of the block in the medium and the rest in air (n_g = 1); with no block (radius 0) the whole arm in
    the medium (a half-space)."""
    lam = st.lam
    ng_in = group_index(st.n_in, st.dns[0].real, lam)
    ng_out = group_index(st.n_out, st.dns[-1].real, lam)
    L = min(float(radius_mm) * 1e-3, ARM_M) if radius_mm > 0 else ARM_M

    def arm(ng):  # the arm's optical delay: L in the medium (group index ng), the rest in air
        return (L * ng + (ARM_M - L) * 1.0) / C if ng != 1.0 else ARM_M / C
    t_in = arm(ng_in)
    tau = {}
    for q in ("s", "p"):
        if st.kind == "none":
            tau[q] = {"tau_r": 0.0, "tau_t": 0.0, "R": 0.0, "T": 1.0}
            continue
        with np.errstate(invalid="ignore", divide="ignore", over="ignore"):  # at θ_c exactly: a 0/0, reported nan
            gd = interfaces.group_delay(st.ns, st.ds, lam, theta, q, dns=st.dns)
        rr = rta(st, lam, theta, q)
        tr = gd["tau_r"] if math.isfinite(gd["tau_r"]) else 0.0
        tt = gd["tau_t"] if math.isfinite(gd["tau_t"]) else 0.0
        tau[q] = {"tau_r": tr, "tau_t": tt, "R": rr["R"], "T": rr["T"]}
    wp, ws = float(np.real(rho[0, 0])), float(np.real(rho[1, 1]))

    def mean(key, wkey):
        a, b = wp * tau["p"][wkey], ws * tau["s"][wkey]
        return (a * tau["p"][key] + b * tau["s"][key]) / (a + b) if a + b > 0 else 0.0

    tau_r, tau_t = mean("tau_r", "R"), mean("tau_t", "T")
    return {"t_in": t_in, "t_R": arm(ng_in) + tau_r, "t_T": arm(ng_out) + tau_t, "arm_m": ARM_M,
            "ng_in": ng_in, "ng_out": ng_out, "tau_r": tau_r, "tau_t": tau_t,
            "tau": {q: {"r": tau[q]["tau_r"], "t": tau[q]["tau_t"]} for q in ("s", "p")}}


def rng_for(seed: int, params: dict) -> np.random.Generator:
    """The world's random generator: its seed and its set-up together (the set-up's parameters as sorted JSON, hashed
    to 64 bits), so that every set-up of an atlas, all of which share one seed, draws its own independent sample. With
    the seed alone every point of a lab's grid drew the same random numbers (common random numbers): the fluctuations
    of neighbouring set-ups moved together, a fit across them saw χ²/dof ≈ 0.2 and a shared bias (found by W35 on the
    first build of the Boundary atlas, 2026-11-18)."""
    text = json.dumps({k: params[k] for k in sorted(params)}, sort_keys=True, default=repr)
    key = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "little")
    return np.random.default_rng([int(seed), key])


# --- the source -------------------------------------------------------------------------------------------------
COMB = 33  # wavelengths that sample the source's Gaussian line over +-4 sigma
COMB_SPAN = 4.0


def line_comb(lam0: float, fwhm: float) -> tuple[np.ndarray, np.ndarray]:
    """The source's line as a comb: (wavelengths, probabilities). A Gaussian of full width at half maximum ``fwhm``
    (nm) sampled at COMB wavelengths over +-COMB_SPAN sigma with Gaussian weights (renormalised); a monochromatic
    source (fwhm 0) is one wavelength."""
    if not fwhm > 0:
        return np.array([float(lam0)]), np.array([1.0])
    sig = fwhm * pd.FWHM_TO_SIGMA
    x = np.linspace(-COMB_SPAN, COMB_SPAN, COMB)
    w = np.exp(-0.5 * x * x)
    return lam0 + sig * x, w / w.sum()


def source_state(p: dict) -> np.ndarray:
    """The density matrix of one photon of the source in the incident beam's (p, s) basis: linear at psi from p
    towards s (s light psi = 90°, p light psi = 0°) or unpolarised (I/2)."""
    m = p["pol"]
    if m == "unpol":
        return pol_.unpolarised()
    psi = {"s": math.pi / 2, "p": 0.0}.get(m, math.radians(float(p["psi_deg"])))
    return pol_.density(pol_.jones_linear(psi))


#: an analyser device: (k1, k2), or None when out
def analyser(p: dict, arm: str):
    """The analyser before the detectors of an arm ('R' or 'T'): None (out: one detector) or (alpha rad, k1, k2)."""
    dev = p["ana" + arm]
    if dev == "out":
        return None
    k1, k2 = (1.0, 0.0) if dev == "ideal" else (float(p["ana_k1"]), float(p["ana_k2"]))
    return math.radians(float(p["ana" + arm + "_deg"])), k1, k2


def ports(a):
    return None if a is None else pol_.beam_splitter(a[0], a[1], a[2])


def outcome_probs(st: Structure, theta: float, rho, aR, aT) -> dict:
    """The Born probabilities of the five outcomes (``polarization.OUTCOMES``: R_pass, R_reject, T_pass, T_reject,
    A) for one photon of state rho at the structure st, with the analysers aR, aT (``analyser``); plus the boundary
    matrices and the arms' states."""
    bm = pol_.boundary_matrices(st.ns, st.ds, st.lam, theta)
    if st.kind == "none":  # exactly: no boundary (M_R = 0, M_T = I)
        bm = pol_.boundary_matrices([st.n_in, st.n_in], [], st.lam, theta)
    pr = pol_.outcome_probabilities(rho, bm, ports(aR), ports(aT))
    th = pol_.through(rho, bm)
    return {"probs": pr, "bm": bm, "rho_R": th["rho_R"], "rho_T": th["rho_T"]}


# --- the detectors ------------------------------------------------------------------------------------------------
DETECTORS = [("spcm_aqrh_14_650nm", pd.DEVICES["spcm_aqrh_14_650nm"]["title"]),
             ("ideal", T("ideal detector (η = 1, no dark counts, no dead time, no jitter): an idealisation"))]


def detector_of(p: dict) -> pd.Detector:
    d = p["det"]
    return pd.IDEAL if d == "ideal" else pd.DEVICES[d]["detector"]


class DetectorState:
    """One single-photon detector in time (``photodetector`` model): photon arrivals detected with probability eta,
    Poisson dark counts, a non-paralysable dead time applied to the merged stream in time order (carried from one
    step to the next), Gaussian jitter on the recorded tags."""

    def __init__(self, det: pd.Detector, rng, t0: float = 0.0):
        self.d, self.rng = det, rng
        self.last = -math.inf  # the last recorded count's true time
        self.t = t0  # dark counts generated up to here

    def step(self, t1: float, arrivals: np.ndarray):
        """Counts on (self.t, t1]: ``arrivals`` the photons' arrival times there (sorted or not). Returns (times of the
        recorded counts (true), their tags (jittered), is_dark per recorded count, indices of the arrivals recorded,
        detected-before-dead-time count, dark counts generated)."""
        d = self.d
        a = np.asarray(arrivals, float)
        det_mask = (self.rng.random(len(a)) < d.eta) if d.eta < 1.0 else np.ones(len(a), bool)
        dark = pd.poisson_times(d.dark_rate, self.t, t1, self.rng) if d.dark_rate > 0 and t1 > self.t else np.zeros(0)
        self.t = t1
        idx = np.nonzero(det_mask)[0]
        times = np.concatenate([a[idx], dark])
        src = np.concatenate([idx, np.full(len(dark), -1, np.int64)])
        order = np.argsort(times, kind="stable")
        times, src = times[order], src[order]
        keep = np.ones(len(times), bool)
        if d.dead_time > 0 and len(times):
            # the engine's non-paralysable rule (photodetector, the model's own time-stream Monte Carlo) on the merged
            # stream, with the last recorded count of the previous step in front of it (it is recorded already)
            lead = np.isfinite(self.last)
            merged = np.concatenate([[self.last], times]) if lead else times
            k = pd._nonparalysable(merged, d.dead_time)
            keep = k[1:] if lead else k
            if keep.any():
                self.last = float(times[keep][-1])
        elif len(times):
            self.last = float(times[-1])
        times, src = times[keep], src[keep]
        tags = times + self.rng.normal(0.0, d.jitter_sigma, len(times)) if d.jitter_sigma > 0 else times.copy()
        return times, tags, src < 0, src[src >= 0], int(len(idx)), int(len(dark))


# --- the photon stream ------------------------------------------------------------------------------------------------
FIELDS = {"pid": np.int64, "te": np.float64, "ts": np.float64, "lam": np.float64, "kl": np.int32, "pol": np.int8,
          "sege": np.int32, "stage": np.int8, "out": np.int8, "seg": np.int32, "tR": np.float64, "tT": np.float64,
          "wR": np.float64, "wT": np.float64, "tdet": np.float64}


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
