# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Newtonian N-body gravity for the playground (plan P15.1): bodies with stable keys, close encounters, mergers.

Any consistent units; G is a parameter. Body k has position x_k, velocity v_k (3-vectors), mass m_k >= 0 and radius
R_k >= 0. A body with m = 0 is a test particle: it feels the massive bodies and exerts nothing. With r_ij = x_j - x_i,
v_ij = v_j - v_i (Nitadori & Makino 2008, "NM08", New Astron. 13, 498, Eqs. 1, 2, 5):

    a_i = G sum_j m_j r_ij / r^3,      j_i = da_i/dt = G sum_j m_j [v_ij / r^3 - 3 alpha r_ij / r^3],
    alpha = (r_ij . v_ij) / r^2,

the sums over the massive bodies j != i. No softening: point masses (``collisions="pass"``) meet the 1/r singularity
only in an exact head-on collision, which raises FloatingPointError.

Integrators (``integrator``):

* ``"hermite"`` (default; close encounters) - the fourth-order Hermite scheme of Makino & Aarseth (1992) in the
  P(EC)^n form of Kokubo, Yoshinaga & Makino (1998, "KYM98", MNRAS 297, 1067), with one step shared by all bodies.
  Predictor (KYM98 Eqs. 1-2): x_p = x0 + v0 dt + a0 dt^2/2 + j0 dt^3/6, v_p = v0 + a0 dt + j0 dt^2/2; then n times
  (``n_iter``): evaluate a1, j1 at the current estimate and correct by the implicit time-symmetric form (KYM98
  Eqs. 7-8)
      v1 = v0 + (a1 + a0) dt/2 - (j1 - j0) dt^2/12,
      x1 = x0 + (v1 + v0) dt/2 - (a1 - a0) dt^2/10 + (j1 + j0) dt^3/120.
  KYM98: "The fourth-order implicit Hermite scheme is a time-symmetric integrator that has no secular energy error for
  the integration of periodic orbits with time-symmetric time-steps"; n = 2-3 iterations come close to it (their
  Figs. 1-3; Hut, Makino & McMillan 1995, "HMM95", ApJ 443, L93: e = 0.999, 10^3 steps per orbit, drift of a/a
  1e-6 with one iteration, 2e-10 with two). The step: Aarseth's criterion (NM08 Eq. 15, KYM98 Eq. 9)
      tau = sqrt(eta (|a||a^(2)| + |a^(1)|^2) / (|a^(1)||a^(3)| + |a^(2)|^2))      ("Usually, a value around 0.02 is
  used for eta", NM08), with a^(2), a^(3) at both ends of the step from the step's own cubic Hermite interpolant of
  the acceleration (KYM98 Eqs. 5, 6, 10):
      a0^(2) = [-6 (a0 - a1) - dt (4 j0 + 2 j1)] / dt^2,  a^(3) = [12 (a0 - a1) + 6 dt (j0 + j1)] / dt^3,
      a1^(2) = a0^(2) + a^(3) dt,
  and the step is time-symmetrized as in HMM95 Eq. (4b), dt = [h(start) + h(end)]/2 with h = min over bodies of tau:
  the step is redone ("passes", at most ``max_passes``) until |dt - (h0 + h1)/2| <= ``dt_rtol`` dt (the first pass
  with one corrector only, as a cheap estimate of the rule, when more passes are allowed; ``max_passes = 1`` takes the
  extrapolated step without symmetrizing it, with all ``n_iter`` correctors: review B6-G9). Reversing a step
  gives the same interpolant, so the rule is symmetric. The first step after a start or an edit begins from
  eta_start |a|/|j| (KYM98 Eq. 12), or eta_start sqrt(d/|a|) (d: distance to the nearest massive body) where j = 0
  (bodies at rest), and is then iterated to the rule. NOT symplectic: with time-symmetric steps and enough
  iterations the energy error of periodic orbits oscillates (KYM98, HMM95); the step is symmetric only to
  ``dt_rtol``, which leaves a residual secular drift (review B6-G8; e = 0.999, eta = 0.02, 386 steps per orbit, the
  error's own level dE/E = 4.5e-4; measured over 300 orbits, slope per orbit / force evaluations per orbit):
  dt_rtol 1e-3: -2.1e-6 / 1633 (the drift reaches the error's level in ~200 orbits); 1e-4 (the default): -7.1e-8 /
  1988 (~6000 orbits); 1e-5: -1.6e-8 / 3098; 1e-6: -7.5e-10 / 3419; at e = 0.9: -8.4e-9 (1e-3), -1.3e-10 (1e-5).
  The default 1e-4 costs more where the step changes fast: ``bench``'s cold random clusters take 0.64 / 1.1 / 4.4 /
  46 ms per step for N = 3 / 30 / 100 / 300 against 0.39 / 0.66 / 3.8 / 26 ms at 1e-3 (2.95 passes per step against
  2.14); pass ``dt_rtol=1e-3`` where speed matters more than the drift. In chaotic encounters (no periodicity) the
  error grows as a random walk of the local errors. Linear momentum and the centre-of-mass
  motion are conserved to round-off (sum_i m_i a_i = 0 and sum_i m_i j_i = 0 pair by pair); angular momentum is not
  conserved exactly by the corrector (truncation error, without secular growth on periodic orbits; tests).
* ``"yoshida4"`` (long quiet systems; fixed step ``dt``) - the fourth-order symplectic composition of Forest & Ruth
  (1990) and Yoshida (1990), in its velocity form (Omelyan, Mryglod & Folk 2002, cond-mat/0110585, Eq. 8 and the
  "velocity FR counterpart"): kicks theta/2, (1-theta)/2, (1-theta)/2, theta/2 around drifts theta, 1-2 theta, theta,
  theta = 1/(2 - 2^(1/3)) ~ 1.3512 (three force evaluations per step). Symplectic and time-symmetric for a fixed step:
  the energy error stays bounded (oscillates at O(dt^4)) over arbitrarily long times; momentum AND angular momentum
  are conserved to round-off (a drift conserves x x v, a kick of central pair forces adds no torque). Close encounters
  need a step much smaller than their time scale - a fixed step does not adapt (use "hermite" there).

Time and output. The integrator advances in its own steps; ``advance(t)`` reveals the world at time t from the
current step's continuous output (Hermite: the corrector's Taylor polynomial x0 + v0 s + a0 s^2/2 + j0 s^3/6 +
a0^(2) s^4/24 + a^(3) s^5/120, equal to the committed x1 at s = dt; yoshida4: the quintic Hermite interpolant of
x, v, a at both ends), so the trajectory does not depend on how the caller slices time. An edit (add, remove, set,
reverse) first commits the state shown at the current time (that continuous output, accurate to the same order as
the steps), so every body not edited keeps exactly its state; the step rule then restarts. A free system (no massive
body, or one body alone) moves exactly in straight lines. Drawing (review UX-ui U2): ``advance(t, samples=Samples())``
also returns points of that continuous output (positions and velocities) on a grid inside every step, fine enough that
no body's direction of motion turns by more than a stated angle between two of them, so a caller can draw the orbits
smoothly at any speed (one point per call joined by chords made Mercury a pentagon); the grid belongs to the step, so
the points do not depend on how the caller slices time.

Collisions (``collisions``): two bodies touch when |x_i - x_j| = R_i + R_j (at least one of them massive).
``"merge"``: the contact time is found on the step's continuous output (sampled, then Brent to round-off; dips
between samples are found as minima of the separation) and the state there is committed; the two become one body at
their centre of mass with
m = m_i + m_j, momentum m_i v_i + m_j v_j (both exact up to one rounding), radius (R_i^3 + R_j^3)^(1/3) (equal
density: a stated choice), keeping the key of the heavier body. A body added with ``radius_per_mass`` k > 0 (a compact
body: k = 2G/c^2 makes its radius the Schwarzschild radius, a black hole's capture radius) has R = k m now, after every
change of its mass and after every merger: a merger with it keeps its key (the compact body absorbs the other; of two
compact bodies the heavier) and the result has R = k (m_i + m_j) (review B6-G5: the equal-density rule gave a hole
that swallowed a star the star's radius). The event reports the time, both keys, the kept key and the energy change
of the merger: the kinetic energy of the relative motion, the pair's mutual potential energy, and the change of the
pair's potential energy in the other bodies' field when the two are replaced by one body at their centre of mass
(review B6-G16; the running energy check must add it). ``"pass"``: point masses pass through; each entry into contact
is reported once. The law can be changed at the current moment (``set_collisions``, review UX-ui U12): to "pass", the
pairs already touching pass on; to "merge", a pair touching then merges at that moment.

Edits are transactional (review B6-G2): ``add``, ``remove``, ``set`` and ``set_many`` either complete or leave the
object exactly as it was (bit for bit) and raise; a body placed exactly on a massive body (or a massive body exactly
on any body: an infinite force) raises ``ValueError``.

Diagnostics: energy, momentum, angular momentum, centre of mass; the field at arbitrary points: acceleration,
potential and the tidal tensor T_ab = -d^2 Phi / dx_a dx_b = G sum_k m_k (3 d_a d_b - d^2 delta_ab) / d^5 (d = x_k - p).
Per step (Hermite): the predictor-corrector difference (an upper indicator, O(dt^4)) and the local error of the
velocity |a^(4)| dt^5 / 720 (the error term of the corrected trapezoidal rule the velocity corrector is; a^(4) from
the change of a^(3) between steps). The numerical error itself: a companion with a stricter accuracy (``clone``).
``state_dict`` / ``from_state_dict``: plain data (lists, floats, None); restoring and continuing is bit-identical.

Cost (measured on the CPU, NumPy, i9-9900K; ``bench``): see ``ABOUT["validity"]``. A GPU kernel pays only for
N >~ 2000 (the O(N^2) pair sums are a few dozen arrays of N x N; below that the NumPy call overhead dominates).
"""

from __future__ import annotations

import copy
import math

import numpy as np

from lfphys.i18n import T, text_of
from lfphys.codes import coded

ABOUT = {
    "layer": "core", "kind": "numerical solution",
    "title": T("The N-body problem in Newtonian gravity: close encounters, mergers, tides"),
    "statement": T("Point masses and test particles (m = 0) with stable keys: bodies are added, removed and changed "
                   "at the current moment; the time-symmetric fourth-order Hermite scheme P(EC)^n with a shared step "
                   "by Aarseth's criterion (symmetrised over the ends of the step) for close encounters, and the "
                   "fourth-order symplectic Forest–Ruth–Yoshida scheme with a constant step for long runs of quiet "
                   "systems; collisions (the moment the surfaces touch is found exactly): a merger conserving mass "
                   "and momentum, or a pass-through; energy, momentum, angular momentum, centre of mass; "
                   "acceleration, potential and tidal tensor at any points; an estimate of the local step error and a "
                   "companion run of stricter accuracy; the state is plain data, and a restore continues the "
                   "computation bit for bit."),
    "validity": T("Newtonian gravity: GR corrections of order GM/(c²r) and v²/c² (for two bodies the fuller form is "
                  "core.gravity.pn_binary, for test bodies about one mass the geodesics of core.gravity.kerr_newman: "
                  "see conflicts; for N ≥ 3 this is the most complete form in the engine, which has no post-Newtonian "
                  "N-body problem, hence the module is in the core, LAYERS.md §1); point masses without tidal "
                  "deformation or spin of the bodies; a merger is perfectly inelastic on contact (the radius of the "
                  "merged body by equal density or, for a compact body, proportional to the mass: a choice); the "
                  "Hermite scheme is not symplectic (with symmetric steps the energy error oscillates on periodic "
                  "orbits; the residual secular drift is set by the symmetrisation tolerance dt_rtol, see the "
                  "README), Yoshida-4 is symplectic but has a constant step. Cost of a step on the CPU (NumPy): see "
                  "the README"),
    "basis": [T("Makino & Aarseth, PASJ 44, 141 (1992): the Hermite scheme"),
              "Kokubo, Yoshinaga & Makino, MNRAS 297, 1067 (1998), Eqs. (1)-(12)",
              T("Hut, Makino & McMillan, ApJ 443, L93 (1995), eq. (4b): symmetrisation of the step"),
              "Nitadori & Makino, New Astron. 13, 498 (2008), Eqs. (1), (2), (5), (15)",
              "Forest & Ruth, Physica D 43, 105 (1990); Yoshida, Phys. Lett. A 150, 262 (1990); "
              "Omelyan, Mryglod & Folk, Comput. Phys. Commun. 146, 188 (2002), Eq. (8)",
              T("checks: Kepler; the Chenciner–Montgomery figure-eight (2000, initial conditions by Simó); Burrau's "
                "Pythagorean problem (Szebehely & Peters, AJ 72, 876 (1967))")],
    # the cases where the engine has the fuller form of the same law (review B6-G14): shown with the module
    "conflicts": [T("lfphys.core.gravity.pn_binary: a binary in GR has periapsis precession and an inspiral by the "
                    "emission of gravitational waves, both absent here"),
                  T("lfphys.core.gravity.kerr_newman: a test body about one mass moves on a geodesic (periapsis "
                    "precession, 43″ per century for Mercury; instability inside the ISCO; capture by the horizon), "
                    "not on a Kepler ellipse")],
}

THETA = 1.0 / (2.0 - 2.0 ** (1.0 / 3.0))
INTEGRATORS = ("hermite", "yoshida4")
POLICIES = ("merge", "pass")
_FORMAT = "lfphys.nbody/1"
_U = 2.0 ** -53


# --- the field ------------------------------------------------------------------------------------------------------
def acc_jerk(x, v, m, G, src=None, jerk=True, notself=None):
    """Acceleration (and jerk) of every body (rows of x, v) from the massive bodies ``src`` (indices; default: all
    with m > 0), NM08 Eqs. (1), (2), (5). Self pairs are skipped (``notself``: the (n, ns) float mask 1 - [i == src_j],
    computed if not given)."""
    x = np.asarray(x, float)
    n = x.shape[0]
    if src is None:
        src = np.flatnonzero(np.asarray(m) > 0.0)
    if n == 0 or len(src) == 0:
        z = np.zeros((n, 3))
        return (z, z.copy()) if jerk else z
    if notself is None:
        notself = (np.arange(n)[:, None] != np.asarray(src)[None, :]).astype(float)
    dx = x[src][None, :, :] - x[:, None, :]
    r2 = np.einsum("ijk,ijk->ij", dx, dx) + (1.0 - notself)
    if not np.all(r2 > 0.0):
        raise coded(FloatingPointError(T("two bodies at the same point (an exact collision of point masses)")),
                    "nbody.collision")
    inv_r2 = 1.0 / r2
    w = (G * np.asarray(m, float)[src]) * notself * inv_r2 * np.sqrt(inv_r2)
    a = np.einsum("ij,ijk->ik", w, dx)
    if not jerk:
        return a
    v = np.asarray(v, float)
    dv = v[src][None, :, :] - v[:, None, :]
    alpha = np.einsum("ijk,ijk->ij", dx, dv) * inv_r2
    j = np.einsum("ij,ijk->ik", w, dv) - 3.0 * np.einsum("ij,ijk->ik", w * alpha, dx)
    return a, j


def field_at(points, x, m, G, exclude=None):
    """Potential Phi, acceleration -grad Phi and tidal tensor -d^2 Phi/dx dx at points (k, 3) from the bodies (x, m),
    excluding the rows ``exclude``. Returns (phi (k,), acc (k, 3), tidal (k, 3, 3))."""
    p = np.atleast_2d(np.asarray(points, float))
    x = np.asarray(x, float)
    m = np.asarray(m, float)
    keep = m > 0.0
    if exclude is not None and len(exclude):
        keep[np.asarray(exclude, int)] = False
    xs, ms = x[keep], m[keep]
    if len(ms) == 0:
        k = p.shape[0]
        return np.zeros(k), np.zeros((k, 3)), np.zeros((k, 3, 3))
    d = xs[None, :, :] - p[:, None, :]
    d2 = np.einsum("ijk,ijk->ij", d, d)
    if np.any(d2 == 0.0):
        raise coded(FloatingPointError(T("a field point coincides with a massive body")), "nbody.collision")
    inv = 1.0 / np.sqrt(d2)
    gm = G * ms[None, :]
    phi = -np.sum(gm * inv, axis=1)
    w3 = gm * inv ** 3
    acc = np.einsum("ij,ijk->ik", w3, d)
    w5 = 3.0 * gm * inv ** 5
    tid = np.einsum("ij,ija,ijb->iab", w5, d, d) - np.sum(w3, axis=1)[:, None, None] * np.eye(3)[None]
    return phi, acc, tid


def _aarseth(A, J, S, C, eta):
    """Aarseth's tau per body from the magnitudes |a|, |a'|, |a''|, |a'''| (inf where undefined)."""
    num = A * S + J * J
    den = J * C + S * S
    ok = (den > 0.0) & (num > 0.0)
    return np.where(ok, np.sqrt(eta * num / np.where(ok, den, 1.0)), np.inf)


def _quintic_hermite(s, h, y0, d0, e0, y1, d1, e1):
    """Value and derivative at s in [0, h] of the quintic with y, y', y'' = (y0, d0, e0) at 0 and (y1, d1, e1) at h."""
    u = s / h
    u2, u3 = u * u, u * u * u
    u4, u5 = u3 * u, u3 * u2
    h0 = 1 - 10 * u3 + 15 * u4 - 6 * u5
    h1 = u - 6 * u3 + 8 * u4 - 3 * u5
    h2 = 0.5 * u2 - 1.5 * u3 + 1.5 * u4 - 0.5 * u5
    h3 = 10 * u3 - 15 * u4 + 6 * u5
    h4 = -4 * u3 + 7 * u4 - 3 * u5
    h5 = 0.5 * u3 - u4 + 0.5 * u5
    g0 = (-30 * u2 + 60 * u3 - 30 * u4) / h
    g1 = (1 - 18 * u2 + 32 * u3 - 15 * u4) / h
    g2 = (u - 4.5 * u2 + 6 * u3 - 2.5 * u4) / h
    g3 = (30 * u2 - 60 * u3 + 30 * u4) / h
    g4 = (-12 * u2 + 28 * u3 - 15 * u4) / h
    g5 = (1.5 * u2 - 4 * u3 + 2.5 * u4) / h
    y = h0 * y0 + h1 * h * d0 + h2 * h * h * e0 + h3 * y1 + h4 * h * d1 + h5 * h * h * e1
    dy = g0 * y0 + g1 * h * d0 + g2 * h * h * e0 + g3 * y1 + g4 * h * d1 + g5 * h * h * e1
    return y, dy


class _Step:
    """A computed step from the committed state: its length, end state, continuous output, contacts inside it."""
    __slots__ = ("dt", "x1", "v1", "a1", "j1", "c2", "c3", "tau", "passes", "residual", "pc", "contacts")

    def __init__(self, dt):
        self.dt = dt
        self.contacts = []
        self.tau = None
        self.passes = 0
        self.residual = (0.0, 0.0)
        self.pc = 0.0
        self.j1 = None
        self.c2 = None
        self.c3 = None


def _turn(v0, v1):
    """Angle between the rows of v0 and v1 (0 where either is zero)."""
    c = np.einsum("ij,ij->i", v0, v1)
    s = np.linalg.norm(np.cross(v0, v1), axis=1)
    return np.arctan2(s, c)


def _speed_change(v0, v1):
    """| |v1| - |v0| | / max(|v0|, |v1|) per row (0 where both are zero)."""
    a, b = np.linalg.norm(v0, axis=1), np.linalg.norm(v1, axis=1)
    m = np.maximum(a, b)
    return np.abs(b - a) / np.where(m > 0, m, 1.0)


class Samples:
    """Points of the computed trajectories for drawing them (review UX-ui U2: p01 joined one point per frame by
    straight chords, so Mercury was drawn as a pentagon). ``NBody.advance(t, samples=s)`` appends to ``s.points``, in
    time order, tuples (t, keys, x (n, 3), v (n, 3), restart): the continuous output of the integrator (exactly the
    trajectory the world shows) on a grid inside every step, uniform in the step and fine enough that between two
    consecutive points no body's direction of motion turns by more than ``turn`` (radians), no body's speed changes
    by more than the fraction ``dspeed`` and no body moves farther than ``length`` (at most ``max_per_step`` points in
    a step); the grid belongs to the step, not to the call, so the points do not depend on how the caller slices time
    (the end of a call is not a point). A merger adds the touching state at the contact and then the merged state at
    the same time with ``restart`` = the kept key (its state jumps there); otherwise ``restart`` is empty. A free
    system (straight lines) gives no points unless ``length`` is finite."""

    def __init__(self, turn: float = math.radians(10.0), dspeed: float = 0.1, length: float = math.inf,
                 max_per_step: int = 64):
        if not (turn > 0 and dspeed > 0 and length > 0 and max_per_step >= 1):
            raise ValueError("turn, dspeed, length > 0 and max_per_step >= 1")
        self.turn, self.dspeed, self.length, self.max_per_step = float(turn), float(dspeed), float(length), int(max_per_step)
        self.points: list = []

    def _count(self, x0, v0, x1, v1) -> int:
        """Equal parts of an interval that keep every body within the limits (from its ends)."""
        if len(x0) == 0:
            return 1
        need = max(float(np.max(_turn(v0, v1))) / self.turn, float(np.max(_speed_change(v0, v1))) / self.dspeed,
                   float(np.max(np.linalg.norm(x1 - x0, axis=1))) / self.length)
        return int(min(max(math.ceil(need - 1e-12), 1), self.max_per_step))


def _key_ok(k):
    if isinstance(k, bool) or not isinstance(k, (int, str)):
        raise TypeError("a body key must be an int or a str")
    return k


class NBody:
    """Newtonian N bodies with stable keys (see the module docstring).

    NBody(G=1.0, *, integrator="hermite", eta=0.02, n_iter=3, dt_rtol=1e-4, max_passes=6, eta_start=0.01,
          dt=None, dt_max=inf, collisions="merge", t=0.0)
    """

    def __init__(self, G=1.0, *, integrator="hermite", eta=0.02, n_iter=3, dt_rtol=1e-4, max_passes=6,
                 eta_start=0.01, dt=None, dt_max=math.inf, collisions="merge", t=0.0):
        if integrator not in INTEGRATORS:
            raise ValueError(f"integrator must be one of {INTEGRATORS}")
        if collisions not in POLICIES:
            raise ValueError(f"collisions must be one of {POLICIES}")
        if integrator == "yoshida4" and not (dt is not None and dt > 0 and math.isfinite(dt)):
            raise ValueError("yoshida4 needs a fixed step dt > 0")
        if not (G > 0 and eta > 0 and n_iter >= 1 and dt_rtol > 0 and max_passes >= 1 and eta_start > 0
                and dt_max > 0):
            raise ValueError("G, eta, eta_start, dt_rtol, dt_max must be > 0; n_iter, max_passes >= 1")
        self.G = float(G)
        self.integrator = integrator
        self.eta = float(eta)
        self.n_iter = int(n_iter)
        self.dt_rtol = float(dt_rtol)
        self.max_passes = int(max_passes)
        self.eta_start = float(eta_start)
        self.dt = None if dt is None else float(dt)
        self.dt_max = float(dt_max)
        self.collisions = collisions
        self._keys: list = []
        self._x = np.zeros((0, 3))
        self._v = np.zeros((0, 3))
        self._m = np.zeros(0)
        self._R = np.zeros(0)
        self._rpm = np.zeros(0)  # radius per mass of compact bodies (0: the radius is the body's own)
        self._a = np.zeros((0, 3))
        self._j = np.zeros((0, 3))
        self._t = float(t)
        self._t_out = float(t)
        self._tau_prev = None   # (h_start, h_end) of the last regular step: the guess of the next
        self._dt_prev = None
        self._c3_prev = None    # a^(3) of the last step: a^(4) for the local error estimate
        self._sigma = 0.0       # slope dS/d(dt) of the symmetric rule, carried between steps (Newton on dt)
        self._mask = None       # (massive rows, not-self mask) for the force sums
        self._sigma_new = 0.0
        self._next_key = 0
        self._overlap: set = set()
        self._cache = None
        self._stats = {"steps": 0, "force_evals": 0, "passes": 0, "merges": 0, "contacts": 0,
                       "last_dt": 0.0, "last_passes": 0, "last_residual_x": 0.0, "last_residual_v": 0.0,
                       "last_pc": 0.0, "local_error_v": float("nan"), "local_error_x": float("nan"),
                       "unconverged_steps": 0}

    # --- bodies --------------------------------------------------------------------------------------------------
    @property
    def t(self) -> float:
        """The world time: the moment the state is shown at."""
        return self._t_out

    @property
    def keys(self) -> list:
        return list(self._keys)

    @property
    def n(self) -> int:
        return len(self._keys)

    def has(self, key) -> bool:
        return key in self._keys

    @property
    def step_size(self) -> float:
        """The length of the last committed regular step (0 before the first): cheap, unlike ``diagnostics``."""
        return float(self._stats["last_dt"])

    @property
    def step_count(self) -> int:
        """Steps committed so far (as ``diagnostics()["steps"]``, without its O(N^2) energies)."""
        return int(self._stats["steps"])

    def _row(self, key) -> int:
        try:
            return self._keys.index(key)
        except ValueError:
            raise KeyError(f"no body with key {key!r}") from None

    def add(self, x, v=(0.0, 0.0, 0.0), m=0.0, radius=0.0, key=None, radius_per_mass=0.0):
        """Add a body at the current time; returns its key (a new int if none is given). ``radius_per_mass`` k > 0:
        a compact body whose radius is k m (now, after a change of its mass and after a merger; ``radius`` must then
        be left 0). Refused (``ValueError``, nothing changed) where it would sit exactly on a massive body, or, being
        massive, on any body."""
        x = self._vec(x)
        v = self._vec(v)
        m, radius, rpm = float(m), float(radius), float(radius_per_mass)
        if not all(z >= 0.0 and math.isfinite(z) for z in (m, radius, rpm)):
            raise coded(ValueError(T("mass, radius and radius per mass must be finite and ≥ 0")), "nbody.body")
        if rpm > 0.0:
            if radius != 0.0:
                raise coded(ValueError(T("a compact body's radius is its radius per mass × m: give radius 0")),
                            "nbody.body")
            radius = rpm * m
        if key is None:
            while self._next_key in self._keys:
                self._next_key += 1
            key = self._next_key
            self._next_key += 1
        _key_ok(key)
        if key in self._keys:
            raise KeyError(f"key {key!r} exists")

        def apply():
            self._keys.append(key)
            self._x = np.vstack([self._x, x[None]])
            self._v = np.vstack([self._v, v[None]])
            self._m = np.append(self._m, m)
            self._R = np.append(self._R, radius)
            self._rpm = np.append(self._rpm, rpm)
        self._transaction(apply, f"the body {key!r} was not added")
        return key

    def remove(self, key):
        """Remove a body at the current time."""
        i = self._row(key)

        def apply():
            self._drop(i)
            self._overlap = {p for p in self._overlap if key not in p}
        self._transaction(apply, f"the body {key!r} was not removed")

    def set(self, key, *, x=None, v=None, m=None, radius=None, radius_per_mass=None):
        """Change a body's position, velocity, mass, radius or radius per mass at the current time (the others
        untouched); refused as ``add`` (nothing changed)."""
        self.set_many({key: {"x": x, "v": v, "m": m, "radius": radius, "radius_per_mass": radius_per_mass}})

    def set_many(self, changes: dict):
        """Several bodies changed at the current time in one edit (one force evaluation; review B6-G6: a body added on
        a two-body circular orbit gives the others its reflex velocity): ``changes`` = {key: {x?, v?, m?, radius?,
        radius_per_mass?}} (None or absent: unchanged). All or nothing: a refusal leaves every body as it was."""
        plan = []
        for key, ch in changes.items():
            i = self._row(key)
            ch = {k: val for k, val in (ch or {}).items() if val is not None}
            bad = set(ch) - {"x", "v", "m", "radius", "radius_per_mass"}
            if bad:
                raise ValueError(f"unknown body fields {sorted(bad)}")
            for k in ("x", "v"):
                if k in ch:
                    ch[k] = self._vec(ch[k])
            for k in ("m", "radius", "radius_per_mass"):
                if k in ch:
                    ch[k] = float(ch[k])
                    if not (ch[k] >= 0.0 and math.isfinite(ch[k])):
                        name = {"m": T("the mass"), "radius": T("the radius"),
                                "radius_per_mass": T("the radius per mass")}[k]
                        raise coded(ValueError(T("{what:cap} must be finite and ≥ 0", what=name)), "nbody.body")
            rpm = ch.get("radius_per_mass", float(self._rpm[i]))
            if rpm > 0.0 and "radius" in ch:
                raise coded(ValueError(T("a compact body's radius is its radius per mass × m: change m or the "
                                         "radius per mass")), "nbody.body")
            plan.append((i, ch))

        def apply():
            for i, ch in plan:
                if "x" in ch:
                    self._x[i] = ch["x"]
                if "v" in ch:
                    self._v[i] = ch["v"]
                if "m" in ch:
                    self._m[i] = ch["m"]
                if "radius" in ch:
                    self._R[i] = ch["radius"]
                if "radius_per_mass" in ch:
                    self._rpm[i] = ch["radius_per_mass"]
                if self._rpm[i] > 0.0:
                    self._R[i] = self._rpm[i] * self._m[i]
        self._transaction(apply, "the change was not applied")

    _STATE = ("_keys", "_x", "_v", "_m", "_R", "_rpm", "_a", "_j", "_t", "_t_out", "_tau_prev", "_dt_prev", "_c3_prev",
              "_sigma", "_sigma_new", "_mask", "_next_key", "_overlap", "_cache", "_stats")

    def _transaction(self, apply, what):
        """Sync to the world time, apply the change, recompute the forces; on any failure restore the whole state
        as it was before the call (bit for bit) and re-raise (coincident points as ValueError: a refusal)."""
        snap = {k: copy.deepcopy(getattr(self, k)) for k in self._STATE}
        try:
            self._sync()
            apply()
            self._edited()
        except FloatingPointError as e:
            for k, val in snap.items():
                setattr(self, k, val)
            raise coded(ValueError(T("{reason}: {what}", reason=text_of(e), what=what)), "nbody.refused") from e
        except BaseException:
            for k, val in snap.items():
                setattr(self, k, val)
            raise

    def reverse(self):
        """Time reversal of the state at the current time: v -> -v (the motion retraces itself)."""
        self._sync()
        self._v = -self._v
        if self._j is not None:
            self._j = -self._j
        if self._tau_prev is not None:
            self._tau_prev = (self._tau_prev[1], self._tau_prev[0])
        self._c3_prev = None
        self._cache = None

    def body(self, key) -> dict:
        """State of one body at the current time: x, v (lists), m, radius."""
        i = self._row(key)
        x, v = self._out()
        return {"key": key, "x": x[i].tolist(), "v": v[i].tolist(), "m": float(self._m[i]),
                "radius": float(self._R[i]), "radius_per_mass": float(self._rpm[i])}

    def positions(self) -> np.ndarray:
        """(n, 3) positions at the current time, rows in ``keys`` order."""
        return self._out()[0].copy()

    def velocities(self) -> np.ndarray:
        return self._out()[1].copy()

    def masses(self) -> np.ndarray:
        return self._m.copy()

    def radii(self) -> np.ndarray:
        return self._R.copy()

    # --- time ----------------------------------------------------------------------------------------------------
    def advance(self, t_target, samples: "Samples | None" = None) -> list:
        """Advance the world to time t_target (>= t); returns the events met on the way (dicts, in time order).
        ``samples``: a ``Samples`` that receives points of the trajectories on the way (for drawing; the motion is
        the same with or without it)."""
        t_target = float(t_target)
        if not t_target >= self._t_out:
            raise ValueError(f"time runs forward: t_target {t_target} < t {self._t_out}")
        events: list = []
        while True:
            if self._free():
                h = t_target - self._t
                if samples is not None:
                    self._sample_free(samples, t_target)
                self._x = self._x + h * self._v
                self._t = self._t_out = t_target
                self._cache = None
                return events
            st = self._tentative()
            if samples is not None:
                sm = self._merge_s(st, t_target)
                self._sample_step(samples, st, min(st.dt, t_target - self._t) if sm is None else sm, sm)
            if self._handle_contacts(st, t_target, events):
                if samples is not None and events and events[-1].get("kind") == "merge":
                    samples.points.append((self._t, tuple(self._keys), self._x.copy(), self._v.copy(),
                                           frozenset([events[-1]["key"]])))
                continue
            if self._t + st.dt <= t_target:
                self._commit(st)
                continue
            self._t_out = t_target
            return events

    def _merge_s(self, st, t_until):
        """s of the first contact in the step that merges two bodies by t_until (None: none)."""
        if self.collisions != "merge":
            return None
        for s, _, _ in st.contacts:
            return s if self._t + s <= t_until else None
        return None

    def _sample_step(self, samples, st, s_hi, contact=None):
        """The step's grid points in (s_lo, s_hi], s_lo the part already shown; the contact itself as a point."""
        s_lo = self._t_out - self._t
        k = samples._count(self._x, self._v, st.x1, st.v1)
        grid = [q * st.dt / k for q in range(1, k + 1)]
        ss = [s for s in grid if s_lo < s <= s_hi * (1.0 + 1e-15)]
        if contact is not None and contact > s_lo and (not ss or abs(ss[-1] - contact) > 1e-15 * st.dt):
            ss = [s for s in ss if s < contact] + [contact]
        keys = tuple(self._keys)
        for s in ss:
            x, v = self._dense(st, min(s, st.dt))
            samples.points.append((self._t + s, keys, np.array(x), np.array(v), frozenset()))

    def _sample_free(self, samples, t_target):
        """Straight motion from the shown time to t_target: points only where ``length`` asks for them."""
        h0, h1 = self._t_out - self._t, t_target - self._t
        if not math.isfinite(samples.length) or h1 <= h0 or self.n == 0:
            return
        x0 = self._x + h0 * self._v
        k = samples._count(x0, self._v, self._x + h1 * self._v, self._v)
        keys = tuple(self._keys)
        for q in range(1, k + 1):
            h = h0 + (h1 - h0) * q / k
            samples.points.append((self._t + h, keys, self._x + h * self._v, self._v.copy(), frozenset()))

    def set_collisions(self, policy: str):
        """Change the collision law at the current moment (review UX-ui U12): "merge" or "pass". Switching to "pass"
        marks the pairs already in contact (they pass through from now on; their entry is not reported again);
        switching to "merge" merges a pair in contact at once (at the next advance, at the current time)."""
        if policy not in POLICIES:
            raise ValueError(f"collisions must be one of {POLICIES}")
        if policy == self.collisions:
            return
        self._sync()
        self.collisions = policy
        if policy == "pass":
            self._update_overlap()
        else:
            self._overlap = set()
        self._cache = None

    def step(self, n: int = 1) -> list:
        """Commit n of the integrator's own steps from the current time (the world time moves to their end)."""
        events: list = []
        self._sync()
        for _ in range(int(n)):
            if self._free():
                raise RuntimeError("free motion has no step of its own")
            st = self._tentative()
            if self._handle_contacts(st, self._t + st.dt, events):
                continue
            self._commit(st)
        return events

    # --- diagnostics ---------------------------------------------------------------------------------------------
    def kinetic_energy(self) -> float:
        v = self._out()[1]
        return float(0.5 * np.sum(self._m * np.einsum("ij,ij->i", v, v)))

    def potential_energy(self) -> float:
        x = self._out()[0]
        src = np.flatnonzero(self._m > 0.0)
        if len(src) < 2:
            return 0.0
        xs, ms = x[src], self._m[src]
        d = xs[:, None, :] - xs[None, :, :]
        r = np.sqrt(np.einsum("ijk,ijk->ij", d, d))
        iu = np.triu_indices(len(src), 1)
        return float(-self.G * np.sum(ms[iu[0]] * ms[iu[1]] / r[iu]))

    def energy(self) -> float:
        """Total energy (kinetic + pair potential of the massive bodies) at the current time."""
        return self.kinetic_energy() + self.potential_energy()

    def momentum(self) -> np.ndarray:
        return np.sum(self._m[:, None] * self._out()[1], axis=0)

    def angular_momentum(self, origin=(0.0, 0.0, 0.0)) -> np.ndarray:
        x, v = self._out()
        return np.sum(self._m[:, None] * np.cross(x - np.asarray(origin, float), v), axis=0)

    def total_mass(self) -> float:
        return float(np.sum(self._m))

    def center_of_mass(self):
        """(position, velocity) of the centre of mass of the massive bodies (None, None without mass)."""
        M = self.total_mass()
        if M <= 0.0:
            return None, None
        x, v = self._out()
        return np.sum(self._m[:, None] * x, axis=0) / M, np.sum(self._m[:, None] * v, axis=0) / M

    def potential_at(self, points, exclude=()) -> np.ndarray:
        return self._field(points, exclude)[0]

    def acceleration_at(self, points, exclude=()) -> np.ndarray:
        """Gravitational acceleration -grad Phi at points (k, 3) (bodies with keys in ``exclude`` left out)."""
        return self._field(points, exclude)[1]

    def tidal_tensor_at(self, points, exclude=()) -> np.ndarray:
        """Tidal tensor -d^2 Phi / dx_a dx_b at points: (k, 3, 3), symmetric, trace 0 off the bodies."""
        return self._field(points, exclude)[2]

    def _field(self, points, exclude):
        rows = [self._row(k) for k in exclude]
        return field_at(points, self._out()[0], self._m, self.G, rows)

    def diagnostics(self) -> dict:
        """Running checks and the cost so far: energy, momentum, angular momentum, centre of mass; the last step's
        length, passes, corrector residual (P(EC)^n convergence), predictor-corrector difference and local error
        estimates (velocity: |a^(4)| dt^5/720, position: dt/2 times that)."""
        com = self.center_of_mass()
        d = dict(self._stats)
        d.update({"t": self._t_out, "t_committed": self._t, "n": self.n, "n_massive": int(np.sum(self._m > 0)),
                  "energy": self.energy(), "momentum": self.momentum().tolist(),
                  "angular_momentum": self.angular_momentum().tolist(),
                  "com_x": None if com[0] is None else com[0].tolist(),
                  "com_v": None if com[1] is None else com[1].tolist(),
                  "integrator": self.integrator})
        return d

    # --- state ---------------------------------------------------------------------------------------------------
    def state_dict(self) -> dict:
        """Plain data of the whole state (lists, floats, ints, str, None): restoring continues bit-identically."""
        def f(z):
            return None if z is None or not math.isfinite(z) else float(z)
        return {
            "format": _FORMAT, "G": self.G, "integrator": self.integrator, "eta": self.eta, "n_iter": self.n_iter,
            "dt_rtol": self.dt_rtol, "max_passes": self.max_passes, "eta_start": self.eta_start, "dt": self.dt,
            "dt_max": f(self.dt_max), "collisions": self.collisions, "t": self._t, "t_out": self._t_out,
            "keys": list(self._keys), "x": self._x.tolist(), "v": self._v.tolist(), "m": self._m.tolist(),
            "radius": self._R.tolist(), "radius_per_mass": self._rpm.tolist(), "a": self._a.tolist(),
            "j": None if self._j is None else self._j.tolist(),
            "tau_prev": None if self._tau_prev is None else [f(self._tau_prev[0]), f(self._tau_prev[1])],
            "dt_prev": self._dt_prev, "c3_prev": None if self._c3_prev is None else self._c3_prev.tolist(),
            "sigma": self._sigma, "sigma_new": self._sigma_new,
            "next_key": self._next_key, "overlap": [sorted(p, key=str) for p in self._overlap],
            "stats": dict(self._stats),
        }

    @classmethod
    def from_state_dict(cls, d: dict, **overrides) -> "NBody":
        """Rebuild from ``state_dict`` data. Without ``overrides`` the object continues bit-identically. With
        ``overrides`` (eta, n_iter, dt_rtol, max_passes, eta_start, dt, dt_max, integrator, collisions) it is a
        companion: the same physical state at the world time (a step of the original scheme ending there is committed
        first), then the new settings from their start rule."""
        if d.get("format") != _FORMAT:
            raise ValueError(f"not an {_FORMAT} state")
        kw = {k: d[k] for k in ("G", "integrator", "eta", "n_iter", "dt_rtol", "max_passes", "eta_start", "dt",
                                "collisions")}
        kw["dt_max"] = math.inf if d["dt_max"] is None else d["dt_max"]
        o = cls(t=d["t"], **kw)
        o._load(d)
        if not overrides:
            return o
        o._sync()
        kw.update(overrides)
        c = cls(t=o._t, **kw)
        c._keys, c._x, c._v, c._m, c._R = list(o._keys), o._x.copy(), o._v.copy(), o._m.copy(), o._R.copy()
        c._rpm = o._rpm.copy()
        c._next_key, c._overlap, c._stats = o._next_key, set(o._overlap), dict(o._stats)
        c._edited(keep_overlap=True)
        return c

    def _load(self, d):
        self._t_out = float(d["t_out"])
        self._keys = list(d["keys"])
        n = len(self._keys)
        self._x = np.array(d["x"], float).reshape(n, 3)
        self._v = np.array(d["v"], float).reshape(n, 3)
        self._m = np.array(d["m"], float).reshape(n)
        self._R = np.array(d["radius"], float).reshape(n)
        self._rpm = np.array(d.get("radius_per_mass") or [0.0] * n, float).reshape(n)
        self._a = np.array(d["a"], float).reshape(n, 3)
        self._j = None if d["j"] is None else np.array(d["j"], float).reshape(n, 3)
        tp = d["tau_prev"]
        self._tau_prev = None if tp is None else tuple(math.inf if z is None else float(z) for z in tp)
        self._dt_prev = d["dt_prev"]
        self._c3_prev = None if d["c3_prev"] is None else np.array(d["c3_prev"], float).reshape(n, 3)
        self._sigma = float(d["sigma"])
        self._sigma_new = float(d["sigma_new"])
        self._next_key = int(d["next_key"])
        self._overlap = {frozenset(p) for p in d["overlap"]}
        self._stats = dict(d["stats"])
        self._mask = None

    def clone(self, **overrides) -> "NBody":
        """An independent copy at the current state; ``overrides`` as in ``from_state_dict`` (a companion)."""
        return NBody.from_state_dict(self.state_dict(), **overrides)

    # --- internals: state ----------------------------------------------------------------------------------------
    @staticmethod
    def _vec(z):
        z = np.asarray(z, float).reshape(3)
        if not np.all(np.isfinite(z)):
            raise coded(ValueError(T("a vector with non-finite components")), "nbody.body")
        return z

    def _src(self):
        return np.flatnonzero(self._m > 0.0)

    def _force(self, x, v, jerk=True):
        self._stats["force_evals"] += 1
        if self._mask is None:
            src = self._src()
            self._mask = (src, (np.arange(self.n)[:, None] != src[None, :]).astype(float))
        return acc_jerk(x, v, self._m, self.G, self._mask[0], jerk=jerk, notself=self._mask[1])

    def _free(self) -> bool:
        ns = int(np.sum(self._m > 0.0))
        return ns == 0 or self.n <= 1

    def _edited(self, keep_overlap=False):
        """After a change of the bodies: forces at the committed state, the step restarts from its start rule."""
        self._mask = None
        if self.integrator == "hermite":
            self._a, self._j = self._force(self._x, self._v)
        else:
            self._a = self._force(self._x, self._v, jerk=False)
            self._j = None
        self._tau_prev = None
        self._dt_prev = None
        self._c3_prev = None
        self._sigma = 0.0
        self._cache = None
        if not keep_overlap:
            self._overlap = {p for p in self._overlap if all(k in self._keys for k in p)}

    def _drop(self, i):
        del self._keys[i]
        self._x = np.delete(self._x, i, axis=0)
        self._v = np.delete(self._v, i, axis=0)
        self._m = np.delete(self._m, i)
        self._R = np.delete(self._R, i)
        self._rpm = np.delete(self._rpm, i)

    def _sync(self):
        """Make the world time the committed time (before an edit): the state there is the current step's continuous
        output - exactly what is shown - so an edit leaves every other body as it is."""
        if self._t_out > self._t:
            h = self._t_out - self._t
            if self._free():
                self._x = self._x + h * self._v
                self._t = self._t_out
            else:
                self._land(h)
        self._cache = None

    def _land(self, s):
        """Commit the continuous output at s (0 < s <= dt) of the current step; forces there; the step rule keeps
        its last values as the guess."""
        st = self._tentative()
        x, v = self._dense(st, s)
        self._x, self._v = np.array(x), np.array(v)
        self._t = self._t + s
        self._t_out = max(self._t_out, self._t)
        self._mask = None
        if self.integrator == "hermite":
            self._a, self._j = self._force(self._x, self._v)
        else:
            self._a = self._force(self._x, self._v, jerk=False)
        self._c3_prev = None
        if self.collisions == "pass":
            self._update_overlap()
        self._cache = None

    def _out(self):
        """(x, v) at the world time."""
        if self._t_out == self._t or self._free():
            if self._t_out != self._t:
                h = self._t_out - self._t
                return self._x + h * self._v, self._v
            return self._x, self._v
        st = self._tentative()
        return self._dense(st, self._t_out - self._t)

    # --- internals: steps ----------------------------------------------------------------------------------------
    def _start_guess(self):
        a, j = self._a, self._j
        A = np.linalg.norm(a, axis=1)
        guesses = []
        if j is not None:
            J = np.linalg.norm(j, axis=1)
            ok = (J > 0) & (A > 0)
            if np.any(ok):
                guesses.append(np.min(A[ok] / J[ok]))
        src = self._src()
        d = self._x[:, None, :] - self._x[src][None, :, :]
        r = np.sqrt(np.einsum("ijk,ijk->ij", d, d))
        r = np.where(np.arange(self.n)[:, None] == src[None, :], np.inf, r)
        dmin = np.min(r, axis=1)
        ok = (A > 0) & np.isfinite(dmin)
        if np.any(ok):
            guesses.append(np.min(np.sqrt(dmin[ok] / A[ok])))
        g = self.eta_start * min(guesses) if guesses else 1.0
        return min(g, self.dt_max)

    def _hermite_try(self, dt, n_iter=None):
        n_iter = self.n_iter if n_iter is None else n_iter
        x0, v0, a0, j0 = self._x, self._v, self._a, self._j
        x1 = x0 + dt * (v0 + dt * (0.5 * a0 + dt * j0 / 6.0))
        v1 = v0 + dt * (a0 + 0.5 * dt * j0)
        xp = x1
        a1 = j1 = None
        x_prev = v_prev = None
        for _ in range(n_iter):
            a1, j1 = self._force(x1, v1)
            x_prev, v_prev = x1, v1
            v1 = v0 + (0.5 * dt) * (a1 + a0) - (dt * dt / 12.0) * (j1 - j0)
            x1 = x0 + (0.5 * dt) * (v1 + v0) - (dt * dt / 10.0) * (a1 - a0) + (dt * dt * dt / 120.0) * (j1 + j0)
        res = (float(np.max(np.abs(x1 - x_prev))), float(np.max(np.abs(v1 - v_prev))))
        st = _Step(dt)
        st.x1, st.v1, st.a1, st.j1 = x1, v1, a1, j1
        st.c2 = (-6.0 * (a0 - a1) - dt * (4.0 * j0 + 2.0 * j1)) / (dt * dt)
        st.c3 = (12.0 * (a0 - a1) + 6.0 * dt * (j0 + j1)) / (dt * dt * dt)
        st.residual = res
        st.pc = float(np.max(np.abs(x1 - xp)))
        return st

    def _tau_ends(self, st):
        z = np.stack((self._a, self._j, st.c2, st.c3, st.a1, st.j1, st.c2 + st.c3 * st.dt))
        A0, J0, S0, C, A1, J1, S1 = np.sqrt(np.einsum("kij,kij->ki", z, z))
        return float(np.min(_aarseth(A0, J0, S0, C, self.eta))), float(np.min(_aarseth(A1, J1, S1, C, self.eta)))

    def _fr(self, h):
        x, v, a = self._x, self._v, self._a
        v = v + (0.5 * THETA * h) * a
        x = x + (THETA * h) * v
        a = self._force(x, v, jerk=False)
        v = v + (0.5 * (1.0 - THETA) * h) * a
        x = x + ((1.0 - 2.0 * THETA) * h) * v
        a = self._force(x, v, jerk=False)
        v = v + (0.5 * (1.0 - THETA) * h) * a
        x = x + (THETA * h) * v
        a = self._force(x, v, jerk=False)
        v = v + (0.5 * THETA * h) * a
        st = _Step(h)
        st.x1, st.v1, st.a1 = x, v, a
        return st

    def _tentative(self) -> _Step:
        if self._cache is not None:
            return self._cache
        if self.integrator == "yoshida4":
            st = self._fr(min(self.dt, self.dt_max))
            st.passes = 1
        else:
            if self._tau_prev is None or not all(math.isfinite(z) for z in self._tau_prev):
                dt = self._start_guess()
            else:
                h0, h1 = self._tau_prev
                dt = h1 + 0.5 * (h1 - h0)
                if self._dt_prev:
                    dt = min(max(dt, 0.5 * self._dt_prev), 2.0 * self._dt_prev)
                dt = min(dt, self.dt_max)
            st = None
            sigma = self._sigma
            prev = None
            for p in range(self.max_passes):
                # a cheap first estimate of the rule, only when a later pass can correct it (review B6-G9)
                n = 1 if (p == 0 and self.n_iter > 1 and self.max_passes > 1) else self.n_iter
                st = self._hermite_try(dt, n)
                st.tau = self._tau_ends(st)
                st.passes = p + 1
                sym = min(self.dt_max, 0.5 * (st.tau[0] + st.tau[1]))
                if not math.isfinite(sym):
                    sym = dt
                F = sym - dt
                if n == self.n_iter and abs(F) <= self.dt_rtol * dt:
                    break
                if prev is not None and dt != prev[0]:
                    sigma = min(max(1.0 + (F - prev[1]) / (dt - prev[0]), -0.9), 0.9)  # S'(dt), secant
                prev = (dt, F)
                dt = min(max(dt + F / (1.0 - sigma), 0.25 * dt), 4.0 * dt)  # Newton on dt = S(dt)
            else:
                self._stats["unconverged_steps"] += 1
            self._sigma_new = sigma
        st.contacts = self._contacts(st)
        self._cache = st
        return st

    def _dense(self, st, s, rows=slice(None)):
        """(x, v) of the bodies (``rows``) at s in [0, dt] after the committed state."""
        if self.integrator == "hermite":
            x0, v0, a0, j0 = self._x[rows], self._v[rows], self._a[rows], self._j[rows]
            c2, c3 = st.c2[rows], st.c3[rows]
            x = x0 + s * (v0 + s * (0.5 * a0 + s * (j0 / 6.0 + s * (c2 / 24.0 + s * c3 / 120.0))))
            v = v0 + s * (a0 + s * (0.5 * j0 + s * (c2 / 6.0 + s * c3 / 24.0)))
            return x, v
        return _quintic_hermite(s, st.dt, self._x[rows], self._v[rows], self._a[rows], st.x1[rows], st.v1[rows],
                                st.a1[rows])

    def _commit(self, st, regular=True):
        if self.integrator == "hermite" and regular:
            if self._c3_prev is not None and self._dt_prev:
                a4 = np.linalg.norm(st.c3 - self._c3_prev, axis=1) / (0.5 * (st.dt + self._dt_prev))
                ev = float(np.max(a4)) * st.dt ** 5 / 720.0
                self._stats["local_error_v"] = ev
                self._stats["local_error_x"] = 0.5 * st.dt * ev
            self._c3_prev = st.c3
            self._tau_prev = st.tau
            self._dt_prev = st.dt
            self._sigma = self._sigma_new
        self._x, self._v, self._a = st.x1, st.v1, st.a1
        if self.integrator == "hermite":
            self._j = st.j1
        self._t = self._t + st.dt
        self._t_out = max(self._t_out, self._t)
        s = self._stats
        s["steps"] += 1
        s["passes"] += st.passes
        s["last_dt"], s["last_passes"] = st.dt, st.passes
        s["last_residual_x"], s["last_residual_v"] = st.residual
        s["last_pc"] = st.pc
        if self.collisions == "pass":
            self._update_overlap()
        self._cache = None

    # --- internals: collisions -----------------------------------------------------------------------------------
    def _pairs(self):
        n = self.n
        if n < 2:
            return np.zeros(0, int), np.zeros(0, int)
        i, j = np.triu_indices(n, 1)
        ok = ((self._m[i] > 0) | (self._m[j] > 0)) & ((self._R[i] + self._R[j]) > 0)
        return i[ok], j[ok]

    def _update_overlap(self):
        i, j = self._pairs()
        if len(i) == 0:
            self._overlap = set()
            return
        d = np.linalg.norm(self._x[j] - self._x[i], axis=1)
        inside = d <= self._R[i] + self._R[j]
        self._overlap = {frozenset((self._keys[a], self._keys[b])) for a, b in zip(i[inside], j[inside])}

    def _contacts(self, st):
        """Entries into contact inside the step: sorted list of (s, i, j) (s from the committed time)."""
        if not np.any(self._R > 0.0):
            return []
        i, j = self._pairs()
        if len(i) == 0:
            return []
        dt = st.dt
        R = self._R[i] + self._R[j]
        d0 = self._x[j] - self._x[i]
        d1 = st.x1[j] - st.x1[i]
        e = d1 - d0
        ee = np.einsum("ij,ij->i", e, e)
        with np.errstate(divide="ignore", invalid="ignore"):
            u = np.clip(np.where(ee > 0, -np.einsum("ij,ij->i", d0, e) / ee, 0.0), 0.0, 1.0)
        chord = np.linalg.norm(d0 + u[:, None] * e, axis=1)
        arel = np.maximum(np.linalg.norm(self._a[j] - self._a[i], axis=1),
                          np.linalg.norm(st.a1[j] - st.a1[i], axis=1))
        margin = 0.5 * arel * dt * dt + 1e-12 * (np.linalg.norm(d0, axis=1) + R)
        cand = np.flatnonzero(chord <= R + margin)
        out = []
        K = 32
        grid = np.linspace(0.0, dt, K + 1)
        for c in cand:
            a_, b_ = int(i[c]), int(j[c])
            rr = float(R[c])

            rows = np.array([a_, b_])

            def sep(s, rows=rows):
                x, v = self._dense(st, s, rows)
                return x[1] - x[0], v[1] - v[0]

            g = np.empty(K + 1)
            gd = np.empty(K + 1)
            for q, s in enumerate(grid):
                dd, dv = sep(s)
                g[q] = math.sqrt(float(dd @ dd)) - rr
                gd[q] = float(dd @ dv)
            key = frozenset((self._keys[a_], self._keys[b_]))
            if g[0] <= 0.0:
                if self.collisions == "merge" or key not in self._overlap:
                    out.append((0.0, a_, b_))
                    continue
            s_hit = self._first_entry(sep, grid, g, gd, rr)
            if s_hit is not None:
                out.append((s_hit, a_, b_))
        out.sort(key=lambda z: z[0])
        return out

    @staticmethod
    def _first_entry(sep, grid, g, gd, rr):
        """First s > 0 where g = |d| - R goes from > 0 to <= 0 (sampled sign changes and dips between samples)."""
        from scipy.optimize import brentq, minimize_scalar

        def gf(s):
            dd, _ = sep(s)
            return math.sqrt(float(dd @ dd)) - rr

        for q in range(1, len(grid)):
            lo, hi = grid[q - 1], grid[q]
            if g[q - 1] > 0.0 and g[q] <= 0.0:
                return brentq(gf, lo, hi, xtol=4 * _U * max(hi, 1e-300), rtol=8 * _U)
            if g[q - 1] > 0.0 and g[q] > 0.0 and gd[q - 1] < 0.0 and gd[q] > 0.0:
                r = minimize_scalar(gf, bounds=(lo, hi), method="bounded", options={"xatol": 1e-12 * (hi - lo)})
                if r.fun <= 0.0:
                    return brentq(gf, lo, r.x, xtol=4 * _U * max(r.x, 1e-300), rtol=8 * _U)
        return None

    def _handle_contacts(self, st, t_until, events) -> bool:
        """Process the step's contacts up to t_until. Returns True if the state changed (a merger)."""
        for s, a_, b_ in st.contacts:
            tc = self._t + s
            if tc > t_until:
                break
            ka, kb = self._keys[a_], self._keys[b_]
            if self.collisions == "merge":
                events.append(self._merge(s, a_, b_))
                return True
            key = frozenset((ka, kb))
            if s == 0.0:
                if key in self._overlap:
                    continue
                self._overlap.add(key)
            elif tc <= self._t_out:
                continue
            self._stats["contacts"] += 1
            x, v = self._dense(st, s) if s > 0 else (self._x, self._v)
            events.append({"t": tc, "kind": "contact", "keys": [ka, kb], "key": None,
                           "x": [x[a_].tolist(), x[b_].tolist()], "v": [v[a_].tolist(), v[b_].tolist()]})
        return False

    def _merge(self, s, a_, b_):
        """Commit the step's continuous output at the contact (s located on it to round-off), merge rows a_, b_."""
        if s > 0.0:
            self._land(s)
        e_before = self._pair_energy(a_, b_)
        ma, mb = self._m[a_], self._m[b_]
        M = ma + mb
        ca, cb = self._rpm[a_] > 0.0, self._rpm[b_] > 0.0
        if ca != cb:  # a compact body absorbs the other (review B6-G5)
            keep, drop = (a_, b_) if ca else (b_, a_)
        else:
            keep, drop = (a_, b_) if ma >= mb else (b_, a_)
        ka, kb = self._keys[a_], self._keys[b_]
        if M > 0.0:
            x = (ma * self._x[a_] + mb * self._x[b_]) / M
            v = (ma * self._v[a_] + mb * self._v[b_]) / M
        else:  # pragma: no cover - pairs of test particles are never in contact
            x, v = self._x[keep], self._v[keep]
        rpm = float(self._rpm[keep])
        R = rpm * M if rpm > 0.0 else float(np.cbrt(self._R[a_] ** 3 + self._R[b_] ** 3))
        e_after = 0.5 * M * float(v @ v)
        kept_key = self._keys[keep]
        self._x[keep], self._v[keep], self._m[keep], self._R[keep] = x, v, M, R
        self._drop(drop)
        self._t_out = max(self._t_out, self._t)
        self._overlap = {p for p in self._overlap if self._keys_present(p)}
        self._edited()
        self._stats["merges"] += 1
        return {"t": self._t, "kind": "merge", "keys": [ka, kb], "key": kept_key, "m": float(M), "x": x.tolist(),
                "v": v.tolist(), "radius": R, "delta_energy": e_after - e_before}

    def _keys_present(self, p):
        return all(k in self._keys for k in p)

    def _pair_energy(self, a_, b_):
        """Kinetic energy of the pair + their mutual potential energy + their potential energy in the others' field
        that changes when they merge at their centre of mass."""
        m = self._m
        ke = 0.5 * (m[a_] * float(self._v[a_] @ self._v[a_]) + m[b_] * float(self._v[b_] @ self._v[b_]))
        pe = 0.0
        if m[a_] > 0 and m[b_] > 0:
            pe -= self.G * m[a_] * m[b_] / float(np.linalg.norm(self._x[a_] - self._x[b_]))
        others = [k for k in range(self.n) if k not in (a_, b_) and m[k] > 0]
        M = m[a_] + m[b_]
        xc = (m[a_] * self._x[a_] + m[b_] * self._x[b_]) / M if M > 0 else self._x[a_]
        for k in others:
            pe -= self.G * m[k] * (m[a_] / np.linalg.norm(self._x[k] - self._x[a_])
                                   + m[b_] / np.linalg.norm(self._x[k] - self._x[b_])
                                   - M / np.linalg.norm(self._x[k] - xc))
        return ke + float(pe)


def bench(ns=(3, 10, 30, 100, 300, 1000), integrator="hermite", repeat=20, seed=1):
    """Seconds per integrator step (after the first) for N bodies in a cold random cluster: {N: seconds}."""
    import time
    rng = np.random.default_rng(seed)
    out = {}
    for n in ns:
        nb = NBody(integrator=integrator, dt=1e-3 if integrator == "yoshida4" else None, collisions="pass")
        for _ in range(n):
            nb.add(rng.normal(size=3), 0.1 * rng.normal(size=3), m=1.0 / n)
        nb.step(1)
        t0 = time.perf_counter()
        nb.step(repeat)
        out[n] = (time.perf_counter() - t0) / repeat
    return out
