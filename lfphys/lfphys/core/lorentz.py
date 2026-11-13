# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Special relativity in 3+1 dimensions (plan P9): the Lorentz group acting on lab coordinates (ct, x, y, z), metric
diag(1, -1, -1, -1).

* boosts and rotations as 4 x 4 matrices, the decomposition of any proper orthochronous transformation into a boost
  followed by a rotation, velocity addition in any directions;
* the Thomas-Wigner rotation as an SO(3) rotation (axis and angle), from the matrices and from a closed form;
* the spinor representation SL(2, C) (the double cover: it tells a rotation by 2 pi from none);
* aberration, Doppler factor and the searchlight effect in 3-D; the transformation of electromagnetic fields;
* what an observer sees: the light-time (retarded) image of a point in uniform motion, and the outline of a moving
  sphere (Penrose 1959: a circle).

Everything is exact: closed forms of the Lorentz group in float64; functions take arrays with leading dimensions.
Velocities are in the units of ``c`` (default 1: velocities in units of c). The 2+1 functions of
``lfphys.core.relativity`` are the special case z = 0 (tests).

Conventions. ``boost(v)`` maps lab coordinates to those of the frame moving with lab velocity v (origins coincide).
``rot3(n, theta)`` is the active rotation of vectors by theta about n (right hand). A transformation L = diag(1, R)
boost(w) maps lab coordinates to a frame moving with w whose coordinates are turned by R: its spatial axes, seen from
the frame reached by boost(w) alone, are the columns of R^T.
"""

from __future__ import annotations

import numpy as np

from lfphys.i18n import T
from lfphys.codes import coded

ABOUT = {
    "layer": "core", "kind": "law",
    "title": T("Special relativity in 3+1"),
    "statement": T("The Lorentz group in 3+1: boosts and rotations, the decomposition of a transformation into a "
                   "boost and a rotation, velocity composition in any directions, the Thomas–Wigner rotation as an "
                   "SO(3) rotation (axis and angle), the spinor representation SL(2, C), aberration, the Doppler and "
                   "searchlight effects in 3-D, the transformation of the electromagnetic field, the apparent "
                   "position of a body with the light delay (the Terrell rotation, the outline of a sphere is a "
                   "circle, Penrose)."),
    "validity": T("flat spacetime; gravity is in lfphys.core.gravity"),
    "basis": ["Einstein, Ann. Phys. 17, 891 (1905)",
              T("Wigner, Ann. Math. 40, 149 (1939): representations of the Lorentz group; the Wigner rotation"),
              "Thomas, Nature 117, 514 (1926)",
              "Penrose, Proc. Camb. Phil. Soc. 55, 137 (1959); Terrell, Phys. Rev. 116, 1041 (1959)",
              "Jackson, Classical Electrodynamics, 3rd ed. (1999), §§ 11.3–11.5, 11.10",
              T("tests of the isotropy of c and of time dilation: no violation found")],
    "conflicts": [],
}

ETA = np.diag([1.0, -1.0, -1.0, -1.0])
SIGMA = np.array([[[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]], dtype=complex)
SIGMA4 = np.concatenate([np.eye(2, dtype=complex)[None], SIGMA])  # sigma_0 = identity


def _vec(v):
    v = np.asarray(v, dtype=float)
    if v.shape[-1:] != (3,):
        raise ValueError(T("a three-dimensional vector is expected (last axis of length 3)"))
    return v


def _beta(v, c):
    b = _vec(v) / c
    b2 = np.einsum("...i,...i->...", b, b)
    if np.any(b2 >= 1.0):
        raise coded(ValueError(T("|v| ≥ c: no inertial frame moves at or faster than light")),
                    "kinematics.superluminal")
    return b, b2


def gamma_of(v, c: float = 1.0):
    """Lorentz factor of velocity vectors, written as 1/sqrt((1 - |b|)(1 + |b|)) (full precision near c)."""
    b, b2 = _beta(v, c)
    m = np.sqrt(b2)
    return 1.0 / np.sqrt((1.0 - m) * (1.0 + m))


def four_velocity(v, c: float = 1.0):
    """U = dx/dtau = (gamma c, gamma v)."""
    g = gamma_of(v, c)
    return np.concatenate([(g * c)[..., None], g[..., None] * _vec(v)], axis=-1)


def mdot(a, b):
    """Minkowski product a0 b0 - a.b of four-vectors (last axis)."""
    a, b = np.asarray(a), np.asarray(b)
    return a[..., 0] * b[..., 0] - np.einsum("...i,...i->...", a[..., 1:], b[..., 1:])


def boost(v, c: float = 1.0):
    """4 x 4 matrices mapping lab (ct, x, y, z) to the coordinates of the frame moving with lab velocity v. The
    spatial block I + (gamma - 1) b b^T / b^2 is written as I + gamma^2/(gamma + 1) b b^T (no division by b^2)."""
    b, b2 = _beta(v, c)
    g = gamma_of(v, c)
    L = np.zeros(b.shape[:-1] + (4, 4))
    L[..., 0, 0] = g
    L[..., 0, 1:] = -g[..., None] * b
    L[..., 1:, 0] = -g[..., None] * b
    L[..., 1:, 1:] = np.eye(3) + (g * g / (g + 1.0))[..., None, None] * b[..., :, None] * b[..., None, :]
    return L


def rot3(axis, angle):
    """3 x 3 active rotation by ``angle`` about the unit vector ``axis`` (Rodrigues)."""
    n = _vec(axis)
    n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    th = np.asarray(angle, dtype=float)
    c, s = np.cos(th)[..., None, None], np.sin(th)[..., None, None]
    K = np.zeros(n.shape[:-1] + (3, 3))
    K[..., 0, 1], K[..., 0, 2], K[..., 1, 2] = -n[..., 2], n[..., 1], -n[..., 0]
    K = K - np.swapaxes(K, -1, -2)
    return np.eye(3) + s * K + (1.0 - c) * (K @ K)


def rotation(axis, angle):
    """4 x 4 matrix diag(1, rot3(axis, angle))."""
    R = rot3(axis, angle)
    L = np.zeros(R.shape[:-2] + (4, 4))
    L[..., 0, 0] = 1.0
    L[..., 1:, 1:] = R
    return L


def axis_angle(R):
    """Axis n and angle theta in [0, pi] of 3 x 3 rotations R = rot3(n, theta). The angle from atan2 of the
    antisymmetric and the symmetric parts (accurate at every angle); near pi the axis comes from the symmetric part,
    its sign from the antisymmetric one. For theta = 0 the axis is undefined and returned as (0, 0, 1)."""
    R = np.asarray(R, dtype=float)
    a = 0.5 * np.stack([R[..., 2, 1] - R[..., 1, 2], R[..., 0, 2] - R[..., 2, 0], R[..., 1, 0] - R[..., 0, 1]], -1)
    sn = np.linalg.norm(a, axis=-1)
    cs = 0.5 * (np.trace(R, axis1=-2, axis2=-1) - 1.0)
    th = np.arctan2(sn, cs)
    n = np.where(sn[..., None] > 1e-300, a / np.maximum(sn, 1e-300)[..., None], 0.0)
    near_pi = cs < -0.5
    if np.any(near_pi):
        S = 0.5 * (R + np.swapaxes(R, -1, -2)) - cs[..., None, None] * np.eye(3)
        S = S / np.maximum(1.0 - cs, 1e-300)[..., None, None]  # = n n^T
        k = np.argmax(np.diagonal(S, axis1=-2, axis2=-1), axis=-1)
        col = np.take_along_axis(S, k[..., None, None].repeat(3, -1), axis=-1)[..., 0]
        col = col / np.linalg.norm(col, axis=-1, keepdims=True)
        sign = np.where(np.einsum("...i,...i->...", col, a) < 0, -1.0, 1.0)
        n = np.where(near_pi[..., None], col * sign[..., None], n)
    n = np.where((sn[..., None] <= 1e-300) & ~near_pi[..., None], np.array([0.0, 0.0, 1.0]), n)
    return n, th


def inverse(L):
    """Inverse of Lorentz matrices: eta L^T eta (exact, no linear solve)."""
    return ETA @ np.swapaxes(np.asarray(L, dtype=float), -1, -2) @ ETA


def lorentz_defect(L):
    """max |L^T eta L - eta|: how far a matrix is from the Lorentz group (round-off for products of exact ones)."""
    L = np.asarray(L, dtype=float)
    return float(np.max(np.abs(np.swapaxes(L, -1, -2) @ ETA @ L - ETA)))


def decompose(L, c: float = 1.0):
    """L = diag(1, R) boost(w) for proper orthochronous L: returns (w, R). w is the lab velocity of the frame L maps
    to (its origin's worldline: the first column of L^-1 is its four-velocity over c)."""
    L = np.asarray(L, dtype=float)
    inv = inverse(L)
    w = c * inv[..., 1:, 0] / inv[..., 0, 0][..., None]
    R = (L @ boost(-w, c))[..., 1:, 1:]
    return w, R


def add_velocities(u, v, c: float = 1.0):
    """u (+) v: the lab velocity of a frame F2 that moves with velocity v relative to F1 (measured in the coordinates
    of F1, the frame reached from the lab by boost(u)), F1 moving with u in the lab:
    w = [u + v / gamma_u + gamma_u/(1 + gamma_u) (u.v) u / c^2] / (1 + u.v / c^2). Domain: |u|, |v| < c; a sum that
    rounds to |w| >= c (both within ~1e-8 of c) is refused (compose such motions by rapidities)."""
    u, v = _vec(u), _vec(v)
    gu = gamma_of(u, c)[..., None]
    gamma_of(v, c)
    uv = np.einsum("...i,...i->...", u, v)[..., None]
    w = (u + v / gu + gu / (1.0 + gu) * uv * u / c**2) / (1.0 + uv / c**2)
    if np.any(np.einsum("...i,...i->...", w, w) >= c * c):  # review B2-8: round-off at the edge of the ball
        raise ValueError(T("velocity composition at the very limit c: in float64 the sum rounded to |w| ≥ c; give "
                           "such velocities as rapidities"))
    return w


def relative_velocity(u, w, c: float = 1.0):
    """The velocity of a body moving with lab velocity w, measured in the frame reached from the lab by boost(u): the
    v with u (+) v = w."""
    U = np.einsum("...ij,...j->...i", boost(u, c), four_velocity(w, c))
    return c * U[..., 1:] / U[..., 0][..., None]


def wigner_rotation(u, v, c: float = 1.0):
    """Thomas-Wigner rotation of two boosts. F1 moves with u in the lab, F2 with v relative to F1 (v in F1's
    coordinates). boost(v) boost(u) = diag(1, R) boost(w) with w = u (+) v; R = rot3(n, theta) acts on coordinates,
    so the axes of F2 are turned by -theta about n relative to the frame reached by boost(w) alone. For u along x and v
    along y, n = +z and theta > 0, ~ |u x v| / (2 c^2) at small speeds (the 2+1 angle of
    ``relativity.wigner_rotation_angle``). Returns (w, R, n, theta), theta in [0, pi); n along u x v."""
    L = boost(v, c) @ boost(u, c)
    w, R = decompose(L, c)
    n, th = axis_angle(R)
    return w, R, n, th


def wigner_angle_closed_form(u, v, c: float = 1.0):
    """The Thomas-Wigner angle from the Lorentz factors alone (an independent route to ``wigner_rotation``):
    1 + cos theta = (1 + G + gu + gv)^2 / ((1 + G)(1 + gu)(1 + gv)), with G = gu gv (1 + u.v/c^2) the Lorentz factor
    of u (+) v. For small angles 1 - cos theta is taken from the exact identity
    2 (1 + G)(1 + gu)(1 + gv) - (1 + G + gu + gv)^2 = (gu gv)^2 |u x v|^2 / c^4 (expand with G = gu gv (1 + u.v/c^2) and
    gu^2 - 1 = gu^2 |u|^2/c^2), so no cancellation occurs."""
    u, v = _vec(u), _vec(v)
    gu, gv = gamma_of(u, c), gamma_of(v, c)
    uv = np.einsum("...i,...i->...", u, v) / c**2
    G = gu * gv * (1.0 + uv)
    den = (1.0 + G) * (1.0 + gu) * (1.0 + gv)
    cr = np.cross(u, v) / c**2
    one_minus = (gu * gv) ** 2 * np.einsum("...i,...i->...", cr, cr) / den
    one_plus = (1.0 + G + gu + gv) ** 2 / den
    return np.arctan2(np.sqrt(np.maximum(one_minus * one_plus, 0.0)), 0.5 * (one_plus - one_minus))


# --- spinors: SL(2, C) -> SO+(1, 3) -------------------------------------------------------------------------------------

def lorentz_of_sl2(A):
    """The Lorentz matrix of A in SL(2, C): X = x0 I + x.sigma -> A X A^dagger, Lambda^mu_nu = tr(sigma_mu A sigma_nu
    A^dagger) / 2. A and -A give the same Lambda (the double cover)."""
    A = np.asarray(A, dtype=complex)
    Ad = np.conj(np.swapaxes(A, -1, -2))
    T = np.einsum("mab,...bc,ncd,...da->...mn", SIGMA4, A, SIGMA4, Ad)
    return 0.5 * T.real


def sl2_boost(v, c: float = 1.0):
    """The SL(2, C) element of ``boost(v)``: exp(-eta n.sigma / 2) = cosh(eta/2) I - sinh(eta/2) n.sigma, with eta the
    rapidity and n the direction of v."""
    b, b2 = _beta(v, c)
    m = np.sqrt(b2)
    eta = np.arctanh(m)
    n = np.where(m[..., None] > 0, b / np.where(m > 0, m, 1.0)[..., None], 0.0)
    ch, sh = np.cosh(eta / 2), np.sinh(eta / 2)
    return ch[..., None, None] * np.eye(2) - sh[..., None, None] * np.einsum("...i,iab->...ab", n, SIGMA)


def sl2_rotation(axis, angle):
    """The SU(2) element of the active rotation rot3(axis, angle): exp(-i angle n.sigma / 2). Angles theta and
    theta + 2 pi give opposite elements."""
    n = _vec(axis)
    n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    th = np.asarray(angle, dtype=float)
    return (np.cos(th / 2)[..., None, None] * np.eye(2)
            - 1j * np.sin(th / 2)[..., None, None] * np.einsum("...i,iab->...ab", n, SIGMA))


def su2_axis_angle(A):
    """Axis n and angle theta in [0, 2 pi] of an SU(2) element A = cos(theta/2) I - i sin(theta/2) n.sigma (the angle
    the double cover keeps: theta and 2 pi - theta about the opposite axis give the same SO(3) rotation but opposite
    spinors)."""
    A = np.asarray(A, dtype=complex)
    ch = 0.5 * np.trace(A, axis1=-2, axis2=-1).real
    s = -0.5 * np.einsum("iab,...ba->...i", SIGMA, A).imag  # sin(theta/2) n
    sn = np.linalg.norm(s, axis=-1)
    th = 2.0 * np.arctan2(sn, ch)
    n = np.where(sn[..., None] > 1e-300, s / np.maximum(sn, 1e-300)[..., None], np.array([0.0, 0.0, 1.0]))
    return n, th


# --- light: aberration, Doppler, searchlight ----------------------------------------------------------------------------

def aberrate(n_src, v, c: float = 1.0):
    """Light emitted along unit directions ``n_src`` in the rest frame of a source that moves with lab velocity v:
    returns (n_lab, D) with n_lab its lab direction and D = nu_lab / nu_src = gamma (1 + beta.n_src) its Doppler
    factor (Lorentz transformation of the null vector (1, n_src))."""
    n = _vec(n_src)
    k = np.concatenate([np.ones(n.shape[:-1] + (1,)), n], axis=-1)
    kl = np.einsum("...ij,...j->...i", boost(-np.asarray(v, float), c), k)
    return kl[..., 1:] / kl[..., :1], kl[..., 0]


def doppler(n_lab, v, c: float = 1.0):
    """nu_received / nu_emitted for a source moving with lab velocity v whose light travels along the unit lab
    direction ``n_lab`` (from the source to the receiver at rest): 1 / (gamma (1 - beta.n_lab))."""
    b, _ = _beta(v, c)
    return 1.0 / (gamma_of(v, c) * (1.0 - np.einsum("...i,...i->...", b, _vec(n_lab))))


def searchlight(n_lab, v, c: float = 1.0):
    """Radiant intensity of a source isotropic in its rest frame (power P' there), per lab solid angle, in units of
    P'/(4 pi): (D^4 per unit time of reception by a distant receiver at rest, D^3/gamma per unit lab time of emission);
    D = ``doppler(n_lab, v)``. The second integrates to 1 over the sphere (the emitted power is invariant)."""
    D = doppler(n_lab, v, c)
    return D**4, D**3 / gamma_of(v, c)


# --- electromagnetic fields ---------------------------------------------------------------------------------------------

def field_tensor(E, B, c: float = 1.0):
    """F^{mu nu} (SI, signature +---): F^{i0} = E_i / c, F^{ij} = -eps_ijk B_k. The Lorentz force is
    dp^mu/dtau = q F^{mu nu} eta_{nu lambda} U^lambda."""
    E, B = _vec(E), _vec(B)
    F = np.zeros(E.shape[:-1] + (4, 4))
    F[..., 1:, 0] = E / c
    F[..., 0, 1:] = -E / c
    F[..., 1, 2], F[..., 2, 1] = -B[..., 2], B[..., 2]
    F[..., 2, 3], F[..., 3, 2] = -B[..., 0], B[..., 0]
    F[..., 3, 1], F[..., 1, 3] = -B[..., 1], B[..., 1]
    return F


def fields_of_tensor(F, c: float = 1.0):
    F = np.asarray(F, dtype=float)
    E = c * F[..., 1:, 0]
    B = np.stack([F[..., 3, 2], F[..., 1, 3], F[..., 2, 1]], axis=-1)
    return E, B


def transform_fields(E, B, v, c: float = 1.0):
    """E, B in the frame moving with lab velocity v (Jackson 11.149):
    E' = gamma (E + v x B) - gamma^2/(gamma + 1) b (b.E), B' = gamma (B - v x E / c^2) - gamma^2/(gamma + 1) b (b.B),
    b = v / c."""
    E, B = _vec(E), _vec(B)
    b, _ = _beta(v, c)
    g = gamma_of(v, c)[..., None]
    k = g * g / (g + 1.0)
    vv = b * c
    Ep = g * (E + np.cross(vv, B)) - k * b * np.einsum("...i,...i->...", b, E)[..., None]
    Bp = g * (B - np.cross(vv, E) / c**2) - k * b * np.einsum("...i,...i->...", b, B)[..., None]
    return Ep, Bp


# --- what an observer sees ----------------------------------------------------------------------------------------------

def retarded_time(x0, v, t_obs, c: float = 1.0):
    """The emission time t_e <= t_obs at which light from a point moving as x(t) = x0 + v t reaches the origin at
    t_obs: the retarded root of |x0 + v t_e| = c (t_obs - t_e), written without cancellation."""
    x0, v = _vec(x0), _vec(v)
    a = c * c - np.einsum("...i,...i->...", v, v)
    if np.any(a <= 0):
        raise coded(ValueError(T("|v| ≥ c: no inertial frame moves at or faster than light")),
                    "kinematics.superluminal")
    t_obs = np.asarray(t_obs, dtype=float)
    bp = np.einsum("...i,...i->...", x0, v) + c * c * t_obs
    cc = np.einsum("...i,...i->...", x0, x0) - c * c * t_obs * t_obs
    sq = np.sqrt(bp * bp + a * cc)
    return np.where(bp > 0, -cc / (bp + sq), (bp - sq) / a)


def apparent(x0, v, t_obs=0.0, observer_v=(0.0, 0.0, 0.0), c: float = 1.0):
    """The image of a point moving as x(t) = x0 + v t, seen at time t_obs by an observer passing the origin then with
    lab velocity ``observer_v``: returns (t_e, x_e, d_obs, D) — the emission event, the unit direction in which the
    observer sees the point (in the observer's frame) and the Doppler factor nu_seen / nu_emitted (the point emits at
    a fixed frequency in its rest frame): D = (k.U_obs) / (k.U_point) for the photon's four-vector k."""
    x0, v = _vec(x0), _vec(v)
    te = retarded_time(x0, v, t_obs, c)
    xe = x0 + v * te[..., None]
    r = np.linalg.norm(xe, axis=-1, keepdims=True)
    if np.any(r == 0):  # review B2-8: a point at the observer has no direction
        raise ValueError(T("the point is at the observer at the moment of observation: it has no direction"))
    khat = -xe / r  # the photon travels from x_e to the origin
    k = np.concatenate([np.ones(khat.shape[:-1] + (1,)), khat], axis=-1)
    uo = np.broadcast_to(np.asarray(observer_v, float), khat.shape)
    ko = np.einsum("...ij,...j->...i", boost(uo, c), k)
    d_obs = -ko[..., 1:] / ko[..., :1]
    D = mdot(k, four_velocity(uo, c)) / mdot(k, four_velocity(np.broadcast_to(v, khat.shape), c))
    return te, xe, d_obs, D


def sphere_outline(center0, radius: float, v, t_obs: float = 0.0, c: float = 1.0, n: int = 256):
    """Lab directions of the apparent outline of a body that is a sphere of radius ``radius`` in its rest frame, its
    centre moving as center0 + v t, seen by an observer at rest at the origin at time t_obs (light-time included). In
    the lab the body is the ellipsoid |x_perp|^2 + gamma^2 x_par^2 = radius^2 about its centre (Lorentz contraction).
    A lab ray d (from the observer, going back in time) meets it where s (d + v/c) - P lies on the ellipsoid,
    P = center0 + v t_obs; the stretch T = I + (gamma - 1) n n^T (n = v/|v|) turns the ellipsoid into the sphere, so T (d
    + v/c) lies on the cone of half-angle arcsin(radius/|T P|) about T P; then d = lambda m - v/c with |d| = 1 and m
    along T^-1 of the cone's direction. Returns (n, 3) unit vectors. Penrose (1959): they lie on a circle of the
    celestial sphere (tests)."""
    b = _vec(v) / c
    P = _vec(center0) + _vec(v) * t_obs
    bn = float(np.linalg.norm(b))
    g = float(gamma_of(b))
    nv = b / bn if bn > 0 else np.zeros(3)
    Tm = np.eye(3) + (g - 1.0) * np.outer(nv, nv)  # the stretch T of the docstring
    Ti = np.eye(3) + (1.0 / g - 1.0) * np.outer(nv, nv)
    TP = Tm @ P
    dist = float(np.linalg.norm(TP))
    if dist <= radius:
        raise ValueError(T("the observer is inside the body"))
    alpha = np.arcsin(radius / dist)
    ph = TP / dist
    e1 = np.cross(ph, [1.0, 0.0, 0.0] if abs(ph[0]) < 0.9 else [0.0, 1.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(ph, e1)
    psi = np.linspace(0.0, 2 * np.pi, n, endpoint=False)
    k = (np.cos(alpha) * ph[None, :] + np.sin(alpha) * (np.cos(psi)[:, None] * e1 + np.sin(psi)[:, None] * e2))
    m = k @ Ti.T
    m /= np.linalg.norm(m, axis=1, keepdims=True)
    mb = m @ b
    lam = mb + np.sqrt(mb * mb + 1.0 - b @ b)
    return lam[:, None] * m - b[None, :]
