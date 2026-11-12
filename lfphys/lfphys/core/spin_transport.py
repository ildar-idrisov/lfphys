# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Gyroscopes and spins carried along accelerated motion in special relativity (plan P9):

* **Fermi-Walker transport along a manoeuvre.** A craft follows an acceleration programme given in its own comoving
  frame: burns (thrust of constant direction) and turns (thrust whose direction turns at a constant rate about an axis
  fixed in the comoving frame). The comoving frame of its gyroscopes is carried without rotation (Fermi-Walker); each
  piece is solved exactly by matrix exponentials (a turn becomes a constant generator in the turning frame), in the
  Lorentz group and, independently, in SL(2, C). Returned along the way: proper and lab time, position, velocity, the
  gyroscopes' orientation and the fuel spent (the total rapidity, the integral of |a| dtau / c).
* **Holonomy.** A manoeuvre that ends at rest leaves the gyroscopes turned by a rotation (Thomas precession): its axis
  and angle in SO(3), and the SU(2) element of the spinor carried along (the double cover keeps the angle in
  [0, 2 pi]: a turn by 2 pi changes the spinor's sign).
* **Velocity space** (the hyperbolic space of curvature -1/c^2 in rapidity units) as the reference for the holonomy:
  distances (relative rapidities), angles, the area of geodesic polygons by Gauss-Bonnet, hyperbolic circles, and the
  isoperimetric inequality of the hyperbolic plane L^2 >= 4 pi A + A^2. For a loop in one plane of velocity space the
  gyroscopes turn by the enclosed area, against the sense of the loop (tests: Thomas's 2 pi (gamma - 1) per revolution
  of uniform circular motion).
* **Charged particle in uniform fields**: exact motion (the exponential of the field tensor) and the spin by the
  Bargmann-Michel-Telegdi equation, with the Thomas-BMT precession rate of the rest-frame spin as a second route.

Units: c (default 1); the thrust magnitude a sets the time scale (tau = c s / a for fuel s) and the length scale c^2/a.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm

from lfphys.i18n import T

from . import lorentz as LZ

ABOUT = {
    "layer": "core", "kind": "law",
    "title": T("Transport of a gyroscope and a spin in SR: Thomas precession, holonomy, BMT"),
    "statement": T("Fermi–Walker transport of a set of gyroscopes along an acceleration programme (exact, by "
                   "exponentials of the generators of the Lorentz group and, independently, of SL(2, C)); the "
                   "rotation of the gyroscopes after a closed manoeuvre (holonomy) in SO(3) and SU(2); the geometry "
                   "of velocity space (hyperbolic): distances, angles, the area of a polygon by Gauss–Bonnet, the "
                   "isoperimetric inequality of the plane L² ≥ 4πA + A²; the motion of a charge in uniform fields "
                   "and the precession of its spin (the Bargmann–Michel–Telegdi equation)."),
    "validity": T("flat spacetime; the acceleration programme is given in the comoving frame; the fields are "
                  "uniform and constant; the spin is a classical vector (BMT: g constant, field gradients neglected)"),
    "basis": ["Thomas, Nature 117, 514 (1926); Phil. Mag. 3, 1 (1927)",
              "Fermi–Walker transport: Misner, Thorne, Wheeler, Gravitation (1973), § 6.5",
              "Bargmann, Michel, Telegdi, Phys. Rev. Lett. 2, 435 (1959)",
              "Jackson, Classical Electrodynamics, 3rd ed. (1999), §§ 11.8, 11.11",
              "Aravind, Am. J. Phys. 65, 634 (1997): the Wigner angle as an anholonomy in rapidity space",
              "Osserman, Bull. Amer. Math. Soc. 84, 1182 (1978): the isoperimetric inequality on surfaces of "
              "constant curvature"],
    "conflicts": [],
}

# generators of the boosts of the Lorentz group acting on (ct, x, y, z)
K = np.zeros((3, 4, 4))
for _i in range(3):
    K[_i, 0, _i + 1] = K[_i, _i + 1, 0] = 1.0


def _cross_matrix(n):
    n = np.asarray(n, dtype=float)
    return np.array([[0.0, -n[2], n[1]], [n[2], 0.0, -n[0]], [-n[1], n[0], 0.0]])


def gen_boost(n):
    """Generator of boosts along n per unit rapidity, acting on the comoving basis: exp(s gen_boost(n)) is the basis
    of a frame moving with velocity tanh(s) n (units of c) relative to the current one (= lorentz.boost(-tanh(s) n))."""
    return np.einsum("i,ijk->jk", np.asarray(n, float), K)


def gen_rot(n):
    """Generator of active rotations about n: exp(theta gen_rot(n)) = lorentz.rotation(n, theta)."""
    G = np.zeros((4, 4))
    G[1:, 1:] = _cross_matrix(n)
    return G


def sl2_gen_boost(n):
    """The SL(2, C) generator of ``gen_boost(n)``: n.sigma / 2."""
    return 0.5 * np.einsum("i,iab->ab", np.asarray(n, float), LZ.SIGMA)


def sl2_gen_rot(n):
    """The SU(2) generator of ``gen_rot(n)``: -i n.sigma / 2."""
    return -0.5j * np.einsum("i,iab->ab", np.asarray(n, float), LZ.SIGMA)


def expm2(X):
    """exp of a traceless 2 x 2 complex matrix in closed form: X^2 = q I, exp(X) = cosh(r) I + sinh(r)/r X, r^2 = q
    (the series for small r): an independent route from scipy's Pade exponential used for the 4 x 4 matrices."""
    X = np.asarray(X, dtype=complex)
    q = -(X[0, 0] * X[1, 1] - X[0, 1] * X[1, 0])  # X^2 = -det(X) I for a traceless X
    r = np.sqrt(q)
    if abs(r) < 1e-3:
        ch = 1 + q / 2 + q * q / 24 + q ** 3 / 720 + q ** 4 / 40320
        sh = 1 + q / 6 + q * q / 120 + q ** 3 / 5040 + q ** 4 / 362880
    else:
        ch, sh = np.cosh(r), np.sinh(r) / r
    return ch * np.eye(2) + sh * X


# --- manoeuvres ---------------------------------------------------------------------------------------------------------

@dataclass
class Burn:
    """Thrust of constant direction ``direction`` (a unit vector of the comoving frame) until the rapidity changed by
    ``rapidity``: a geodesic of velocity space."""
    direction: tuple
    rapidity: float


@dataclass
class Turn:
    """Thrust of constant magnitude whose direction (``direction`` at the start, in the comoving frame) turns about the
    comoving ``axis`` by ``curvature`` radians per unit rapidity, for a fuel of ``rapidity``. With the axis
    perpendicular to the thrust the velocity runs along a circle of velocity space of geodesic curvature
    ``curvature`` (a circle of radius rho has curvature coth(rho); 1 is a horocycle, less a hypercycle); otherwise it
    runs along a helix."""
    direction: tuple
    axis: tuple
    curvature: float
    rapidity: float


@dataclass
class State:
    s: float          # fuel spent so far: the integral of |a| dtau / c
    tau: float        # proper time
    x: np.ndarray     # (ct, x, y, z) of the craft
    M: np.ndarray     # the comoving (gyroscope) basis in lab coordinates: columns e0 = U/c, e1, e2, e3
    A: np.ndarray     # the same in SL(2, C) (continuous: keeps the spinor's sign)


@dataclass
class Track:
    s: np.ndarray
    tau: np.ndarray
    x: np.ndarray       # (n, 4): (ct, x, y, z)
    beta: np.ndarray    # (n, 3): velocity / c (a point of the velocity ball)
    M: np.ndarray       # (n, 4, 4)
    A: np.ndarray       # (n, 2, 2)
    O: np.ndarray       # (n, 3, 3): the gyroscopes' axes (columns) relative to the frame reached by a pure boost
    piece: np.ndarray   # (n,) index of the piece each sample belongs to
    ends: list = field(default_factory=list)  # the exact states at the end of each piece


def _unit(v):
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    if n == 0.0 or not math.isfinite(n):
        raise ValueError(T("no direction given"))
    return v / n


def _piece_generators(p):
    """(G, R_rate, g2, r2): the generator in the turning frame, the turning generator to undo, and the same in SL(2, C)."""
    if isinstance(p, Burn):
        n = _unit(p.direction)
        return gen_boost(n), None, sl2_gen_boost(n), None
    if isinstance(p, Turn):
        n, w = _unit(p.direction), _unit(p.axis)
        k = float(p.curvature)
        return (gen_boost(n) + k * gen_rot(w), k * gen_rot(w),
                sl2_gen_boost(n) + k * sl2_gen_rot(w), k * sl2_gen_rot(w))
    raise TypeError(f"unknown piece {p!r}")


def _advance(st: State, p, s: float, c: float, accel: float) -> State:
    """The exact state after fuel s (0 <= s <= the piece's rapidity) of piece p, from the state st at its start."""
    G, Rr, g2, r2 = _piece_generators(p)
    VL = np.zeros((8, 8))
    VL[:4, :4] = G * s
    VL[:4, 4:] = np.eye(4) * s
    E = expm(VL)  # Van Loan: E[:4, :4] = exp(s G), E[:4, 4:] = the integral of exp(sigma G) over [0, s]
    M = st.M @ E[:4, :4]
    A = st.A @ expm2(g2 * s)
    if Rr is not None:  # undo the turning of the frame in which the generator is constant
        M = M @ expm(-s * Rr)
        A = A @ expm2(-s * r2)
    x = st.x + (c * c / accel) * (st.M @ E[:4, 4:])[:, 0]
    return State(st.s + s, st.tau + c * s / accel, x, M, A)


class Manoeuvre:
    """An acceleration programme from rest at the origin: a sequence of Burn and Turn pieces with a constant magnitude
    ``accel`` of the proper acceleration (it sets only the time and length scales)."""

    def __init__(self, pieces, c: float = 1.0, accel: float = 1.0):
        if accel <= 0 or c <= 0:
            raise ValueError(T("the acceleration and c must be positive"))
        self.pieces = list(pieces)
        for p in self.pieces:
            if not (p.rapidity >= 0 and math.isfinite(p.rapidity)):
                raise ValueError(T("the rapidity of a segment must be non-negative"))
        self.c, self.accel = float(c), float(accel)

    def start(self) -> State:
        return State(0.0, 0.0, np.zeros(4), np.eye(4), np.eye(2, dtype=complex))

    def fuel(self) -> float:
        return float(sum(p.rapidity for p in self.pieces))

    def states(self, ds: float = 0.02):
        """The exact states every ``ds`` of fuel and at the pieces' ends, each computed from the start of its piece:
        (piece index, State) pairs, the start first (index 0); nothing is derived from them."""
        st = self.start()
        yield 0, st
        for k, p in enumerate(self.pieces):
            n = max(1, int(math.ceil(p.rapidity / ds)))
            for j in range(1, n + 1):
                q = _advance(st, p, p.rapidity * j / n, self.c, self.accel)
                yield k, q
            st = q

    def run(self, ds: float = 0.02) -> Track:
        """Samples every ``ds`` of fuel (and at every piece's ends), each computed exactly from the start of its piece."""
        rows = list(self.states(ds))
        ends = [rows[i][1] for i in range(1, len(rows)) if i == len(rows) - 1 or rows[i + 1][0] != rows[i][0]]
        S = [r[1] for r in rows]
        M = np.array([q.M for q in S])
        beta = M[:, 1:, 0] / M[:, :1, 0]
        O = (LZ.boost(beta) @ M)[:, 1:, 1:]
        return Track(np.array([q.s for q in S]), np.array([q.tau for q in S]), np.array([q.x for q in S]), beta, M,
                     np.array([q.A for q in S]), O, np.array([r[0] for r in rows]), ends)

    def end(self) -> State:
        st = self.start()
        for p in self.pieces:
            st = _advance(st, p, p.rapidity, self.c, self.accel)
        return st


def return_burn(state: State) -> Burn:
    """The burn that brings the craft from ``state`` back to rest along the geodesic: the direction of the lab rest
    frame's four-velocity in the comoving frame, and its rapidity."""
    Uc = LZ.inverse(state.M)[:, 0]
    sp = float(np.linalg.norm(Uc[1:]))
    if sp < 1e-15:
        return Burn((1.0, 0.0, 0.0), 0.0)
    return Burn(tuple(Uc[1:] / sp), math.asinh(sp))


def polygon_burns(vertices, c: float = 1.0):
    """Burns that take the craft from rest through the lab velocities ``vertices`` (each reached along the geodesic
    from the previous one) and back to rest: the k-th burn's direction and rapidity are those of the next vertex's
    four-velocity in the craft's comoving frame at the k-th vertex (that frame carries the rotation gathered so far).
    The first and last points are rest; ``vertices`` lists the ones in between.

    Built in extended precision (numpy longdouble, a 64-bit mantissa on x86-64): the next vertex seen from the comoving
    frame is a difference of products of entries up to cosh(eta) (cancellation ~ eps cosh^2), which in float64 bent a
    planar loop out of its plane by more than the flight's own round-off (review B2-1). Each burn is rounded to float64
    as it will be flown, and the frame advanced by that rounded burn, so the next burn makes up for the rounding and the
    last one returns to rest."""
    LD = np.longdouble
    eta_m = np.diag(np.array([1, -1, -1, -1], dtype=LD))
    pts = [np.zeros(3)] + [np.asarray(v, float) / c for v in vertices] + [np.zeros(3)]
    M = np.eye(4, dtype=LD)
    burns = []
    for w in pts[1:]:
        b = np.asarray(w, dtype=LD)
        m = np.sqrt(b @ b)
        if m >= 1:
            raise ValueError("|v| >= c")
        g = LD(1) / np.sqrt((LD(1) - m) * (LD(1) + m))
        U = np.concatenate([[g], g * b])            # over c
        Uc = eta_m @ M.T @ eta_m @ U                # in the comoving frame (M^-1 = eta M^T eta)
        sp = np.sqrt(Uc[1:] @ Uc[1:])
        if sp < 1e-15:
            continue
        burn = Burn(tuple(float(x) for x in Uc[1:] / sp), float(np.arcsinh(sp)))
        burns.append(burn)
        n = np.asarray(burn.direction, dtype=LD)
        n = n / np.sqrt(n @ n)
        e = LD(burn.rapidity)
        B = np.eye(4, dtype=LD)  # exp(e K.n): the basis of the frame the rounded burn reaches
        B[0, 0] = np.cosh(e)
        B[0, 1:] = B[1:, 0] = np.sinh(e) * n
        B[1:, 1:] += (np.cosh(e) - LD(1)) * np.outer(n, n)
        M = M @ B
    return burns


def holonomy(state: State, tol: float = 1e-9) -> dict:
    """The gyroscopes' rotation after a manoeuvre that ends at rest: R (active: the gyroscopes' axes are its columns in
    lab axes), its axis and angle in [0, pi] (SO(3)), and the SU(2) element of the spinor carried along with its axis
    and angle in [0, 2 pi]; ``closed`` says whether the craft is back at rest within ``tol`` (|beta|)."""
    M, A = state.M, state.A
    beta = M[1:, 0] / M[0, 0]
    sp = float(np.linalg.norm(beta))
    R = (LZ.boost(beta) @ M)[1:, 1:]
    n, th = LZ.axis_angle(R)
    # the spinor at rest is in SU(2) up to the residual boost; remove that boost's SL(2, C) part
    A_rest = LZ.sl2_boost(beta) @ A
    n2, th2 = LZ.su2_axis_angle(A_rest)
    return {"closed": sp <= tol, "residual_beta": sp, "R": R, "axis": n, "angle": float(th), "su2": A_rest,
            "su2_axis": n2, "su2_angle": float(th2), "spinor_sign": -1 if th2 > math.pi else 1,
            "unitarity": float(np.max(np.abs(A_rest @ A_rest.conj().T - np.eye(2))))}


def thomas_rate(v, a, c: float = 1.0):
    """Thomas precession rate (lab time) of the rest-frame axes of a body with lab velocity v and lab acceleration
    a = dv/dt: omega_T = gamma^2/(gamma + 1) (a x v) / c^2 (Jackson 11.119): d s/dt = omega_T x s."""
    v, a = np.asarray(v, float), np.asarray(a, float)
    g = LZ.gamma_of(v, c)
    return (g * g / (g + 1.0))[..., None] * np.cross(a, v) / c**2


# --- velocity space (hyperbolic, curvature -1 in rapidity units) ----------------------------------------------------------

def distance(w1, w2, c: float = 1.0):
    """The relative rapidity of two lab velocities: the distance in velocity space, asinh(|U_rel| / c)."""
    U = np.einsum("...ij,...j->...i", LZ.boost(w1, c), LZ.four_velocity(w2, c))
    return np.arcsinh(np.linalg.norm(U[..., 1:], axis=-1) / c)


def angle_at(p, q, r, c: float = 1.0):
    """The angle at velocity p between the geodesics to q and to r (measured in p's pure-boost frame, where velocity
    space is locally Euclidean)."""
    t1 = LZ.relative_velocity(p, q, c)
    t2 = LZ.relative_velocity(p, r, c)
    cr = np.linalg.norm(np.cross(t1, t2), axis=-1)
    return np.arctan2(cr, np.einsum("...i,...i->...", t1, t2))


def polygon_area(vertices, c: float = 1.0) -> float:
    """Area of a convex geodesic polygon of velocity space whose vertices lie in one plane (Gauss-Bonnet with
    curvature -1: (n - 2) pi minus the sum of the interior angles); vertices in order, as lab velocities."""
    P = [np.asarray(v, float) for v in vertices]
    n = len(P)
    s = sum(float(angle_at(P[k], P[k - 1], P[(k + 1) % n], c)) for k in range(n))
    return (n - 2) * math.pi - s


def triangle_area(a, b, cc):
    """Area of a hyperbolic triangle (curvature -1) from its sides by the hyperbolic L'Huilier formula
    tan(A/4)^2 = tanh(s/2) tanh((s - a)/2) tanh((s - b)/2) tanh((s - c)/2), s the half-perimeter (no cancellation for
    thin triangles)."""
    a, b, cc = (np.asarray(x, float) for x in (a, b, cc))
    s = 0.5 * (a + b + cc)
    t = np.tanh(s / 2) * np.tanh((s - a) / 2) * np.tanh((s - b) / 2) * np.tanh((s - cc) / 2)
    return 4.0 * np.arctan(np.sqrt(np.maximum(t, 0.0)))


def circle_area(rho):
    """Area enclosed by a circle of radius rho in the hyperbolic plane: 2 pi (cosh rho - 1) = 4 pi sinh^2(rho/2)."""
    return 4.0 * np.pi * np.sinh(np.asarray(rho, float) / 2) ** 2


def circle_length(rho):
    return 2.0 * np.pi * np.sinh(np.asarray(rho, float))


def regular_polygon_area(n: int, rho: float) -> float:
    """Area of the regular geodesic n-gon with circumradius rho: (n - 2) pi - n alpha, with the interior angle alpha
    from the right triangle centre-vertex-midpoint: cosh(rho) = cot(pi/n) cot(alpha/2)."""
    alpha = 2.0 * math.atan(1.0 / (math.cosh(rho) * math.tan(math.pi / n)))
    return (n - 2) * math.pi - n * alpha


def isoperimetric_bound(L):
    """The largest area a closed curve of length L can enclose in the hyperbolic plane of curvature -1:
    L^2 >= 4 pi A + A^2, i.e. A <= sqrt(4 pi^2 + L^2) - 2 pi, written as L^2 / (sqrt(4 pi^2 + L^2) + 2 pi). Osserman,
    Bull. AMS 84, 1182 (1978), eq. (4.23) L^2 >= 4 pi A - K A^2 "for all surfaces of constant curvature, with equality
    in each case only for geodesic circles" (proved for K = -1 by Schmidt, 1940, as cited there; checked against the
    text 2026-10-27). A theorem about curves in a plane; for curves that leave every plane (in 3-D velocity space) it
    is a comparison line, not a bound proven here."""
    L = np.asarray(L, float)
    return L * L / (np.sqrt(4.0 * np.pi**2 + L * L) + 2.0 * np.pi)


# --- a charged particle in uniform fields: motion and spin ------------------------------------------------------------

def charge_motion(q_over_m: float, E, B, U0, taus, c: float = 1.0):
    """Exact motion in uniform constant fields: dU/dtau = (q/m) F eta U, so U(tau) = exp(tau (q/m) F eta) U0, and the
    position (ct, x) by the integral of U (Van Loan). Returns (U (n, 4), x (n, 4)) at proper times ``taus``."""
    Fe = q_over_m * LZ.field_tensor(E, B, c) @ LZ.ETA
    U0 = np.asarray(U0, float)
    Us, xs = [], []
    for tau in np.atleast_1d(taus):
        VL = np.zeros((8, 8))
        VL[:4, :4] = Fe * tau
        VL[:4, 4:] = np.eye(4) * tau
        Ex = expm(VL)
        Us.append(Ex[:4, :4] @ U0)
        xs.append(Ex[:4, 4:] @ U0)
    return np.array(Us), np.array(xs)


def bmt(q_over_m: float, g: float, E, B, U0, S0, taus, c: float = 1.0, rtol: float = 1e-12):
    """Spin four-vector S of a particle (charge to mass q/m, g-factor g) in uniform fields by the BMT equation
    dS/dtau = (q/m) [ (g/2) F eta S + (g/2 - 1)/c^2 U (S^T eta F eta U) ] (Jackson 11.164 in SI), with the exact U(tau)
    of ``charge_motion``; integrated by DOP853 at relative tolerance ``rtol``. S.U = 0 is kept by the equation.
    Returns (U (n, 4), S (n, 4)) at proper times ``taus`` (increasing, from 0)."""
    F = LZ.field_tensor(E, B, c)
    Fe = q_over_m * F @ LZ.ETA
    U0, S0 = np.asarray(U0, float), np.asarray(S0, float)
    k = 0.5 * g - 1.0

    def U_at(tau):
        return expm(Fe * tau) @ U0

    def rhs(tau, S):
        U = U_at(tau)
        return 0.5 * g * Fe @ S + q_over_m * k / c**2 * U * (S @ LZ.ETA @ F @ LZ.ETA @ U)

    taus = np.atleast_1d(np.asarray(taus, float))
    sol = solve_ivp(rhs, (0.0, float(taus[-1])), S0, method="DOP853", t_eval=taus, rtol=rtol,
                    atol=rtol * float(np.max(np.abs(S0))))
    return np.array([U_at(t) for t in taus]), sol.y.T


def rest_spin(U, S, c: float = 1.0):
    """The spin in the particle's rest frame (reached from the lab by a pure boost): s = S_vec - S^0 U_vec / (U^0 + c)."""
    U, S = np.asarray(U, float), np.asarray(S, float)
    return S[..., 1:] - (S[..., :1] * U[..., 1:]) / (U[..., :1] + c)


def thomas_bmt_rate(q_over_m: float, g: float, E, B, v, c: float = 1.0):
    """Precession rate (lab time) of the rest-frame spin: ds/dt = Omega x s with (Jackson 11.170, SI)
    Omega = -(q/m) [ (g/2 - 1 + 1/gamma) B - (g/2 - 1) gamma/(gamma + 1) (b.B) b - (g/2 - gamma/(gamma + 1)) b x E / c ],
    b = v / c."""
    E, B, v = (np.asarray(x, float) for x in (E, B, v))
    b = v / c
    gm = LZ.gamma_of(v, c)
    a = 0.5 * g - 1.0
    term = ((a + 1.0 / gm)[..., None] * B - (a * gm / (gm + 1.0))[..., None] * np.einsum("...i,...i->...", b, B)[..., None] * b
            - (0.5 * g - gm / (gm + 1.0))[..., None] * np.cross(b, E) / c)
    return -q_over_m * term
