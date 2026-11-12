# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The rainbow of ray optics (Descartes) and Airy's wave theory of it: approximations of the exact Mie series
(lfphys.core.optics.mie, mie_debye) kept for comparison (plan P1/P14.8, batch B8).

A ray hits a sphere of relative index m at impact parameter b (in units of the radius; b = sin i, i the angle of
incidence, sin i = m sin r). After p chords inside (p - 1 internal reflections; p = 0 the external reflection) it is
deviated by

    D_0 = pi - 2 i,   D_p = (p - 1) pi + 2 i - 2 p r  (p >= 1),   scattering angle theta = arccos(cos D).

Descartes (1637): theta has an extremum for p >= 2 where dD/db = 0, cos^2 i = (m^2 - 1)/(p^2 - 1) (b^2 = (p^2 - m^2)/
(p^2 - 1)); rays crowd there (the rainbow angle theta_R; for m = 4/3: 137.97 deg for p = 2, the primary bow 42 deg
around the antisolar point; 129.02 deg for p = 3, the secondary bow outside it). Between the two, no rays of p = 2, 3
arrive: Alexander's dark band. Near theta_R, theta - theta_R = (h/2)(b - b_R)^2 with h = d^2 theta/db^2 =
sign(sin D_R) D''(b_R), D'' = 2b/cos^3 i - 2p b/(m^3 cos^3 r).

Classical intensity (each ray an energy tube): |S_j|^2 = x^2 |eps_j|^2 b / (sin theta |d theta/db|) per ray, eps_j the
product of the Fresnel amplitudes along the ray (|eps|^2 = R for p = 0, (1 - R)^2 R^(p-1) for p >= 1; j = 1 for the
perpendicular, s, polarisation, j = 2 for the parallel, p) — infinite at theta_R.

Airy (1838): the wavefront near the rainbow ray is cubic; the phase x (Theta(b) - theta) integrated over b gives
    |S_j|^2 = 2 pi |eps_j|^2 (b_R / sin theta_R) x^(7/3) (2/|h|)^(2/3) Ai^2(-z),
    z = sign(h) (2/|h|)^(1/3) x^(2/3) (theta - theta_R),
derived here so that far from theta_R on the bright side it averages to the two classical rays (tests); its maxima
(the main bow and the supernumerary bows) at the zeros a'_k of Ai': theta_k = theta_R - sign(h) a'_k (|h|/2)^(1/3)
x^(-2/3) (a'_1 = -1.0188: the main maximum lies on the bright side, beyond Descartes' angle by ~x^(-2/3)). The theory
assumes a single cubic wavefront and constant eps: it fails for the parallel polarisation near the Brewster angle of
the internal reflection, far from theta_R, and it has no glory, no surface waves and no interference between orders.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import optimize, special

ABOUT = {
    "layer": "theories", "kind": "approximation",
    "title": "Радуга лучевой оптики (Декарт) и теория Эйри",
    "statement": "Угол отклонения луча с p хордами внутри шара; угол радуги Декарта для k внутренних отражений; тёмная "
                 "полоса Александра; классическая интенсивность лучевых трубок с френелевскими множителями; теория "
                 "Эйри: интенсивность Ai²(−z) у угла радуги, положения главной и дополнительных дуг.",
    "validity": "x ≫ 1 (размер ≫ длины волны); Эйри — у угла радуги, |θ − θ_R| порядка x^(−2/3); хуже для "
                "параллельной поляризации (рядом угол Брюстера внутреннего отражения); нет глории, поверхностных "
                "волн и интерференции разных порядков",
    "basis": ["Descartes, Les Météores (1637)", "Airy, Trans. Camb. Phil. Soc. 6, 379 (1838)",
              "van de Hulst, Light Scattering by Small Particles (1957), гл. 13", "Nussenzveig, Sci. Am. 236 (4), 116 "
              "(1977)"],
    "conflicts": ["lfphys.core.optics.mie, mie_debye: точная волновая теория — у угла радуги лучи дают бесконечность, "
                  "Эйри смещает максимум и даёт дополнительные дуги, но отличается от ряда Дебая (сильнее для "
                  "параллельной поляризации); глорию и поверхностные волны даёт только точный ряд"],
}


def angles(m: float, b):
    """(i, r): angle of incidence and of refraction for impact parameter b (radians)."""
    b = np.asarray(b, float)
    return np.arcsin(b), np.arcsin(b / m)


def deviation(m: float, p: int, b):
    """D_p(b) (radians): p = 0 external reflection, p >= 1 after p chords (p - 1 internal reflections)."""
    i, r = angles(m, b)
    if p == 0:
        return math.pi - 2.0 * i
    return (p - 1) * math.pi + 2.0 * i - 2.0 * p * r


def scattering_angle(D):
    """theta in [0, pi] of a deviation D."""
    return np.arccos(np.clip(np.cos(D), -1.0, 1.0))


def descartes(m: float, p: int) -> dict:
    """The rainbow ray of order p >= 2 (k = p - 1 internal reflections): b_R, i_R, r_R, D_R, theta_R (radians) and
    h = d^2 theta / db^2 at b_R (signed: > 0 where theta has a minimum, the bright side at larger theta)."""
    m = float(m)
    if p < 2:
        raise ValueError("a rainbow needs at least one internal reflection (p >= 2)")
    c2 = (m * m - 1.0) / (p * p - 1.0)
    if not 0.0 < c2 < 1.0:
        raise ValueError(f"no rainbow of order p = {p} for m = {m}: needs 1 < m < p")
    ci = math.sqrt(c2)
    i = math.acos(ci)
    b = math.sin(i)
    r = math.asin(b / m)
    D = (p - 1) * math.pi + 2 * i - 2 * p * r
    cr = math.cos(r)
    d2 = 2 * b / ci ** 3 - 2 * p * b / (m ** 3 * cr ** 3)
    h = math.copysign(1.0, math.sin(D)) * d2
    return {"p": p, "b": b, "i": i, "r": r, "D": D, "theta": float(scattering_angle(D)), "h": h}


def alexander_band(m: float) -> tuple[float, float]:
    """(theta_3, theta_2): the scattering angles of the secondary and primary rainbows; between them no rays of
    p = 2 or 3 arrive (Alexander's dark band)."""
    return descartes(m, 3)["theta"], descartes(m, 2)["theta"]


def fresnel_R(m: float, b, pol: str):
    """Power reflectance of the surface for a ray at impact parameter b, polarisation "s" (perpendicular, S1) or
    "p" (parallel, S2); the same inside (i <-> r) by reciprocity."""
    i, r = angles(m, b)
    with np.errstate(all="ignore"):
        if pol == "s":
            R = (np.sin(i - r) / np.sin(i + r)) ** 2
        elif pol == "p":
            R = (np.tan(i - r) / np.tan(i + r)) ** 2
        else:
            raise ValueError("pol must be 's' or 'p'")
    m0 = ((m - 1.0) / (m + 1.0)) ** 2  # normal incidence
    return np.where(np.asarray(b) == 0, m0, R)


def eps2(m: float, p: int, b, pol: str):
    """|eps|^2: the fraction of the ray's power left after its p chords (R for p = 0, (1 - R)^2 R^(p-1))."""
    R = fresnel_R(m, b, pol)
    return R if p == 0 else (1.0 - R) ** 2 * R ** (p - 1)


def dtheta_db(m: float, p: int, b):
    """d theta / d b (signed), from D'(b) = 2/cos i - 2p/(m cos r) (p >= 1), -2/cos i (p = 0)."""
    i, r = angles(m, b)
    dD = -2.0 / np.cos(i) if p == 0 else 2.0 / np.cos(i) - 2.0 * p / (m * np.cos(r))
    return np.sign(np.sin(deviation(m, p, b))) * dD


def rays(m: float, p: int, theta, n_grid: int = 4001):
    """The impact parameters b of the rays of order p leaving at scattering angle theta (radians, scalar): all roots
    of theta_p(b) = theta in (0, 1), found by bracketing on a grid and Brent's method."""
    bs = np.linspace(1e-9, 1.0 - 1e-12, n_grid)
    f = scattering_angle(deviation(m, p, bs)) - theta
    out = []
    for k in np.nonzero(np.sign(f[:-1]) * np.sign(f[1:]) < 0)[0]:
        out.append(optimize.brentq(lambda b: float(scattering_angle(deviation(m, p, b))) - theta, bs[k], bs[k + 1],
                                   xtol=1e-15))
    return out


def classical(m: float, p: int, x: float, theta, pol: str):
    """|S_j|^2 of ray optics (summed over the rays of order p), at angles theta (radians, array)."""
    th = np.atleast_1d(np.asarray(theta, float))
    out = np.zeros_like(th)
    for k, t in enumerate(th):
        for b in rays(m, p, t):
            out[k] += x * x * float(eps2(m, p, b, pol)) * b / (math.sin(t) * abs(float(dtheta_db(m, p, b))))
    return out


def airy(m: float, p: int, x: float, theta, pol: str):
    """Airy's |S_j|^2 near the rainbow of order p (see the module docstring)."""
    d = descartes(m, p)
    th = np.asarray(theta, float)
    h = abs(d["h"])
    z = math.copysign(1.0, d["h"]) * (2.0 / h) ** (1.0 / 3.0) * x ** (2.0 / 3.0) * (th - d["theta"])
    ai = special.airy(-z)[0]
    e2 = float(eps2(m, p, d["b"], pol))
    return 2 * math.pi * e2 * d["b"] / math.sin(d["theta"]) * x ** (7.0 / 3.0) * (2.0 / h) ** (2.0 / 3.0) * ai * ai


def airy_maxima(m: float, p: int, x: float, k: int = 5) -> np.ndarray:
    """The scattering angles (radians) of the first k maxima of Airy's intensity: the main bow (k = 1) and the
    supernumerary bows, theta_k = theta_R - sign(h) a'_k (|h|/2)^(1/3) x^(-2/3), a'_k the zeros of Ai'."""
    d = descartes(m, p)
    ap = special.ai_zeros(k)[1]  # a'_k < 0
    return d["theta"] - math.copysign(1.0, d["h"]) * ap * (abs(d["h"]) / 2.0) ** (1.0 / 3.0) * x ** (-2.0 / 3.0)


def ray_path(m: float, p: int, b: float, length: float = 3.0) -> np.ndarray:
    """The polyline of a ray in the plane of incidence (coordinates (x, z) in units of the radius, the ray coming from
    z = -length at x = b along +z): its entry point, the p - 1 internal reflection points, the exit point and a
    segment of the outgoing ray; for p = 0 the reflected ray from the entry point. For m < 1 a ray enters only if
    b < m (sin r = b/m); a larger b raises ValueError for p >= 1."""
    if not 0.0 <= b < 1.0:
        raise ValueError("0 <= b < 1")
    i = math.asin(b)
    entry = np.array([b, -math.cos(i)])
    pts = [np.array([b, -length]), entry]
    d_in = np.array([0.0, 1.0])
    nrm = entry.copy()  # outward normal at the entry point (unit: on the unit circle)
    if p == 0:
        out = d_in - 2.0 * (d_in @ nrm) * nrm
        pts.append(entry + length * out)
        return np.array(pts)
    if b >= m:
        raise ValueError("no refracted ray: b >= m (a sphere of m < 1 admits only b < m)")
    r = math.asin(b / m)
    psi = i
    cur = entry
    for _ in range(p):
        psi += math.pi - 2.0 * r
        cur = np.array([math.sin(psi), -math.cos(psi)])
        pts.append(cur)
    u = pts[-1] - pts[-2]
    u = u / np.linalg.norm(u)
    n = cur / np.linalg.norm(cur)
    cu = float(u @ n)
    t = m * u + (math.sqrt(max(0.0, 1.0 - m * m * (1.0 - cu * cu))) - m * cu) * n
    pts.append(cur + length * t / np.linalg.norm(t))
    return np.array(pts)
