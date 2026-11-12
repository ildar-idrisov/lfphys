# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Bodies of the FDTD solver (``lfphys.core.em.fdtd``): shapes in 2-D and 3-D and how a Yee node takes their material.

Shapes (coordinates in the solver's length unit; 2-D shapes use (x, y)): ``Sphere`` (3-D), ``Cylinder`` (a disk in
2-D; in 3-D a circular cylinder along x, y or z, finite or infinite), ``Box`` (axis-aligned), ``HalfSpace`` (a point
and the outward normal), ``Polygon`` (2-D; in 3-D a prism along z between ``zmin`` and ``zmax``), ``Mask`` (a
callable inside(x, y[, z]) -> bool; staircase only). Every shape gives ``inside`` and, except ``Mask``, a signed
distance with the outward unit normal of the nearest surface point (``sdf``; exact for the sphere, the disk and
cylinder side, the half-space, the box and the polygon edges; the box and the finite cylinder near edges and corners
take the normal of the nearest face).

**How a node takes a material.** Every field component lives on its own Yee node; a node's material is read at the
node itself:

* ``staircase``: the node takes the material of the last body containing it (the body's ``inside`` at the node).
  The surface is then resolved to within half a cell, so the error of a curved surface is first order in the cell
  size (it is second order for a plane surface lying half-way between nodes).
* ``subpixel`` (the default for non-dispersive, non-conducting dielectric and magnetic bodies): within half a cell
  diagonal of the surface the node takes the averaged permittivity of the cell of size dx^D centred on it, from the
  fill fraction f of the body in that cell and the surface normal n. Farjadpour et al. 2006 (Opt. Lett. 31, 2972,
  eq. (1)) average the inverse tensor eps_eff^-1 = P <eps^-1> + (1 - P) <eps>^-1, P = n n^T, and obtain the
  off-diagonal terms through D averaged from the adjacent Yee points; the solver keeps only the diagonal element of
  the component's own axis: 1/eps_aa = n_a^2 <1/eps> + (1 - n_a^2) / <eps>, with <eps> = f eps_body + (1 - f)
  eps_before (eps_before: what the node had before this body). This is the scheme Farjadpour et al. call VP-EP ("the
  VP-EP scheme, which is exactly the diagonal part of Eq. (1) for s = 1"), which they class among the schemes that
  "do not satisfy the perturbation criterion for diagonal interfaces" and "are therefore expected to have only linear
  convergence in general" (review B8-fdtd F6; the earlier statement "between first and second order" was wrong [error
  in earlier]). Measured: exact (second order) for a plane surface along the grid axes and for E along a cylinder's
  axis (TM, where the diagonal is the full tensor: m = 1.5, error ratios 3.3-4.0 per halving); for E in the plane of a
  curved surface first order in general (TE cylinder eps = 6, a = 0.5, f = 0.5: Q_sca +2.6, +1.4, +0.8 % at 40, 80,
  160 cells per unit) and not monotone at weak contrast (TE m = 1.5, f = 0.4: -0.02, -0.12, -0.09 %). Kottke,
  Farjadpour & Johnson 2008 (Phys. Rev. E 77, 036611) give the justification and the anisotropic case. mu is averaged
  the same way on the H nodes. The full tensor is not implemented (the solver's update is diagonal; STATUS).
  The fill fraction is that of the cell cut by the tangent plane at the nearest surface point (exact volume of a
  cube or square cut by a plane: the corner sum below), so it carries the surface's curvature error O(dx^2 / R).
* PEC, conducting and dispersive bodies are always staircase (an averaged dispersion or conductivity has no unique
  definition; stated where they are used).
"""

from __future__ import annotations

import math

import numpy as np

ABOUT = {
    "layer": "core", "kind": "numerics",
    "title": "FDTD: тела и как узел сетки Йи получает их вещество",
    "statement": "Формы (шар, цилиндр/диск, параллелепипед, полупространство, многоугольник/призма, маска) со знаковым "
                 "расстоянием и нормалью; узел получает вещество ступенькой (по своей точке) или усреднением по "
                 "ячейке (диагональ тензора Фарджадпура и др. — по их классификации схема VP-EP — с долей заполнения "
                 "по касательной плоскости).",
    "validity": "ступенька — 1-й порядок по размеру ячейки для кривых границ (2-й для плоской границы между узлами); "
                "усреднение — 2-й порядок для плоских границ вдоль осей и для E вдоль оси цилиндра (TM), для E в "
                "плоскости кривой границы в общем случае 1-й порядок (внедиагональные элементы тензора отброшены: "
                "TE-цилиндр ε = 6 — 2.6, 1.4, 0.8 % при 40, 80, 160 ячейках на единицу) и при малом контрасте "
                "немонотонно; проводники, PEC и диспергирующие тела — всегда ступенькой",
    "basis": ["Farjadpour et al., Opt. Lett. 31, 2972 (2006), ур. (1) — анизотропное усреднение по подъячейкам; "
              "его диагональ — схема VP-EP, по их оценке линейной сходимости в общем случае",
              "Kottke, Farjadpour, Johnson, Phys. Rev. E 77, 036611 (2008) — обоснование, анизотропный случай",
              "объём куба, отсечённого плоскостью: сумма по вершинам (свёртка равномерных распределений)"],
    "conflicts": [],
}


# --- shapes -------------------------------------------------------------------------------------------------------
class Shape:
    """A region of space. ``dims``: 2, 3 or None (both)."""
    kind = "shape"
    dims = None
    analytic = True  # has a signed distance (sub-pixel averaging possible)

    def inside(self, P) -> np.ndarray:
        """P: tuple of coordinate arrays (x, y) or (x, y, z), broadcastable; True inside (boundary included)."""
        d, _ = self.sdf(P)
        return d <= 0.0

    def sdf(self, P):
        """(signed distance, outward unit normal as a tuple of arrays) at the points P; negative inside."""
        raise NotImplementedError

    def bbox(self, dim: int):
        """(lo, hi) per axis (may be infinite)."""
        raise NotImplementedError

    def params(self) -> dict:
        raise NotImplementedError

    def _check(self, dim: int):
        if self.dims is not None and dim != self.dims:
            raise ValueError(f"форма {self.kind} задана для {self.dims}-D, а мир {dim}-D")


def _as_vec(v, n=None):
    a = tuple(float(x) for x in v)
    if n is not None and len(a) != n:
        raise ValueError(f"нужно {n} координат, дано {len(a)}")
    return a


class Sphere(Shape):
    kind = "sphere"
    dims = 3

    def __init__(self, center, radius: float):
        self.center, self.radius = _as_vec(center, 3), float(radius)
        if not self.radius > 0:
            raise ValueError("радиус шара > 0")

    def sdf(self, P):
        dx, dy, dz = (P[0] - self.center[0], P[1] - self.center[1], P[2] - self.center[2])
        r = np.sqrt(dx * dx + dy * dy + dz * dz)
        rs = np.where(r > 0, r, 1.0)
        return r - self.radius, (np.where(r > 0, dx / rs, 1.0), np.where(r > 0, dy / rs, 0.0),
                                 np.where(r > 0, dz / rs, 0.0))

    def bbox(self, dim):
        return [(c - self.radius, c + self.radius) for c in self.center]

    def params(self):
        return {"kind": self.kind, "center": list(self.center), "radius": self.radius}


class Cylinder(Shape):
    """A disk in 2-D (``center`` (x, y)); in 3-D a circular cylinder with its axis along ``axis`` through ``center``
    (x, y, z), of ``height`` (None: infinite) centred on the centre's coordinate along the axis."""
    kind = "cylinder"

    def __init__(self, center, radius: float, axis: str = "z", height: float | None = None):
        self.center, self.radius = _as_vec(center), float(radius)
        if len(self.center) not in (2, 3):
            raise ValueError("центр цилиндра: (x, y) или (x, y, z)")
        if not self.radius > 0:
            raise ValueError("радиус цилиндра > 0")
        if axis not in ("x", "y", "z"):
            raise ValueError("ось цилиндра: x, y или z")
        self.axis = axis
        self.height = None if height is None else float(height)
        if self.height is not None and not self.height > 0:
            raise ValueError("высота цилиндра > 0 (или None — бесконечный)")
        self.dims = len(self.center)
        if self.dims == 2 and (axis != "z" or self.height is not None):
            raise ValueError("в 2-D цилиндр — это диск (ось z, без высоты)")

    def sdf(self, P):
        if self.dims == 2:
            dx, dy = P[0] - self.center[0], P[1] - self.center[1]
            r = np.sqrt(dx * dx + dy * dy)
            rs = np.where(r > 0, r, 1.0)
            return r - self.radius, (np.where(r > 0, dx / rs, 1.0), np.where(r > 0, dy / rs, 0.0))
        a = "xyz".index(self.axis)
        u, v = [k for k in range(3) if k != a]
        du, dv = P[u] - self.center[u], P[v] - self.center[v]
        r = np.sqrt(du * du + dv * dv)
        rs = np.where(r > 0, r, 1.0)
        d_side = r - self.radius
        n = [None, None, None]
        n[u] = np.where(r > 0, du / rs, 1.0) + 0.0 * P[a]
        n[v] = np.where(r > 0, dv / rs, 0.0) + 0.0 * P[a]
        n[a] = 0.0 * (du + dv + P[a])
        if self.height is None:
            return d_side + 0.0 * P[a], tuple(np.broadcast_arrays(*n))
        za = P[a] - self.center[a]
        d_cap = np.abs(za) - self.height / 2
        # outside both: distance to the rim; otherwise the larger of the two (exact inside and off the rim)
        out = (d_side > 0) & (d_cap > 0)
        d = np.where(out, np.sqrt(np.maximum(d_side, 0) ** 2 + np.maximum(d_cap, 0) ** 2), np.maximum(d_side, d_cap))
        cap = d_cap > d_side
        nn = [np.where(cap, 0.0, n[k]) for k in range(3)]
        nn[a] = np.where(cap, np.sign(za) + (za == 0), 0.0)
        return d, tuple(np.broadcast_arrays(*nn))

    def bbox(self, dim):
        if self.dims == 2:
            return [(self.center[k] - self.radius, self.center[k] + self.radius) for k in range(2)]
        a = "xyz".index(self.axis)
        out = []
        for k in range(3):
            if k == a:
                out.append((-math.inf, math.inf) if self.height is None else
                           (self.center[k] - self.height / 2, self.center[k] + self.height / 2))
            else:
                out.append((self.center[k] - self.radius, self.center[k] + self.radius))
        return out

    def params(self):
        return {"kind": self.kind, "center": list(self.center), "radius": self.radius, "axis": self.axis,
                "height": self.height}


class Box(Shape):
    """Axis-aligned box between corners ``lo`` and ``hi`` (2 or 3 coordinates; +-inf allowed)."""
    kind = "box"

    def __init__(self, lo, hi):
        self.lo, self.hi = _as_vec(lo), _as_vec(hi)
        if len(self.lo) != len(self.hi) or len(self.lo) not in (2, 3):
            raise ValueError("углы параллелепипеда: по 2 или 3 координаты")
        if any(not h > l for l, h in zip(self.lo, self.hi)):
            raise ValueError("параллелепипед: hi > lo по каждой оси")
        self.dims = len(self.lo)

    def sdf(self, P):
        D = len(self.lo)
        c = [(l + h) / 2 if math.isfinite(l + h) else (l if math.isfinite(l) else (h if math.isfinite(h) else 0.0))
             for l, h in zip(self.lo, self.hi)]
        # per axis: distance outside the slab (positive) or minus the depth inside
        q = []
        for k in range(D):
            lo, hi = self.lo[k], self.hi[k]
            dl = lo - P[k] if math.isfinite(lo) else -np.inf + 0 * P[k]
            dh = P[k] - hi if math.isfinite(hi) else -np.inf + 0 * P[k]
            q.append(np.maximum(dl, dh))
        q = np.broadcast_arrays(*q)
        outside = sum(np.maximum(qq, 0.0) ** 2 for qq in q)
        dmax = np.max(np.stack(q), axis=0)
        d = np.where(dmax > 0, np.sqrt(outside), dmax)
        arg = np.argmax(np.stack(q), axis=0)
        n = []
        for k in range(D):
            lo, hi = self.lo[k], self.hi[k]
            side = np.where(P[k] >= c[k], 1.0, -1.0) if (math.isfinite(lo) and math.isfinite(hi)) else (
                np.ones_like(P[k], dtype=float) if math.isfinite(hi) else -np.ones_like(P[k], dtype=float))
            n.append(np.where(arg == k, side, 0.0))
        return d, tuple(np.broadcast_arrays(*n))

    def inside(self, P):
        m = True
        for k in range(len(self.lo)):
            m = m & (P[k] >= self.lo[k]) & (P[k] <= self.hi[k])
        return m

    def bbox(self, dim):
        return list(zip(self.lo, self.hi))

    def params(self):
        return {"kind": self.kind, "lo": list(self.lo), "hi": list(self.hi)}


class HalfSpace(Shape):
    """{r : (r - point) . normal <= 0}: ``normal`` points out of the body."""
    kind = "halfspace"

    def __init__(self, point, normal):
        self.point = _as_vec(point)
        n = np.array(_as_vec(normal, len(self.point)))
        if not np.linalg.norm(n) > 0:
            raise ValueError("нормаль полупространства ненулевая")
        self.normal = tuple(float(v) for v in n / np.linalg.norm(n))
        self.dims = len(self.point)

    def sdf(self, P):
        d = sum((P[k] - self.point[k]) * self.normal[k] for k in range(len(self.point)))
        return d, tuple(np.broadcast_arrays(*[self.normal[k] + 0.0 * d for k in range(len(self.point))]))

    def bbox(self, dim):
        out = []
        for k in range(len(self.point)):
            others = any(abs(self.normal[j]) > 0 for j in range(len(self.point)) if j != k)
            if others or self.normal[k] == 0:
                out.append((-math.inf, math.inf))
            elif self.normal[k] > 0:
                out.append((-math.inf, self.point[k]))
            else:
                out.append((self.point[k], math.inf))
        return out

    def params(self):
        return {"kind": self.kind, "point": list(self.point), "normal": list(self.normal)}


class Polygon(Shape):
    """A simple polygon (vertices (x, y) in order) in 2-D; in 3-D the prism between ``zmin`` and ``zmax``."""
    kind = "polygon"

    def __init__(self, points, zmin: float | None = None, zmax: float | None = None):
        p = np.array(points, float)
        if p.ndim != 2 or p.shape[1] != 2 or len(p) < 3:
            raise ValueError("многоугольник: не меньше трёх вершин (x, y)")
        self.points = p
        self.zmin = None if zmin is None else float(zmin)
        self.zmax = None if zmax is None else float(zmax)
        self.dims = 2 if zmin is None and zmax is None else 3
        if self.dims == 3 and not (self.zmax is not None and self.zmin is not None and self.zmax > self.zmin):
            raise ValueError("призма: zmin < zmax")

    def _sdf2(self, X, Y):
        p = self.points
        q = np.roll(p, -1, axis=0)
        d2 = np.full(np.broadcast(X, Y).shape, np.inf)
        nx = np.zeros(d2.shape)
        ny = np.zeros(d2.shape)
        wn = np.zeros(d2.shape, bool)
        for (ax, ay), (bx, by) in zip(p, q):
            ex, ey = bx - ax, by - ay
            L2 = ex * ex + ey * ey
            t = np.clip(((X - ax) * ex + (Y - ay) * ey) / L2, 0.0, 1.0)
            cx, cy = X - (ax + t * ex), Y - (ay + t * ey)
            dd = cx * cx + cy * cy
            better = dd < d2
            r = np.sqrt(np.maximum(dd, 1e-300))
            nx = np.where(better, cx / r, nx)
            ny = np.where(better, cy / r, ny)
            d2 = np.where(better, dd, d2)
            cond = (ay > Y) != (by > Y)
            xint = ax + (Y - ay) * ex / np.where(ey == 0, 1.0, ey)
            wn ^= cond & (X < xint)
        d = np.sqrt(d2)
        sgn = np.where(wn, -1.0, 1.0)
        # the normal points from the surface to the point outside, so inside it is reversed
        return sgn * d, sgn * nx, sgn * ny

    def sdf(self, P):
        X, Y = np.broadcast_arrays(P[0], P[1])
        d, nx, ny = self._sdf2(X, Y)
        if self.dims == 2:
            return d, (nx, ny)
        Z = P[2]
        dz = np.maximum(self.zmin - Z, Z - self.zmax)
        out = (d > 0) & (dz > 0)
        dd = np.where(out, np.sqrt(np.maximum(d, 0) ** 2 + np.maximum(dz, 0) ** 2), np.maximum(d, dz))
        cap = dz > d
        zc = (self.zmin + self.zmax) / 2
        return dd, tuple(np.broadcast_arrays(np.where(cap, 0.0, nx), np.where(cap, 0.0, ny),
                                             np.where(cap, np.where(Z >= zc, 1.0, -1.0), 0.0)))

    def bbox(self, dim):
        b = [(float(self.points[:, 0].min()), float(self.points[:, 0].max())),
             (float(self.points[:, 1].min()), float(self.points[:, 1].max()))]
        if self.dims == 3:
            b.append((self.zmin, self.zmax))
        return b

    def params(self):
        return {"kind": self.kind, "points": self.points.tolist(), "zmin": self.zmin, "zmax": self.zmax}


class Mask(Shape):
    """A region given by a function inside(x, y[, z]) -> bool array (staircase only), or by a boolean array sampled
    on a uniform grid (``array`` with its ``lo`` and ``hi`` corners: nearest sample)."""
    kind = "mask"
    analytic = False

    def __init__(self, inside=None, array=None, lo=None, hi=None, dims: int | None = None):
        if (inside is None) == (array is None):
            raise ValueError("маска: функция inside или массив array (одно из двух)")
        self.fn = inside
        self.array = None if array is None else np.asarray(array, bool)
        self.lo = None if lo is None else _as_vec(lo)
        self.hi = None if hi is None else _as_vec(hi)
        if self.array is not None:
            if self.lo is None or self.hi is None or len(self.lo) != self.array.ndim:
                raise ValueError("маска-массив: нужны углы lo и hi по числу осей массива")
            self.dims = self.array.ndim
        else:
            self.dims = dims

    def inside(self, P):
        if self.fn is not None:
            return np.asarray(self.fn(*P), bool)
        idx = []
        for k in range(self.array.ndim):
            n = self.array.shape[k]
            u = (P[k] - self.lo[k]) / (self.hi[k] - self.lo[k]) * n
            idx.append(np.clip(np.floor(u).astype(int), 0, n - 1))
        inb = True
        for k in range(self.array.ndim):
            inb = inb & (P[k] >= self.lo[k]) & (P[k] < self.hi[k])
        return inb & self.array[tuple(np.broadcast_arrays(*idx))]

    def sdf(self, P):
        raise ValueError("маска не задаёт расстояние до поверхности: только ступенька")

    def bbox(self, dim):
        if self.array is not None:
            return list(zip(self.lo, self.hi))
        return [(-math.inf, math.inf)] * dim

    def params(self):
        if self.fn is not None:
            raise ValueError("маска-функция не сохраняется в состоянии: задайте маску массивом (array, lo, hi)")
        return {"kind": self.kind, "array": self.array.tolist(), "lo": list(self.lo), "hi": list(self.hi)}


def shape_from_params(d: dict) -> Shape:
    k = d["kind"]
    if k == "sphere":
        return Sphere(d["center"], d["radius"])
    if k == "cylinder":
        return Cylinder(d["center"], d["radius"], d.get("axis", "z"), d.get("height"))
    if k == "box":
        return Box(d["lo"], d["hi"])
    if k == "halfspace":
        return HalfSpace(d["point"], d["normal"])
    if k == "polygon":
        return Polygon(d["points"], d.get("zmin"), d.get("zmax"))
    if k == "mask":
        return Mask(array=np.array(d["array"], bool), lo=d["lo"], hi=d["hi"])
    raise ValueError(f"неизвестная форма {k!r}")


# --- fill fraction of a cell cut by a plane ---------------------------------------------------------------------------
_SMALL = 1e-4  # normal components below this are folded (error O(m^2) < 1e-8 of the cell)


def _corner_volume(m, t):
    """Volume of {v in [0,1]^D : m . v <= t} for m_i > 0 (arrays (..., D)), by the corner sum
    (1 / (D! prod m)) sum_v (-1)^|v| max(0, t - m.v)^D (the CDF of a sum of uniform variables)."""
    D = m.shape[-1]
    tot = np.zeros(t.shape)
    for bits in range(1 << D):
        s = np.zeros(t.shape)
        sign = 1.0
        for k in range(D):
            if bits >> k & 1:
                s = s + m[..., k]
                sign = -sign
        tot = tot + sign * np.maximum(t - s, 0.0) ** D
    return tot / (math.factorial(D) * np.prod(m, axis=-1))


def cut_fraction(normal, offset):
    """Fraction of the unit cell [-1/2, 1/2]^D on the side n . u <= offset of a plane through it (n a unit normal,
    arrays (..., D); offset (...) in cell units). Exact (corner sum), with normal components below 1e-4 folded into
    a shift of the plane (error below 1e-8)."""
    m = np.abs(np.asarray(normal, float))
    t = np.asarray(offset, float) + 0.5 * m.sum(axis=-1)
    m = np.sort(m, axis=-1)[..., ::-1]  # descending; the largest >= 1/sqrt(D)
    D = m.shape[-1]
    out = np.empty(t.shape)
    # how many components are significant
    nsig = (m >= _SMALL).sum(axis=-1)
    for k in range(1, D + 1):
        sel = nsig == k
        if not np.any(sel):
            continue
        mk = m[sel][..., :k]
        tk = t[sel] - 0.5 * m[sel][..., k:].sum(axis=-1)  # folded components: the plane shifted by their mean
        out[sel] = _corner_volume(mk, tk)
    return np.clip(out, 0.0, 1.0)
