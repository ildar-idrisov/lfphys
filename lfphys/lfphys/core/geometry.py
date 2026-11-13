# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Geometry of computations in 2-D and 3-D (plan P10; owner, 2026-10-24).

* ``Plane`` — an oriented plane in 3-D: an origin and orthonormal in-plane axes u, v (normal n = u x v). Presets
  "xy", "xz", "yz" (with an offset along the normal) or any normal. A 2-D model is computed in the plane's
  coordinates (a, b) and placed in 3-D by ``to3d`` / read back by ``to2d``; vectors (velocities, fields) likewise.
  The choice of plane does not change a 2-D model's physics, only where it sits in 3-D.
* ``Grid`` — a uniform Cartesian grid in 1, 2 or 3 dimensions (node coordinates per axis).
* ``slice_field`` — the values of a 3-D field on a plane: exact (no interpolation) for a coordinate plane through grid
  nodes; otherwise trilinear interpolation, whose error is at most (h_x^2 |f_xx| + h_y^2 |f_yy| + h_z^2 |f_zz|)/8 for
  a smooth field (exact for fields linear in each coordinate).
* ``Modelling`` — how a 3-D world is modelled (owner, 2026-10-24): **full 3-D** (the whole volume; any plane can be
  explored afterwards) or **chosen slices** (only one or several given planes are computed, for speed; only those can
  be explored). The model states whether its slices are exact (e.g. the angular spectrum gives the exact field on
  any coordinate plane; a field invariant along an axis reduces exactly to 2-D) or an approximation (a reduced 2-D
  model of a 3-D problem without that symmetry); an approximation is flagged everywhere it is shown.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from lfphys.i18n import T, join
from lfphys.codes import coded

ABOUT = {
    "layer": "core", "kind": "numerics",
    "title": T("Geometry of computations: 2-D and 3-D, planes and slices"),
    "statement": T("A plane in space (xy, xz, yz or any normal) for two-dimensional models; the slice of a "
                   "three-dimensional field by a plane; the modes of three-dimensional modelling: the whole volume or "
                   "only the given slices (flagged when a slice is an approximation)."),
    "validity": T("exact linear algebra; a slice along a coordinate plane through the nodes is exact, otherwise "
                  "trilinear interpolation with an error ≤ Σ h²·|∂²f|/8"),
    "basis": [T("linear algebra; trilinear interpolation (the error bound: the remainder term of Lagrange "
                "interpolation)")],
    "conflicts": [],
}

_PRESETS = {
    "xy": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    "xz": ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    "yz": ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
}


@dataclass(frozen=True)
class Plane:
    """origin + a u + b v; u, v orthonormal; normal = u x v."""
    origin: tuple = (0.0, 0.0, 0.0)
    u: tuple = (1.0, 0.0, 0.0)
    v: tuple = (0.0, 1.0, 0.0)
    name: str = ""  # "xy", "xz", "yz" when the axes are a preset's, otherwise "custom" (review B1-16)

    def __post_init__(self):
        u, v = np.asarray(self.u, float), np.asarray(self.v, float)
        if abs(np.linalg.norm(u) - 1) > 1e-12 or abs(np.linalg.norm(v) - 1) > 1e-12 or abs(u @ v) > 1e-12:
            raise ValueError("Plane: u and v must be orthonormal")
        if not self.name:
            name = next((nm for nm, (pu, pv) in _PRESETS.items()
                         if np.allclose(u, pu, atol=1e-12) and np.allclose(v, pv, atol=1e-12)), "custom")
            object.__setattr__(self, "name", name)

    @classmethod
    def preset(cls, name: str, offset: float = 0.0) -> "Plane":
        """"xy" (at z = offset), "xz" (at y = offset) or "yz" (at x = offset). The offset is along the positive
        coordinate axis missing from the name (the normal u x v of "xz" points along -y)."""
        if name not in _PRESETS:
            raise ValueError(f"Plane.preset: one of {sorted(_PRESETS)}")
        u, v = _PRESETS[name]
        axis = {"xy": (0.0, 0.0, 1.0), "xz": (0.0, 1.0, 0.0), "yz": (1.0, 0.0, 0.0)}[name]
        return cls(tuple(float(offset * a) for a in axis), u, v, name)

    @classmethod
    def horizontal(cls, normal, origin=(0.0, 0.0, 0.0)) -> "Plane":
        """The plane through ``origin`` with unit normal along ``normal`` and in-plane axes fixed by the depth axis z
        (the slices of a 3-D field behind a source in z = 0): u horizontal (u_z = 0), v with v_z >= 0, u x v = n.
        u = z x n normalised (x for a transverse plane), signs chosen so that v points to larger depth."""
        n = np.asarray(normal, float)
        if np.linalg.norm(n) == 0:
            raise coded(ValueError(T("a plane needs a non-zero normal")), "geometry.zero_normal")
        n = n / np.linalg.norm(n)
        h = np.cross((0.0, 0.0, 1.0), n)
        if np.linalg.norm(h) < 1e-12:  # transverse plane: u = x, v = n x u (y for n = +z)
            h = np.array([1.0, 0.0, 0.0])
        h = h / np.linalg.norm(h)
        v = np.cross(n, h)
        if v[2] < -1e-12 or (abs(v[2]) <= 1e-12 and v[1] < 0 and abs(n[2]) < 1 - 1e-12):
            h, v = -h, -v
        h[2] = 0.0
        return cls(tuple(float(x) for x in np.asarray(origin, float)), tuple(float(x) for x in h),
                   tuple(float(x) for x in v))

    @classmethod
    def from_normal(cls, normal, origin=(0.0, 0.0, 0.0), u_hint=(1.0, 0.0, 0.0)) -> "Plane":
        """The plane through ``origin`` with unit normal along ``normal``; u is ``u_hint`` projected into the plane
        (another axis if u_hint is along the normal), v = n x u."""
        n = np.asarray(normal, float)
        if np.linalg.norm(n) == 0:
            raise coded(ValueError(T("a plane needs a non-zero normal")), "geometry.zero_normal")
        n = n / np.linalg.norm(n)
        h = np.asarray(u_hint, float)
        u = h - (h @ n) * n
        if np.linalg.norm(u) < 1e-9:
            for alt in ((1.0, 0, 0), (0, 1.0, 0), (0, 0, 1.0)):
                u = np.asarray(alt) - (np.asarray(alt) @ n) * n
                if np.linalg.norm(u) > 1e-3:
                    break
        u = u / np.linalg.norm(u)
        v = np.cross(n, u)
        return cls(tuple(float(x) for x in np.asarray(origin, float)), tuple(float(x) for x in u),
                   tuple(float(x) for x in v), "custom")

    @property
    def normal(self) -> np.ndarray:
        return np.cross(np.asarray(self.u), np.asarray(self.v))

    @property
    def rotation(self) -> np.ndarray:
        """3x3 matrix with rows u, v, n: world vector -> (along u, along v, along n)."""
        return np.vstack([self.u, self.v, self.normal])

    def to3d(self, a, b) -> np.ndarray:
        """Points with in-plane coordinates (a, b) -> world coordinates, shape (..., 3)."""
        a, b = np.broadcast_arrays(np.asarray(a, float), np.asarray(b, float))
        return (np.asarray(self.origin) + a[..., None] * np.asarray(self.u) + b[..., None] * np.asarray(self.v))

    def to2d(self, p) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """World points (..., 3) -> (a, b, signed distance from the plane)."""
        d = np.asarray(p, float) - np.asarray(self.origin)
        return d @ np.asarray(self.u), d @ np.asarray(self.v), d @ self.normal

    def vec_to3d(self, va, vb) -> np.ndarray:
        va, vb = np.broadcast_arrays(np.asarray(va, float), np.asarray(vb, float))
        return va[..., None] * np.asarray(self.u) + vb[..., None] * np.asarray(self.v)

    def vec_to2d(self, w) -> tuple[np.ndarray, np.ndarray]:
        w = np.asarray(w, float)
        return w @ np.asarray(self.u), w @ np.asarray(self.v)

    def same_as(self, other: "Plane", tol: float = 1e-9) -> bool:
        """The same set of points (orientation of u, v within the plane may differ)."""
        n1, n2 = self.normal, other.normal
        if np.linalg.norm(np.cross(n1, n2)) > tol:
            return False
        return abs((np.asarray(other.origin) - np.asarray(self.origin)) @ n1) <= tol

    def as_dict(self) -> dict:
        return {"name": self.name, "origin": list(self.origin), "u": list(self.u), "v": list(self.v),
                "normal": [float(x) for x in self.normal]}

    @classmethod
    def from_dict(cls, d: dict) -> "Plane":
        return cls(tuple(d["origin"]), tuple(d["u"]), tuple(d["v"]), d.get("name", "custom"))


@dataclass(frozen=True)
class Grid:
    """A uniform Cartesian grid; ``axes`` are the node coordinates along x (and y, z)."""
    axes: tuple

    @classmethod
    def uniform(cls, n, L) -> "Grid":
        """n nodes (int or per axis) with spacing d = L/n at x_i = (i - n//2) d (L scalar or per axis): the convention
        of the FFT-based kernels (``lfphys.core.optics.angular_spectrum``), for odd and even n (review B1-3)."""
        n = np.atleast_1d(n).astype(int)
        L = np.broadcast_to(np.atleast_1d(np.asarray(L, float)), n.shape)
        return cls(tuple((np.arange(ni) - ni // 2) * (li / ni) for ni, li in zip(n, L)))

    @property
    def ndim(self) -> int:
        return len(self.axes)

    @property
    def shape(self) -> tuple:
        return tuple(len(a) for a in self.axes)

    @property
    def spacing(self) -> tuple:
        return tuple(float(a[1] - a[0]) if len(a) > 1 else 0.0 for a in self.axes)

    def mesh(self):
        return np.meshgrid(*self.axes, indexing="ij")


def slice_field(field3, grid: Grid, plane: Plane, a, b, fill=np.nan) -> tuple[np.ndarray, bool]:
    """Values of a 3-D field (indexed [ix, iy, iz] on ``grid``) on the plane points (a, b) (1-D arrays: the result has
    shape (len(a), len(b))). Returns (values, exact): exact when the plane is a coordinate plane through grid nodes and
    the in-plane points are grid nodes; otherwise trilinear interpolation. Points outside the grid get ``fill``."""
    if grid.ndim != 3:
        raise ValueError("slice_field: a 3-D grid")
    if min(grid.shape) < 2:
        raise ValueError("slice_field: at least two nodes per axis")
    A, B = np.meshgrid(np.asarray(a, float), np.asarray(b, float), indexing="ij")
    P = plane.to3d(A, B)
    idx = []
    exact = True
    for d in range(3):
        ax = grid.axes[d]
        h = ax[1] - ax[0]
        t = (P[..., d] - ax[0]) / h
        ti = np.rint(t)
        if np.max(np.abs(t - ti)) > 1e-9:
            exact = False
        idx.append(t)
    shape = grid.shape
    out = np.full(A.shape, fill, dtype=np.result_type(field3, float))
    inside = np.ones(A.shape, bool)
    for d in range(3):
        inside &= (idx[d] >= -1e-9) & (idx[d] <= shape[d] - 1 + 1e-9)
    if exact:
        ii = [np.clip(np.rint(t).astype(int), 0, s - 1) for t, s in zip(idx, shape)]
        out[inside] = field3[ii[0][inside], ii[1][inside], ii[2][inside]]
        return out, True
    i0 = [np.clip(np.floor(t).astype(int), 0, s - 2) for t, s in zip(idx, shape)]
    f = [np.clip(t - i, 0.0, 1.0) for t, i in zip(idx, i0)]
    val = 0.0
    for cx in (0, 1):
        wx = f[0] if cx else 1 - f[0]
        for cy in (0, 1):
            wy = f[1] if cy else 1 - f[1]
            for cz in (0, 1):
                wz = f[2] if cz else 1 - f[2]
                val = val + wx * wy * wz * field3[i0[0] + cx, i0[1] + cy, i0[2] + cz]
    out[inside] = np.asarray(val)[inside]
    return out, False


def interpolation_bound(grid: Grid, second_derivatives) -> float:
    """Bound of the trilinear interpolation error: sum_d h_d^2 max|f_dd| / 8."""
    return float(sum(h * h * abs(m) for h, m in zip(grid.spacing, second_derivatives)) / 8.0)


@dataclass(frozen=True)
class Slice:
    """A computed plane of mode "slices" with its own status: exact (as the full 3-D model on the same grid) or an
    approximation (a reduced model), with the reason (review B1-12)."""
    plane: Plane
    exact: bool = True
    reason: T | str = field(default="", compare=False)  # a translatable text (lfphys.i18n); not hashed


@dataclass
class Modelling:
    """How a 3-D world is modelled (owner, 2026-10-24): mode "full3d" (any plane explorable afterwards) or "slices"
    (only ``planes`` are computed and explorable). ``planes`` holds ``Slice`` entries (a bare ``Plane`` takes the
    defaults ``exact`` / ``reason`` given here); a slice that is not exact is an approximation, flagged by
    ``describe()`` per plane and for the world."""
    mode: str = "full3d"
    planes: list = field(default_factory=list)
    exact: bool = True
    reason: T | str = ""  # a translatable text (lfphys.i18n)

    def __post_init__(self):
        if self.mode not in ("full3d", "slices"):
            raise ValueError("Modelling.mode: 'full3d' or 'slices'")
        if self.mode == "slices" and not self.planes:
            raise ValueError("Modelling: mode 'slices' needs at least one plane")
        self.planes = [p if isinstance(p, Slice) else Slice(p, self.exact, self.reason) for p in self.planes]

    def find(self, plane: Plane) -> Slice | None:
        return next((s for s in self.planes if plane.same_as(s.plane)), None)

    def explorable(self, plane: Plane) -> bool:
        return self.mode == "full3d" or self.find(plane) is not None

    def is_exact(self, plane: Plane) -> bool:
        if self.mode == "full3d":
            return True
        s = self.find(plane)
        return bool(s and s.exact)

    @property
    def approximation(self) -> bool:
        return self.mode == "slices" and any(not s.exact for s in self.planes)

    def approximations(self) -> list[T]:
        """One line per approximate plane, for a run's header and passport."""
        return [T("slice {plane}: {reason}", plane=_label(s.plane), reason=s.reason)
                for s in self.planes if not s.exact]

    def describe(self) -> dict:
        d = {"mode": self.mode, "approximation": self.approximation, "approximations": self.approximations(),
             "planes": [{**s.plane.as_dict(), "label": _label(s.plane), "exact": bool(s.exact), "reason": s.reason}
                        for s in self.planes]}
        if self.mode == "full3d":
            d["note"] = T("the whole volume; any slice can be explored")
        elif self.approximation:
            items = join(self.approximations(), "; ")
            if any(s.exact for s in self.planes):
                d["note"] = T("the given slices only; APPROXIMATION in the slices: {items}. The other slices are "
                              "exact. Only these slices can be explored.", items=items)
            else:
                d["note"] = T("the given slices only; APPROXIMATION in the slices: {items}. Only these slices can be "
                              "explored.", items=items)
        else:
            d["note"] = T("the given slices only, each exact; only they can be explored")
        return d


def _label(p: Plane) -> T:
    """A translatable label: "y = 1.5" for a coordinate plane, "through the z axis, φ = 30°" for a plane containing the
    z axis, otherwise "an arbitrary plane"."""
    axis = {"xy": ("z", 2), "xz": ("y", 1), "yz": ("x", 0)}.get(p.name)
    if axis is not None:
        return T("{axis} = {value}", axis=axis[0], value=float(p.origin[axis[1]]))
    n = p.normal
    for i, a in enumerate("xyz"):  # a coordinate plane with other in-plane axes (e.g. the normal +y instead of -y)
        if abs(abs(n[i]) - 1.0) < 1e-12:
            return T("{axis} = {value}", axis=a, value=float(p.origin[i]))
    if abs(n[2]) < 1e-12 and abs(n[0] * p.origin[0] + n[1] * p.origin[1]) < 1e-12:  # contains the z axis
        u = np.asarray(p.u, float) if abs(p.u[2]) < 1e-12 else np.asarray(p.v, float)
        phi = round(math.degrees(math.atan2(u[1], u[0])) % 180.0, 2) % 180.0
        return T("through the z axis, φ = {phi}°", phi=float(phi))
    return T("an arbitrary plane")


def plane_cut(origin, normal, box):
    """The plane through ``origin`` with normal ``normal`` (in-plane axes ``Plane.horizontal``) cut by the box
    ((xmin, ymin, zmin), (xmax, ymax, zmax)): (plane, polygon of the cut in (s, t) sorted around its centre, s range,
    t range). ValueError when the plane misses the box. Shared by every 3-D world's slice planes."""
    pl = Plane.horizontal(normal, origin)
    o, n = np.asarray(pl.origin), pl.normal
    u, v = np.asarray(pl.u), np.asarray(pl.v)
    lo, hi = np.asarray(box[0], float), np.asarray(box[1], float)
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    d = (corners - o) @ n
    scale = float(np.max(np.abs(hi - lo)))
    on = np.abs(d) <= 1e-12 * scale  # corners on the plane: once each (review B2-7: the last corner was lost and the
    pts = [corners[i] for i in range(8) if on[i]]  # others repeated when the plane passed through corners)
    for a in range(8):
        for b in range(a + 1, 8):
            if np.count_nonzero(corners[a] != corners[b]) != 1 or on[a] or on[b]:
                continue
            if d[a] * d[b] < 0:  # a strict crossing inside the edge
                pts.append(corners[a] + (corners[b] - corners[a]) * d[a] / (d[a] - d[b]))
    if len(pts) < 3:
        raise ValueError(T("the plane does not cross the computed region"))
    st = np.array([[(p - o) @ u, (p - o) @ v] for p in pts])
    c = st.mean(axis=0)
    st = st[np.argsort(np.arctan2(st[:, 1] - c[1], st[:, 0] - c[0]))]
    return pl, st, (float(st[:, 0].min()), float(st[:, 0].max())), (float(st[:, 1].min()), float(st[:, 1].max()))


def plane_points(pl: Plane, s, t) -> np.ndarray:
    """Points (len(t), len(s), 3) of the plane at in-plane coordinates s (along u) and t (along v)."""
    o, u, v = (np.asarray(a, float) for a in (pl.origin, pl.u, pl.v))
    return o + np.asarray(s)[None, :, None] * u + np.asarray(t)[:, None, None] * v


def inside_box(P, box, tol: float = 1e-9) -> np.ndarray:
    lo, hi = np.asarray(box[0], float), np.asarray(box[1], float)
    return np.all((P >= lo - tol) & (P <= hi + tol), axis=-1)


def axial_plane(phi_deg: float) -> Plane:
    """The plane through the z axis at azimuth phi (degrees from the x axis): points (s cos phi, s sin phi, z);
    phi = 0 is the plane y = 0, phi = 90 the plane x = 0."""
    phi = math.radians(phi_deg)
    return Plane((0.0, 0.0, 0.0), (math.cos(phi), math.sin(phi), 0.0), (0.0, 0.0, 1.0))


def rotation_between(p1: Plane, p2: Plane) -> np.ndarray:
    """The rotation R (3x3, det 1) with R u1 = u2, R v1 = v2, R n1 = n2."""
    return p2.rotation.T @ p1.rotation


def angle_between(p1: Plane, p2: Plane) -> float:
    """Dihedral angle between the planes (rad, 0..pi/2)."""
    c = abs(float(p1.normal @ p2.normal))
    return math.acos(min(1.0, c))
