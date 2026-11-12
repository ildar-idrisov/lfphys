# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v09 apparatus over the engine lfphys (no physics of its own): the manoeuvres flown from rest (closed loops of
velocity space, planar and not), their references, and the field of three-burn loops that the volume and the slice
planes show.

Velocity space is drawn as the ball of velocities beta = v/c, |beta| < 1 (the Beltrami-Klein picture: geodesics, i.e.
burns of fixed direction, are straight chords; the sphere |beta| = 1 is light). Every quantity comes from
lfphys.core.spin_transport and lfphys.core.lorentz.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import lorentz as LZ
from lfphys.core import spin_transport as T

# one g of thrust in light-years per year squared (c = 1 ly/yr): 9.80665 m/s^2 * (Julian year)^2 / light-year
from lfphys.core.constants import LIGHT_YEAR, YEAR_JULIAN

G_LY = 9.80665 * YEAR_JULIAN**2 / LIGHT_YEAR

LOOPS = [
    ("thomas", "равномерное движение по окружности (прецессия Томаса)"),
    ("circle", "круг через покой (лучшее для плоских петель)"),
    ("triangle", "три импульса: треугольник"),
    ("polygon", "правильный многоугольник через покой"),
    ("crown", "корона: неплоский многоугольник (вершины выше и ниже)"),
    ("helix", "винт: тяга поворачивается вокруг наклонной оси, потом возврат"),
    ("seam", "шов мяча на сфере пространства скоростей (неплоский)"),
]
PLANAR = ("thomas", "circle", "triangle", "polygon")
SEAM_BURNS = 96  # burns of the seam polygon (the smooth seam is its limit; the difference to 2x is measured)
FIELD_BETA_MAX = 0.999  # the field is computed for |beta| <= this (gamma <= 22.4); beyond: blank
ETA_LIMIT = 7.0  # a manoeuvre may reach rapidity 7 (gamma ~ 550): beyond, float64 loses the rotation (refused)


def repeated(verts, m):
    """The vertices of a loop flown m times: back through rest between the repetitions (polygon_burns adds rest at the
    start and the end)."""
    out = []
    for k in range(m):
        out += list(verts) + ([np.zeros(3)] if k < m - 1 else [])
    return out


def check_reach(pieces):
    """Refuse a manoeuvre that comes closer to light than float64 can follow (rapidity above ETA_LIMIT), looking at
    the exact states every 0.05 of fuel before anything else is computed from them."""
    gmax = 1.0
    for _, q in T.Manoeuvre(pieces).states(ds=0.05):
        g = float(q.M[0, 0])
        gmax = max(gmax, g) if math.isfinite(g) else math.inf
        if gmax > math.cosh(ETA_LIMIT):
            raise ValueError(f"манёвр подходит к скорости света ближе, чем позволяет точность расчёта (γ > "
                             f"{math.cosh(ETA_LIMIT):.0f}): уменьшите ρ, χ или число повторов")


def base_frame(nth_deg: float, nph_deg: float):
    """The loop's base plane: its normal n from the angles (theta from z, azimuth phi), and in-plane axes e1, e2 with
    e1 x e2 = n; e1 is the horizontal direction closest to x."""
    t, p = math.radians(nth_deg), math.radians(nph_deg)
    n = np.array([math.sin(t) * math.cos(p), math.sin(t) * math.sin(p), math.cos(t)])
    ref = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 0.0, 1.0])
    e1 = ref - (ref @ n) * n
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    return e1, e2, n


def _on_sphere(center_rho, e1, d, rho):
    """The point at distance rho from the centre c = tanh(center_rho) e1 in direction d (unit, in c's boost frame)."""
    return LZ.add_velocities(math.tanh(center_rho) * e1, math.tanh(rho) * np.asarray(d, float))


def build(p: dict):
    """The manoeuvre of the world's parameters: (pieces, info). ``info``: planar, normal (planar loops), reference
    (the holonomy angle a closed form gives, accumulated: may exceed 2 pi) and how it was obtained, vertices (lab
    velocities of the burns' ends, for drawing), loop_pieces (the pieces of one loop when a polygon is flown m times)."""
    kind, rho, m = p["loop"], float(p["rho"]), int(p["turns"])
    e1, e2, n = base_frame(float(p["nth"]), float(p["nph"]))
    chi = math.radians(float(p["chi"]))
    info = {"kind": kind, "planar": kind in PLANAR, "normal": n.tolist(), "e1": e1.tolist(), "e2": e2.tolist()}
    if kind == "thomas":
        pieces = [T.Burn(tuple(e1), rho),
                  T.Turn(tuple(e2), tuple(n), 1.0 / math.tanh(rho), m * float(T.circle_length(rho)))]
        pieces.append(T.return_burn(T.Manoeuvre(pieces).end()))
        g = math.cosh(rho)
        info.update(reference=m * 2 * math.pi * (g - 1),
                    ref_how=f"Томас: 2π(γ − 1) за оборот, γ = {g:.6g}, оборотов {m} (= площадь круга скоростей)")
    elif kind == "circle":
        pieces = [T.Turn(tuple(e1), tuple(n), 1.0 / math.tanh(rho), m * float(T.circle_length(rho)))]
        info.update(reference=m * float(T.circle_area(rho)),
                    ref_how=f"Гаусс–Бонне: площадь круга радиуса ρ = {rho:g}, 2π(ch ρ − 1), × {m}")
    elif kind == "triangle":
        alpha = math.radians(float(p["alpha"]))
        u = math.tanh(rho) * e1
        w = LZ.add_velocities(u, math.tanh(rho) * (math.cos(alpha) * e1 + math.sin(alpha) * e2))
        pieces = T.polygon_burns(repeated([u, w], m))
        z = np.zeros(3)
        A = float(T.triangle_area(T.distance(z, u), T.distance(u, w), T.distance(w, z)))
        info.update(reference=m * A, ref_how=f"площадь треугольника по сторонам (формула Люилье), × {m}",
                    vertices=[u.tolist(), w.tolist()])
    elif kind == "polygon":
        k = int(p["sides"])
        verts = [_on_sphere(rho, e1, -math.cos(2 * math.pi * j / k) * e1 - math.sin(2 * math.pi * j / k) * e2, rho)
                 for j in range(1, k)]
        pieces = T.polygon_burns(repeated(verts, m))
        info.update(reference=m * T.regular_polygon_area(k, rho),
                    ref_how=f"правильный {k}-угольник, радиус описанной окружности ρ = {rho:g}: (n − 2)π − n·α, × {m}",
                    vertices=[np.asarray(v).tolist() for v in verts])
    elif kind == "crown":
        k = int(p["sides"])
        verts = []
        for j in range(1, k):
            ph, lift = 2 * math.pi * j / k, chi * (-1) ** j
            d = math.cos(lift) * (-math.cos(ph) * e1 - math.sin(ph) * e2) + math.sin(lift) * n
            verts.append(_on_sphere(rho, e1, d, rho))
        pieces = T.polygon_burns(repeated(verts, m))
        info.update(loop_pieces=len(verts) + 1)
        info.update(reference=None, ref_how="неплоская петля: замкнутой формулы нет; проверка — два представления "
                                            "(группа Лоренца и SL(2, C))", vertices=[v.tolist() for v in verts])
    elif kind == "helix":
        w = math.cos(chi) * n + math.sin(chi) * e1
        pieces = [T.Turn(tuple(e1), tuple(w), 1.0 / math.tanh(rho), m * float(T.circle_length(rho)))]
        check_reach(pieces)
        pieces.append(T.return_burn(T.Manoeuvre(pieces).end()))
        info.update(reference=None, ref_how="винт (ось поворота тяги наклонена на χ): замкнутой формулы нет; при χ = 0 "
                                            "это круг через покой")
    elif kind == "seam":
        verts = seam_vertices(rho, chi, e1, e2, n, SEAM_BURNS)
        pieces = T.polygon_burns(repeated(verts, m))
        info.update(loop_pieces=len(verts) + 1)
        info.update(reference=None, ref_how=f"шов из {SEAM_BURNS} импульсов (гладкий шов — их предел; разница с "
                                            f"{2 * SEAM_BURNS} — в проверке); замкнутой формулы нет")
    else:
        raise ValueError(f"неизвестная петля {kind!r}")
    check_reach(pieces)
    return pieces, info


def seam_vertices(rho, chi, e1, e2, n, N):
    """The seam of a tennis ball on the sphere of radius rho about c = tanh(rho) e1 (which passes through rest): in
    c's frame the direction d(t) = cos(lat) (-cos t e1 - sin t e2) + sin(lat) n, lat = chi sin(2t) (at t = 0 towards
    rest; run anticlockwise about n like the other loops); chi = 0 gives a circle of radius rho through rest. Vertices
    at t = 2 pi j / N, j = 1 .. N-1."""
    out = []
    for j in range(1, N):
        t = 2 * math.pi * j / N
        lat = chi * math.sin(2 * t)
        d = math.cos(lat) * (-math.cos(t) * e1 - math.sin(t) * e2) + math.sin(lat) * n
        out.append(_on_sphere(rho, e1, d, rho))
    return out


# --- the field of three-burn loops rest -> u -> w -> rest ------------------------------------------------------------

def triangle_field(u, W, chunk: int = 40000):
    """For the loop rest -> u -> w -> rest at every lab velocity w of W (..., 3): the gyroscopes' rotation angle theta
    (the Thomas-Wigner angle of the two boosts u and v' = w seen from u, by the engine's Lorentz matrices), the rotation
    vector of the gyroscopes (axis times angle; the loop's normal, opposite to the sense of the loop), and the fuel L
    (the sum of the three burns' rapidities). NaN where |w| > FIELD_BETA_MAX."""
    W = np.asarray(W, float)
    shp = W.shape[:-1]
    Wf = W.reshape(-1, 3)
    th = np.full(len(Wf), np.nan)
    rv = np.full((len(Wf), 3), np.nan)
    L = np.full(len(Wf), np.nan)
    ok = np.linalg.norm(Wf, axis=1) <= FIELD_BETA_MAX
    idx = np.nonzero(ok)[0]
    u = np.asarray(u, float)
    eta_u = math.atanh(float(np.linalg.norm(u)))
    for a in range(0, len(idx), chunk):
        I = idx[a:a + chunk]
        w = Wf[I]
        vp = LZ.relative_velocity(np.broadcast_to(u, w.shape), w)
        _, _, nax, t = LZ.wigner_rotation(np.broadcast_to(u, w.shape), vp)
        th[I] = t
        rv[I] = -nax * t[:, None]  # the gyroscopes turn by R^T: about -n by theta
        L[I] = eta_u + np.arcsinh(np.linalg.norm(vp, axis=1) * LZ.gamma_of(vp)) + \
            np.arcsinh(np.linalg.norm(w, axis=1) * LZ.gamma_of(w))
    return th.reshape(shp), rv.reshape(shp + (3,)), L.reshape(shp)


def triangle_reference(u, w):
    """The same angle by Gauss-Bonnet: the area of the geodesic triangle (rest, u, w) from its sides (L'Huilier)."""
    z = np.zeros(3)
    return float(T.triangle_area(T.distance(z, u), T.distance(u, w), T.distance(w, z)))


def field_tolerance(u, w):
    """Round-off of the matrix route: products of a few matrices with entries up to gamma: 64 eps gamma_u^2 gamma_w^2
    (a bound with margin; measured in the tests)."""
    gu = float(LZ.gamma_of(u))
    gw = float(LZ.gamma_of(w))
    return 64 * np.finfo(float).eps * (gu * gw) ** 2


def field_values(kind: str, th, L):
    """The field drawn: 'theta' -> theta / pi; 'ratio' -> theta over the planar isoperimetric bound at the same fuel."""
    if kind == "theta":
        return th / math.pi
    return th / T.isoperimetric_bound(L)
