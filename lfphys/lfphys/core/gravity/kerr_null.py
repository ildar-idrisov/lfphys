# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Null geodesics of the Kerr exterior in Mino time, with Carter's constant (plan P7).

Units G = c = M = 1, spin chi = a/M in [0, 1), Boyer-Lindquist coordinates (t, r, theta, phi). A photon has
E = -p_t, L = p_phi and Carter's constant Q = p_theta^2 - cos^2 theta (a^2 p_t^2 - p_phi^2 csc^2 theta); with
lambda = L/E and eta = Q/E^2 (Gralla & Lupsasca 2020a, "GL-a", PRD 101, 044032, Eqs. 3-5) the motion in Mino time
tau (dx/dtau = Sigma p/E, GL-a Eq. 9) separates:

    (dr/dtau)^2 = R(r) = (r^2 + a^2 - a lambda)^2 - Delta (eta + (lambda - a)^2),        GL-a Eq. (7)
    (dtheta/dtau)^2 = Theta(theta) = eta + a^2 cos^2 theta - lambda^2 cot^2 theta,          GL-a Eq. (8)
    dphi/dtau = a (2 r - a lambda)/Delta + lambda csc^2 theta,                              GL-a Eq. (6c)
    dt/dtau = (r^2 + a^2)(r^2 + a^2 - a lambda)/Delta + a (lambda - a sin^2 theta),         GL-a Eq. (6d)

(for a photon going forward in time; a ray parametrized towards the past, as from the screen, has the opposite
signs of dphi/dtau and dt/dtau).

r(tau) and theta(tau) are closed forms in Jacobi functions (GL-a Eqs. 38, 64, B27, B46, B75, B109): the constants are
parameters, turning points are passed exactly (sn^2 and cn oscillate through them), no step size. phi and t are
integrals of smooth functions of tau along the closed-form r(tau), theta(tau) (Gauss-Legendre panels).

* Radial roots (GL-a Eqs. 79-95): R = r^4 + A r^2 + B r + C, A = a^2 - eta - lambda^2, B = 2 (eta + (lambda - a)^2),
  C = -a^2 eta; Ferrari with the largest root xi0 of the resolvent cubic (real arithmetic: trigonometric form for
  three real roots, Cardano without cancellation otherwise); z = sqrt(xi0/2); r_{1,2} = -z -+ sqrt(-A/2 - z^2 +
  B/(4z)), r_{3,4} = z -+ sqrt(-A/2 - z^2 - B/(4z)). Cases (GL-a Sec. IV B): I four real roots, r4 > r+ (a ray from
  infinity bounces at r4); II four real roots inside the horizon; III r1, r2 real, r3 = conj r4; IV no real root.
* Polar roots: u_pm = Delta_th pm sqrt(Delta_th^2 + eta/a^2), Delta_th = (1 - (eta + lambda^2)/a^2)/2 (GL-a Eq. 19),
  evaluated through A_m = -u_- a^2 = (eta + lambda^2 - a^2)/2 + sqrt(((eta + lambda^2 - a^2)/2)^2 + a^2 eta) and
  u_+ = eta/A_m (stable as a -> 0), parameter m = u_+/u_- = -eta a^2/A_m^2.
* A distant observer at inclination theta_o (GL-b: Gralla & Lupsasca 2020b, PRD 101, 044031, Eqs. 55, 58, 59):
  alpha = -lambda/sin theta_o, beta = sign(p^theta_o) sqrt(Theta(theta_o)); lambda = -alpha sin theta_o,
  eta = (alpha^2 - a^2) cos^2 theta_o + beta^2 (checked on the rendered page: the plain text drops the brackets).
* The m-th equatorial crossing of the ray traced back from the observer (GL-b Eq. 81): sqrt(A_m) I_r =
  2 m K - sign(beta) F_o, F_o = F(arcsin(cos theta_o/sqrt(u+)) | u+/u-); the image order n (half-orbits, Johnson et
  al. 2020) is m - H(beta) (GL-b Eq. 82).
* Accuracy (measured with the 40-digit route of review B5's check c02, no elliptic function and no Ferrari formula,
  at the engine's own binary64 lambda, eta): every r_n with n <= 3 within 3.4e-12 relative for rays at relative
  distance |d| >= 1e-3 from the critical curve, observers from 1e-4 deg to 90 deg; the Mino times of the crossings
  within 6e-16 near the axis (the phases are formed as atan2 of cancellation-free sines and cosines: review B5-K13).
  Closer to the curve the root gap r4 - r3 ~ sqrt(d) is computed with an absolute error ~u (z + |A| ...), so the far
  n = 0 crossing of a grazing ray loses accuracy (7e-12 at d = 1e-6, 5e-10 at 1e-9, 3e-8 at 1e-12; chi = 0.9999,
  89.9 deg, r ~ 3000 M) and the high orders follow the problem's conditioning (n = 8: 2e-4 at d = 1e-12). The tests'
  "64 u per input" tolerances hold for |d| >~ 1e-6.
* Critical curve (Bardeen 1973, GL-a Eqs. 107, 109): lambda(r) = a + (r/a)(r - 2 Delta/(r - 1)),
  eta(r) = (r^3/a^2)(4 Delta/(r - 1)^2 - r), r over the photon shell [r_-^ph, r_+^ph] (Johnson et al. 2020 Eq. 2b);
  evaluated with t = (r - 3)/a: lambda = a - r (r t + 2 a)/(r - 1), eta = r^3 (4 - r t^2)/(r - 1)^2, exact as a -> 0
  (the circle b = sqrt 27).
* Lyapunov exponent of the bound orbit at r (Johnson et al. 2020, Sci. Adv. 6, eaaz1310, Eqs. 8 and 29):
  gamma = (4/a) sqrt(r^2 - r Delta/(r - 1)^2) int_0^1 dt/sqrt((1 - t^2)(u+ t^2 - u-))
        = 4 sqrt(r^2 - r Delta/(r - 1)^2) K(u+/u-)/sqrt(A_m) = sqrt(R''(r)/2) * (2 K/sqrt(A_m));
  Schwarzschild: pi. Successive photon-ring images approach the critical curve by e^{-gamma} per half-orbit.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.i18n import T
from lfphys.codes import coded

from .. import elliptic as EL
from . import kerr

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Kerr null geodesics: Carter constant, Mino time, critical curve"),
    "statement": T("Light rays near a rotating black hole in Boyer–Lindquist coordinates with the conserved E, L_z "
                   "and Carter constant Q (λ, η): the roots of the radial and polar potentials, r(τ) and θ(τ) in "
                   "Jacobi elliptic functions (Mino time; turning points exact), φ and t by quadrature along the ray; "
                   "the distant observer's screen (α, β); equator crossings by order n; spherical photon orbits, "
                   "Bardeen's critical curve (the edge of the shadow), the Lyapunov exponent of the rings."),
    "validity": T("vacuum solution of GR, 0 ≤ a < M; geometric optics (wavelength ≪ M); exterior r > r₊; observer at "
                  "infinity (Bardeen's screen). Accuracy of r_n (measured against a 40-digit reference computation, "
                  "review B5): for n ≤ 3 within 3·10⁻¹² at a relative distance to the critical curve |d| ≥ 10⁻³ (θ_o "
                  "from 10⁻⁴° to 90°); the far crossing n = 0 of a ray right at the curve: 7·10⁻¹² at d = 10⁻⁶, "
                  "5·10⁻¹⁰ at 10⁻⁹, 3·10⁻⁸ at 10⁻¹²; higher orders as the conditioning of the problem allows (n = 8: "
                  "2·10⁻⁴ at d = 10⁻¹²)"),
    "basis": ["Carter, Phys. Rev. 174, 1559 (1968)", "Bardeen, in Black Holes (Les Houches 1972), 1973",
              "Gralla & Lupsasca, Phys. Rev. D 101, 044032 (2020): null geodesics of the Kerr exterior",
              "Gralla & Lupsasca, Phys. Rev. D 101, 044031 (2020): lensing by Kerr black holes",
              "Johnson et al., Sci. Adv. 6, eaaz1310 (2020): photon ring, Lyapunov exponents"],
    "conflicts": [],
}

CASE_I, CASE_II, CASE_III, CASE_IV = 1, 2, 3, 4


def _chk(chi):
    if not 0.0 <= chi < 1.0:
        raise coded(ValueError(T("the spin χ = a/M must be in [0, 1) (the extremal limit is excluded)")), "kerr.spin")


def horizon(chi: float) -> float:
    _chk(chi)
    return 1.0 + math.sqrt(1.0 - chi * chi)


# --- potentials ---------------------------------------------------------------------------------------------------
def radial_potential(r, lam, eta, chi, xp=np):
    a = chi
    delta = r * r - 2.0 * r + a * a
    return (r * r + a * a - a * lam) ** 2 - delta * (eta + (lam - a) ** 2)


def radial_potential_d2(r, lam, eta, chi):
    """R''(r)."""
    a = chi
    w = r * r + a * a - a * lam
    return 2.0 * (4.0 * r * r) + 4.0 * w - 2.0 * (eta + (lam - a) ** 2)


def polar_potential(theta, lam, eta, chi, xp=np):
    a = chi
    c = xp.cos(theta)
    s = xp.sin(theta)
    return eta + a * a * c * c - lam * lam * c * c / (s * s)


# --- the screen of a distant observer ------------------------------------------------------------------------------
def screen_to_constants(alpha, beta, theta_o, chi, xp=np):
    """(lambda, eta) of the photon arriving at screen point (alpha, beta) (GL-b Eqs. 58-59)."""
    a = chi
    s, c = math.sin(theta_o), math.cos(theta_o)
    alpha = xp.asarray(alpha, dtype=xp.float64)
    beta = xp.asarray(beta, dtype=xp.float64)
    return -alpha * s, (alpha * alpha - a * a) * c * c + beta * beta


def constants_to_screen(lam, eta, theta_o, chi, sign_beta=1.0, xp=np):
    """(alpha, beta) of (lambda, eta) for sign(beta) (GL-b Eq. 55); beta is NaN where Theta(theta_o) < 0."""
    th2 = polar_potential(theta_o, lam, eta, chi, xp)
    return -lam / math.sin(theta_o), sign_beta * xp.sqrt(xp.where(th2 >= 0, th2, xp.nan))


# --- roots ---------------------------------------------------------------------------------------------------------
def polar_roots(lam, eta, chi, xp=np):
    """u_+, A_m = -u_- a^2 and m = u_+/u_- (ordinary rays, eta > 0); for eta <= 0 also u_- (vortical rays).
    Returns a dict of arrays."""
    a = chi
    lam = xp.asarray(lam, dtype=xp.float64)
    eta = xp.asarray(eta, dtype=xp.float64)
    h = 0.5 * (eta + lam * lam - a * a)
    am = h + xp.sqrt(h * h + a * a * eta)  # A_m = -u_- a^2 (> 0 for eta > 0)
    out = {"A_m": am}
    with np.errstate(divide="ignore", invalid="ignore"):
        up = xp.where(am > 0, eta / xp.where(am > 0, am, 1.0), xp.nan)
        out["u_plus"] = up
        out["m"] = -eta * a * a / (am * am)
        if a > 0:  # vortical: u_pm = Dth pm sqrt(Dth^2 + eta/a^2) > 0
            dth = 0.5 * (1.0 - (eta + lam * lam) / (a * a))
            sq = xp.sqrt(xp.maximum(dth * dth + eta / (a * a), 0.0))
            out["u_plus_v"] = dth + sq
            out["u_minus_v"] = dth - sq
    return out


def radial_roots(lam, eta, chi, xp=np):
    """Roots of R(r) and the case (GL-a Eqs. 79-95, Sec. IV B), elementwise. Returns a dict: ``case`` (1-4),
    ``r1..r4`` (real roots; NaN where complex), ``z``, ``a1`` (Im r4 where r3 = conj r4), ``a2`` (Im r2 where
    r1 = conj r2), ``A, B, C``, and ``s12``, ``s34`` = sqrt|d12|, sqrt|d34| (half the gaps r2 - r1, r4 - r3 where real,
    without the cancellation of subtracting the roots)."""
    a = chi
    lam = xp.asarray(lam, dtype=xp.float64)
    eta = xp.asarray(eta, dtype=xp.float64)
    A = a * a - eta - lam * lam
    B = 2.0 * (eta + (lam - a) ** 2)
    C = -a * a * eta
    P = -A * A / 12.0 - C
    Q = -A / 3.0 * ((A / 6.0) ** 2 - C) - B * B / 8.0
    disc = (P / 3.0) ** 3 + (Q / 2.0) ** 2  # = -Delta_3/108
    trig = disc < 0.0
    Ps = xp.where(trig, P, -1.0)
    arg = xp.clip(1.5 * Q / Ps * xp.sqrt(-3.0 / Ps), -1.0, 1.0)
    t_trig = 2.0 * xp.sqrt(-Ps / 3.0) * xp.cos(xp.arccos(arg) / 3.0)
    sq = xp.sqrt(xp.maximum(disc, 0.0))
    sgn = xp.where(Q >= 0.0, 1.0, -1.0)
    u3 = -0.5 * Q - sgn * sq  # |u3| = |Q|/2 + sqrt(disc): no cancellation
    u = xp.cbrt(u3)
    with np.errstate(divide="ignore", invalid="ignore"):
        t_card = xp.where(u != 0.0, u - P / (3.0 * xp.where(u != 0.0, u, 1.0)), 0.0)
    t0 = xp.where(trig, t_trig, t_card)
    xi = t0 - A / 3.0
    # one Newton step on the resolvent cubic R(xi) = xi^3 + A xi^2 + (A^2/4 - C) xi - B^2/8 (a polish; skipped where
    # its derivative is small, i.e. near a double root of the resolvent)
    c1 = A * A / 4.0 - C
    f = ((xi + A) * xi + c1) * xi - B * B / 8.0
    fp = (3.0 * xi + 2.0 * A) * xi + c1
    scale = xp.abs(xi) ** 2 + xp.abs(A) * xp.abs(xi) + xp.abs(c1)
    ok = xp.abs(fp) > 1e-6 * scale
    xi = xp.where(ok, xi - f / xp.where(ok, fp, 1.0), xi)
    xi = xp.maximum(xi, 1e-300)
    z = xp.sqrt(0.5 * xi)
    d12 = -0.5 * A - z * z + B / (4.0 * z)
    d34 = -0.5 * A - z * z - B / (4.0 * z)
    s12 = xp.sqrt(xp.abs(d12))
    s34 = xp.sqrt(xp.abs(d34))
    real12 = d12 >= 0.0
    real34 = d34 >= 0.0
    nan = xp.nan
    r1 = xp.where(real12, -z - s12, nan)
    r2 = xp.where(real12, -z + s12, nan)
    r3 = xp.where(real34 & real12, z - s34, nan)
    r4 = xp.where(real34 & real12, z + s34, nan)
    rp = 1.0 + math.sqrt(1.0 - a * a)
    case = xp.where(~real12, CASE_IV, xp.where(~real34, CASE_III, xp.where(r4 > rp, CASE_I, CASE_II)))
    return {"case": case.astype(xp.int8), "r1": r1, "r2": r2, "r3": r3, "r4": r4, "z": z,
            "a1": xp.where(real34, nan, s34), "a2": xp.where(real12, nan, s12), "A": A, "B": B, "C": C,
            "s12": s12, "s34": s34}


# --- the radial motion ---------------------------------------------------------------------------------------------
class _Radial:
    """Closed-form radial motion for every case (GL-a App. B), elementwise over arrays of (lambda, eta).

    ``I(r)`` is the Mino-time antiderivative of 1/sqrt(R) (increasing with r; r = inf allowed) and ``r_at(X)`` the
    inverse in terms of the case's argument X (``X_from``); a ray started at r0 with sign nu_r has
    X = X_from(tau, I(r0), nu_r). Case 1 (r2 < r < r3, between the horizon and r3 of case I) is the bound motion of
    GL-a Eq. (B27); a ray from outside r4 in case I uses case 2 (B46)."""

    def __init__(self, roots, chi, xp=np, inner=None):
        self.xp = xp
        self.chi = chi
        self.rp = 1.0 + math.sqrt(1.0 - chi * chi)
        c = roots["case"]
        # the substitution class: 1 (case I inside r3), 2 (cases I outside r4, II), 3, 4
        cls = xp.where(c == CASE_IV, 4, xp.where(c == CASE_III, 3, 2)).astype(xp.int8)
        if inner is not None:
            cls = xp.where((c == CASE_I) & inner, 1, cls).astype(xp.int8)
        self.cls = cls
        nan = xp.nan
        r1, r2, r3, r4 = roots["r1"], roots["r2"], roots["r3"], roots["r4"]
        z = roots["z"]
        one = xp.ones_like(z)
        real = (cls == 1) | (cls == 2)
        # case 1, 2 (four real roots)
        R1, R2 = xp.where(real, r1, -3.0 * one), xp.where(real, r2, -2.0 * one)
        R3, R4 = xp.where(real, r3, 1.0 * one), xp.where(real, r4, 2.0 * one)
        self.r1, self.r2, self.r3, self.r4 = R1, R2, R3, R4
        # the gaps r4 - r3 and r2 - r1 from the root solver (2 sqrt(d)): no cancellation as two roots approach
        self.r43 = xp.where(real, 2.0 * roots["s34"], 1.0 * one)
        self.r21 = xp.where(real, 2.0 * roots["s12"], 1.0 * one)
        r31, r32, r41, r42 = R3 - R1, R3 - R2, R4 - R1, R4 - R2
        self.k = xp.clip(r32 * r41 / (r31 * r42), 0.0, 1.0)
        self.s12 = xp.sqrt(r31 * r42)
        # case 3 (r1 < r2 real, r3 = conj r4 = z -+ i a1)
        is3 = cls == 3
        a1 = xp.where(is3, roots["a1"], one)
        q1, q2 = xp.where(is3, r1, -3.0 * one), xp.where(is3, r2, -2.0 * one)
        b1 = z
        Aq = xp.sqrt(a1 * a1 + (b1 - q2) ** 2)
        Bq = xp.sqrt(a1 * a1 + (b1 - q1) ** 2)
        self.q1, self.q2, self.Aq, self.Bq = q1, q2, Aq, Bq
        self.k3 = xp.clip(((Aq + Bq) ** 2 - (q2 - q1) ** 2) / (4.0 * Aq * Bq), 0.0, 1.0)
        self.sAB = xp.sqrt(Aq * Bq)
        # case 4 (r1 = conj r2 = -z -+ i a2, r3 = conj r4 = z -+ i a1)
        is4 = cls == 4
        a1_4 = xp.where(is4, roots["a1"], 2.0 * one)
        a2_4 = xp.where(is4, roots["a2"], one)
        bb = 2.0 * z  # b1 - b2
        C4 = xp.sqrt((a1_4 - a2_4) ** 2 + bb * bb)
        D4 = xp.sqrt((a1_4 + a2_4) ** 2 + bb * bb)
        self.a2, self.b1, self.CD = a2_4, z, C4 + D4
        self.k4 = xp.clip(4.0 * C4 * D4 / (C4 + D4) ** 2, 0.0, 1.0)
        g2 = (4.0 * a2_4 * a2_4 - (C4 - D4) ** 2) / ((C4 + D4) ** 2 - 4.0 * a2_4 * a2_4)
        self.g0 = xp.sqrt(xp.maximum(g2, 0.0))
        self.nan = nan

    # the phase variable of each class as a function of r (r = inf allowed)
    def _phase(self, r):
        """(class 1, 2) arcsin x(r); (3) arccos x3(r); (4) arctan x4(r) + arctan g0. Classes 1 and 2 as atan2 of
        sin and cos: x2^2 = (r - r4) r31/((r - r3) r41) and 1 - x2^2 = r43 (r - r1)/((r - r3) r41), x1^2 = (r - r2) r31/
        ((r - r1) r32) and 1 - x1^2 = r21 (r3 - r)/((r - r1) r32), with the gaps r43, r21 from the root solver: the
        phase stays accurate as r3 -> r4 (rays grazing the critical curve; review B5-K13: arcsin of a ratio -> 1 lost
        3e-8 in a far crossing at d = 1e-12)."""
        xp = self.xp
        r = xp.asarray(r, dtype=xp.float64)
        inf = xp.isinf(r)
        rr = xp.where(inf, 1.0, r)
        with np.errstate(divide="ignore", invalid="ignore"):
            r31 = self.r3 - self.r1
            ph1 = xp.arctan2(xp.sqrt(xp.maximum((rr - self.r2) * r31, 0.0)),
                             xp.sqrt(xp.maximum(self.r21 * (self.r3 - rr), 0.0)))
            ph2 = xp.where(inf, xp.arctan2(xp.sqrt(r31), xp.sqrt(self.r43)),
                           xp.arctan2(xp.sqrt(xp.maximum((rr - self.r4) * r31, 0.0)),
                                      xp.sqrt(xp.maximum(self.r43 * (rr - self.r1), 0.0))))
            num = self.Aq * (rr - self.q1) - self.Bq * (rr - self.q2)
            den = self.Aq * (rr - self.q1) + self.Bq * (rr - self.q2)
            x3 = xp.where(inf, (self.Aq - self.Bq) / (self.Aq + self.Bq), num / den)
            ph4 = xp.where(inf, 0.5 * math.pi, xp.arctan((rr + self.b1) / self.a2)) + xp.arctan(self.g0)
        cls = self.cls
        return xp.where(cls == 1, ph1, xp.where(cls == 2, ph2,
                        xp.where(cls == 3, xp.arccos(xp.clip(x3, -1.0, 1.0)), ph4)))

    def _param(self):
        cls = self.cls
        xp = self.xp
        return xp.where((cls == 1) | (cls == 2), self.k, xp.where(cls == 3, self.k3, self.k4))

    def _rate(self):
        """dX/dtau for an increasing antiderivative: X = rate * I."""
        cls = self.cls
        xp = self.xp
        return xp.where((cls == 1) | (cls == 2), 0.5 * self.s12, xp.where(cls == 3, self.sAB, 0.5 * self.CD))

    def antiderivative(self, r):
        """I(r) = int^r dr/sqrt(R) (GL-a Eqs. B20, B40, B71, B101)."""
        return EL.ellipf(self._phase(r), self._param(), self.xp) / self._rate()

    def r_of(self, X):
        """r at the argument X of the class (GL-a Eqs. B27, B46, B75, B109)."""
        xp = self.xp
        sn, cn, dn = EL.ellipj(X, self._param(), xp)
        s2 = sn * sn
        r1, r2, r3, r4 = self.r1, self.r2, self.r3, self.r4
        with np.errstate(divide="ignore", invalid="ignore"):
            rc1 = (r2 * (r3 - r1) - r1 * (r3 - r2) * s2) / ((r3 - r1) - (r3 - r2) * s2)
            rc2 = (r4 * (r3 - r1) - r3 * (r4 - r1) * s2) / ((r3 - r1) - (r4 - r1) * s2)
            A, B, q1, q2 = self.Aq, self.Bq, self.q1, self.q2
            rc3 = ((B * q2 - A * q1) + (B * q2 + A * q1) * cn) / ((B - A) + (B + A) * cn)
            g0 = self.g0
            rc4 = self.a2 * (sn - g0 * cn) / (cn + g0 * sn) - self.b1
        cls = self.cls
        return xp.where(cls == 1, rc1, xp.where(cls == 2, rc2, xp.where(cls == 3, rc3, rc4)))

    def dr_dX(self, X):
        """dr/dX of ``r_of`` (sn' = cn dn, cn' = -sn dn, am' = dn)."""
        xp = self.xp
        sn, cn, dn = EL.ellipj(X, self._param(), xp)
        s2 = sn * sn
        ds2 = 2.0 * sn * cn * dn
        r1, r2, r3, r4 = self.r1, self.r2, self.r3, self.r4
        with np.errstate(divide="ignore", invalid="ignore"):
            d1 = (r3 - r2) * (r3 - r1) * (r2 - r1) / ((r3 - r1) - (r3 - r2) * s2) ** 2 * ds2
            d2 = (r4 - r1) * (r3 - r1) * (r4 - r3) / ((r3 - r1) - (r4 - r1) * s2) ** 2 * ds2
            A, B, q1, q2 = self.Aq, self.Bq, self.q1, self.q2
            P, Qc, Rr, Sc = B * q2 - A * q1, B * q2 + A * q1, B - A, B + A
            d3 = (Qc * Rr - P * Sc) / (Rr + Sc * cn) ** 2 * (-sn * dn)
            g0 = self.g0
            x4 = (sn - g0 * cn) / (cn + g0 * sn)
            d4 = self.a2 * (1.0 + x4 * x4) * dn
        cls = self.cls
        return xp.where(cls == 1, d1, xp.where(cls == 2, d2, xp.where(cls == 3, d3, d4)))

    def dX_dtau(self, nu_r):
        cls = self.cls
        return self.xp.where(cls == 4, nu_r * self._rate(), self._rate())

    def X_of(self, tau, I0, nu_r):
        """The argument X(tau) of a ray started where the antiderivative is I0, with radial sign nu_r."""
        xp = self.xp
        cls = self.cls
        rate = self._rate()
        # classes 1, 2, 3: X = rate (tau + nu_r I0) (GL-a Eqs. B26, B45, B74); class 4: X = rate (nu_r tau + I0) (B104)
        return xp.where(cls == 4, rate * (nu_r * tau + I0), rate * (tau + nu_r * I0))


def _bh(chi):
    a = chi
    return a, 1.0 + math.sqrt(1.0 - a * a)


# --- rays traced back from a distant observer ---------------------------------------------------------------------
def trace_back(alpha, beta, theta_o, chi, n_max=2, xp=np):
    """Rays traced back in time from screen points (alpha, beta) of an observer at infinity and inclination theta_o
    (radians, 0 <= theta_o <= pi; on the axis lambda = 0 and every photon arrives with p^theta < 0, the formula's
    beta < 0 branch, GL-b Eq. 62). Elementwise; returns a dict of arrays:

    ``lam, eta`` (constants), ``case`` (radial case 1-4), ``captured`` (the ray, followed back, falls into the black
    hole: it came from the white-hole horizon; otherwise it came from infinity), ``tau_total`` (Mino time from the
    observer to the horizon or back to infinity), ``tau_turn`` (Mino time of the radial turning point r4, case I;
    NaN otherwise), ``tau_n`` (n_max + 1, ...) Mino times of the equatorial crossings n = 0..n_max in order along
    the ray (NaN where the ray never gets there: vortical rays (eta <= 0) do not cross the equator), ``r_n`` the
    radii there, ``kr_sign_n`` the sign of the photon's p^r at the crossing in its forward (physical) direction
    (+1 outward), ``face_n`` the face of the equatorial plane the photon left there (+1: towards +z, the northern
    face; -1: the southern face), ``n_cross`` the number of crossings before capture or escape (capped at
    n_max + 1).

    What n is (review B5-K9). n counts the equatorial crossings along the ray traced back from the observer (GL-b's
    m-bar, Eq. 82); since tau_n = (2 (n + H) K - sign(beta) F_o)/sqrt(A_m), n = floor(tau_n / G_half), G_half =
    2 K/sqrt(A_m) the Mino time of one polar half-libration: n is the number of completed polar half-librations
    ("half-orbits" of Johnson et al. 2020 counted in theta). For an observer above the plane, even n are crossings
    from the near (northern) face, odd n from the far (southern) face (GL-b after Eq. 82); ``face_n`` gives it per
    crossing. n is not a count of turns around the hole in azimuth: near edge-on (theta_o >~ 75 deg for a disk of
    20 M) a ray below the line of sight crosses the plane first far away, r ~ |beta|/|cos theta_o|, so the direct
    image of the disk's southern face is its n = 1 crossing; at exactly theta_o = 90 deg (the case GL-b exclude,
    their footnote 15) the observer's own crossing at tau = 0 is dropped and that image is n = 0. n = 1 is the thin
    lensing ring only for moderate inclinations."""
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):  # masked lanes may hold inf/NaN
        return _trace_back(alpha, beta, theta_o, chi, n_max, xp)


def _trace_back(alpha, beta, theta_o, chi, n_max, xp):
    a, rp = _bh(chi)
    if not 0.0 <= theta_o <= math.pi:
        raise ValueError("theta_o must be in [0, pi]")
    flip = theta_o > 0.5 * math.pi  # the reflection theta -> pi - theta maps the observer to the north, beta -> -beta
    th = math.pi - theta_o if flip else theta_o
    alpha = xp.asarray(alpha, dtype=xp.float64)
    beta = xp.asarray(beta, dtype=xp.float64)
    alpha, beta = xp.broadcast_arrays(alpha, beta)
    b_eff = -beta if flip else beta
    lam, eta = screen_to_constants(alpha, b_eff, th, chi, xp)
    roots = radial_roots(lam, eta, chi, xp)
    rad = _Radial(roots, chi, xp)
    case = roots["case"]
    inf = xp.full(lam.shape, xp.inf)
    I_inf = rad.antiderivative(inf)
    I_hor = rad.antiderivative(xp.full(lam.shape, rp))
    scatter = case == CASE_I
    tau_total = xp.where(scatter, 2.0 * I_inf, I_inf - I_hor)
    tau_turn = xp.where(scatter, I_inf, xp.nan)
    # polar motion: equatorial crossings of ordinary rays (eta > 0), GL-b Eq. (81)
    pol = polar_roots(lam, eta, chi, xp)
    ordinary = eta > 0.0
    Am = xp.where(ordinary, pol["A_m"], 1.0)
    mth = xp.where(ordinary, pol["m"], 0.0)
    # psi_o = arcsin(cos(theta_o)/sqrt(u+)) as atan2(cos theta_o, sqrt(u+ - cos^2 theta_o)) with u+ - cos^2 =
    # sin^2 theta_o beta^2/(A_m + a^2 cos^2 theta_o) (from (1 - u) Theta = a^2 (u+ - u)(u - u-), Theta(theta_o) =
    # beta^2): no loss near the axis (review B5-K13: the arcsin of 1 - O(theta_o^2) cost u/theta_o)
    c_o, s_o = math.cos(th), math.sin(th)
    psi_o = xp.arctan2(c_o * xp.ones_like(Am), s_o * xp.abs(b_eff) / xp.sqrt(Am + a * a * c_o * c_o))
    Fo = EL.ellipf(psi_o, mth, xp)
    Kth = EL.ellipk(mth, xp)
    sb = xp.where(b_eff > 0.0, 1.0, -1.0)
    H = xp.where(b_eff > 0.0, 1.0, 0.0)
    if th == 0.0:  # on the axis: F_o = K, and the two branches give the same crossings (GL-b Eqs. 62, 78)
        sb = -xp.ones_like(sb)
        H = xp.zeros_like(H)
    if abs(math.cos(th)) < 1e-12:  # edge-on: the observer is in the plane; its own crossing (tau = 0) is not one
        Fo = xp.zeros_like(Fo)
        H = xp.ones_like(H)
    sq = xp.sqrt(Am)
    taus, rs, ks, fs = [], [], [], []
    ncross = xp.zeros(lam.shape, dtype=xp.int8)
    # the face of the disk the photon left at crossing n: going back, d cos(theta)/dtau = sb sqrt(u+ A_m)
    # (-1)^(n + H) there, so the photon moved (forward) towards +z (left the upper, northern face) when
    # -sb (-1)^(n + H) > 0; mirrored for an observer below the plane
    face_sign = -1.0 if flip else 1.0
    for n in range(n_max + 1):
        tn = (2.0 * (n + H) * Kth - sb * Fo) / sq
        valid = ordinary & (tn < tau_total)
        tn = xp.where(valid, tn, xp.nan)
        X = rad.X_of(xp.where(valid, tn, 0.0), I_inf, -1.0)
        rn = xp.where(valid, rad.r_of(X), xp.nan)
        kr = xp.where(valid, xp.where(scatter & (tn > tau_turn), -1.0, 1.0), xp.nan)
        par = 1.0 - 2.0 * xp.remainder(n + H, 2.0)  # (-1)^(n + H)
        fs.append(xp.where(valid, -face_sign * sb * par, xp.nan))
        taus.append(tn)
        rs.append(rn)
        ks.append(kr)
        ncross = ncross + valid.astype(xp.int8)
    if n_max >= 0:  # is there a crossing beyond n_max? (n_cross capped at n_max + 1)
        tn = (2.0 * (n_max + 1 + H) * Kth - sb * Fo) / sq
        ncross = ncross + (ordinary & (tn < tau_total)).astype(xp.int8)
    return {"lam": lam, "eta": eta, "case": case, "captured": case != CASE_I, "tau_total": tau_total,
            "tau_turn": tau_turn, "tau_n": xp.stack(taus), "r_n": xp.stack(rs), "kr_sign_n": xp.stack(ks),
            "face_n": xp.stack(fs), "n_cross": ncross}


# --- a single ray with positions along it --------------------------------------------------------------------------
class NullRay:
    """One null geodesic with constants (lambda, eta), started at (r0, theta0) with the signs nu_r, nu_theta of
    dr/dtau and dtheta/dtau (r0 = inf: arriving from or leaving to infinity); ``future`` False parametrizes it
    towards the past (phi and t then decrease along tau where the photon's own phi and t increase). Closed-form
    r(tau), theta(tau) and their tau-derivatives; phi(tau) (and t(tau) for finite r0) by Gauss-Legendre quadrature
    along the closed form.

    ``from_screen(alpha, beta, theta_o, chi)``: the ray reaching the screen point, traced back from the observer
    (tau = 0 at the observer, phi = 0 there)."""

    def __init__(self, chi, lam, eta, r0, theta0, nu_r, nu_theta, phi0=0.0, t0=0.0, future=True):
        _chk(chi)
        self.dir = 1.0 if future else -1.0  # the time orientation of the parametrization (from_screen: the past)
        self.chi, self.a = chi, chi
        self.rp = horizon(chi)
        self.lam, self.eta = float(lam), float(eta)
        self.r0, self.theta0 = float(r0), float(theta0)
        self.nu_r, self.nu_th = (1.0 if nu_r >= 0 else -1.0), (1.0 if nu_theta >= 0 else -1.0)
        self.phi0, self.t0 = float(phi0), float(t0)
        roots = radial_roots(np.array([self.lam]), np.array([self.eta]), chi)
        self.roots = {k: v for k, v in roots.items()}
        self.case = int(roots["case"][0])
        inner = None
        if self.case == CASE_I and math.isfinite(self.r0) and self.r0 < float(roots["r4"][0]):
            inner = np.array([True])
        self.rad = _Radial(roots, chi, np, inner)
        self.cls = int(self.rad.cls[0])
        if math.isfinite(self.r0) and radial_potential(self.r0, self.lam, self.eta, chi) < -1e-12 * max(1.0,
                                                                                                        self.r0) ** 4:
            raise ValueError("R(r0) < 0: no null geodesic with these constants passes r0")
        th_pot = float(polar_potential(self.theta0, self.lam, self.eta, chi))
        if th_pot < -1e-12 * (abs(self.eta) + self.lam ** 2 / max(math.sin(self.theta0) ** 2, 1e-300) + chi * chi):
            raise ValueError("Theta(theta0) < 0: no null geodesic with these constants passes theta0")
        self.I0 = float(self.rad.antiderivative(np.array([self.r0]))[0])
        # polar motion
        self._setup_polar()

    @classmethod
    def from_screen(cls, alpha, beta, theta_o, chi):
        lam, eta = screen_to_constants(alpha, beta, theta_o, chi)
        sb = 1.0 if beta > 0 else -1.0
        return cls(chi, float(lam), float(eta), math.inf, theta_o, -1.0, -sb, future=False)

    def _setup_polar(self):
        a, lam, eta = self.a, self.lam, self.eta
        c0 = math.cos(self.theta0)
        if eta > 0 or a == 0.0:
            pol = polar_roots(np.array([lam]), np.array([eta]), self.chi)
            self.Am, self.up, self.mth = float(pol["A_m"][0]), float(pol["u_plus"][0]), float(pol["m"][0])
            self.vortical = False
            th0 = max(float(polar_potential(self.theta0, lam, eta, self.chi)), 0.0)
            psi = math.atan2(c0, abs(math.sin(self.theta0)) * math.sqrt(th0) / math.sqrt(self.Am + a * a * c0 * c0))
            self.Gs = -float(EL.ellipf(psi, self.mth)) / math.sqrt(self.Am)
        else:
            if a == 0.0:
                raise ValueError("eta < 0 is not allowed for a = 0")
            pol = polar_roots(np.array([lam]), np.array([eta]), self.chi)
            self.upv, self.umv = float(pol["u_plus_v"][0]), float(pol["u_minus_v"][0])
            self.vortical = True
            self.h = 1.0 if c0 >= 0 else -1.0
            self.mv = 1.0 - self.upv / self.umv
            self.sqv = math.sqrt(self.umv * a * a)
            ups = math.asin(math.sqrt(max(0.0, min(1.0, (c0 * c0 - self.umv) / (self.upv - self.umv)))))
            self.Gs = -self.h * float(EL.ellipf(ups, self.mv)) / self.sqv

    # closed forms
    def r(self, tau):
        tau = np.asarray(tau, float)
        return np.reshape(self.rad.r_of(self.rad.X_of(tau, self.I0, self.nu_r)), tau.shape)

    def cos_theta(self, tau):
        tau = np.asarray(tau, float)
        if not self.vortical:
            sn, _, _ = EL.ellipj(math.sqrt(self.Am) * (tau + self.nu_th * self.Gs), self.mth)
            return -self.nu_th * math.sqrt(self.up) * sn
        _, _, dn = EL.ellipj(self.sqv * (tau + self.nu_th * self.Gs), self.mv)
        return self.h * math.sqrt(self.umv) * dn

    def theta(self, tau):
        return np.arccos(np.clip(self.cos_theta(tau), -1.0, 1.0))

    def drdtau(self, tau):
        """dr/dtau of the closed form (analytic: sn' = cn dn), for the checks (dr/dtau)^2 = R(r)."""
        tau = np.asarray(tau, float)
        X = self.rad.X_of(tau, self.I0, self.nu_r)
        return np.reshape(self.rad.dr_dX(X) * self.rad.dX_dtau(self.nu_r), tau.shape)

    def dthetadtau(self, tau):
        """dtheta/dtau of the closed form (analytic), for the checks (dtheta/dtau)^2 = Theta(theta)."""
        tau = np.asarray(tau, float)
        if not self.vortical:
            k = math.sqrt(self.Am)
            sn, cn, dn = EL.ellipj(k * (tau + self.nu_th * self.Gs), self.mth)
            dc = -self.nu_th * math.sqrt(self.up) * cn * dn * k
        else:
            sn, cn, dn = EL.ellipj(self.sqv * (tau + self.nu_th * self.Gs), self.mv)
            dc = self.h * math.sqrt(self.umv) * (-self.mv * sn * cn) * self.sqv
        return -dc / np.sin(self.theta(tau))

    def tau_end(self):
        """Mino time at which the ray reaches the horizon (falling) or infinity (escaping)."""
        rad = self.rad
        I_inf = float(rad.antiderivative(np.array([math.inf]))[0])
        I_hor = float(rad.antiderivative(np.array([self.rp]))[0])
        if self.cls == 1:  # bounded between r2 and r3: falls in after the turning point at r3 if outgoing
            I3 = float(rad.antiderivative(np.array([float(self.roots["r3"][0])]))[0])
            return (I3 - self.I0) + (I3 - I_hor) if self.nu_r > 0 else self.I0 - I_hor
        if self.cls == 2 and self.case == CASE_I:  # bounces at r4 if incoming
            return (I_inf - self.I0) if self.nu_r > 0 else self.I0 + I_inf
        # cases II, III, IV: monotone
        return (I_inf - self.I0) if self.nu_r > 0 else (self.I0 - I_hor)

    def dphi_dtau(self, r, theta):
        a, lam = self.a, self.lam
        delta = r * r - 2.0 * r + a * a
        return a * (2.0 * r - a * lam) / delta + lam / np.sin(theta) ** 2

    def dt_dtau(self, r, theta):
        a, lam = self.a, self.lam
        delta = r * r - 2.0 * r + a * a
        w = r * r + a * a - a * lam
        return (r * r + a * a) * w / delta + a * (lam - a * np.sin(theta) ** 2)

    def path(self, taus, nodes=16):
        """r, theta, phi (and t for finite r0) at the increasing Mino times ``taus`` (taus[0] >= 0): phi and t from
        tau = 0 by composite Gauss-Legendre quadrature with ``nodes`` points per interval between successive taus."""
        taus = np.asarray(taus, float)
        x, w = np.polynomial.legendre.leggauss(nodes)
        edges = np.concatenate(([0.0], taus))
        lo, hi = edges[:-1], edges[1:]
        mid, half = 0.5 * (lo + hi), 0.5 * (hi - lo)
        tq = mid[:, None] + half[:, None] * x[None, :]
        rq = self.r(tq)
        thq = self.theta(tq)
        dphi = self.dir * (self.dphi_dtau(rq, thq) * w[None, :]).sum(1) * half
        out = {"tau": taus, "r": self.r(taus), "theta": self.theta(taus), "phi": self.phi0 + np.cumsum(dphi)}
        if math.isfinite(self.r0):
            out["t"] = self.t0 + self.dir * np.cumsum((self.dt_dtau(rq, thq) * w[None, :]).sum(1) * half)
        return out


def cartesian(r, theta, phi, chi):
    """Boyer-Lindquist (r, theta, phi) to the Cartesian coordinates of the Kerr-Schild form at fixed t
    (x + i y = sqrt(r^2 + a^2) sin(theta) e^{i phi}, z = r cos(theta); exact spheres of radius r at a = 0): for
    drawing rays in 3-D. (The azimuth is Boyer-Lindquist phi, which winds without bound at the horizon.)"""
    s = np.sqrt(np.asarray(r, float) ** 2 + chi * chi) * np.sin(theta)
    return s * np.cos(phi), s * np.sin(phi), np.asarray(r, float) * np.cos(theta)


def screen_ray_path(alpha, beta, theta_o, chi, r_out=30.0, n=300, r_stop=None):
    """The ray reaching the screen point (alpha, beta), traced back from the sphere r = r_out (on its way in) until it
    is captured (r = r_stop, default r+ + 0.02) or has left again through r = r_out. Returns a dict: ``tau`` (Mino
    time from the observer), ``r``, ``theta``, ``phi`` (phi = 0 at the observer; Boyer-Lindquist), ``x, y, z``
    (``cartesian``), ``captured``. Closed-form r(tau), theta(tau); phi by Gauss-Legendre quadrature from the observer
    at infinity (the integrand falls as 1/r^2 there)."""
    ray = NullRay.from_screen(alpha, beta, theta_o, chi)
    rad = ray.rad
    rp = ray.rp
    r_stop = rp + 0.02 if r_stop is None else float(r_stop)
    I_inf = float(rad.antiderivative(np.array([math.inf]))[0])
    I_out = float(rad.antiderivative(np.array([float(r_out)]))[0])
    tau_in = I_inf - I_out
    if ray.case == CASE_I:
        r4 = float(ray.roots["r4"][0])
        if r4 >= r_out:
            raise ValueError("the ray never comes inside r_out")
        tau_end = 2.0 * I_inf - I_out
        captured = False
    else:
        tau_end = I_inf - float(rad.antiderivative(np.array([r_stop]))[0])
        captured = True
    taus = np.linspace(tau_in, tau_end, int(n))
    out = ray.path(taus, nodes=24)
    out["captured"] = captured
    out["x"], out["y"], out["z"] = cartesian(out["r"], out["theta"], out["phi"], chi)
    return out


# --- the photon shell and the critical curve -----------------------------------------------------------------------
def photon_shell(chi: float) -> tuple[float, float]:
    """Radii of the prograde and retrograde circular equatorial photon orbits: the photon shell r in [r_-, r_+]
    (Johnson et al. 2020 Eq. 2b; = kerr.photon_orbit)."""
    return kerr.photon_orbit(chi, True), kerr.photon_orbit(chi, False)


def critical_constants(r, chi, xp=np):
    """(lambda, eta) of the spherical photon orbit at radius r (Bardeen; GL-a Eqs. 107, 109), through
    t = (r - 3)/a so that the a -> 0 limit is exact. a > 0."""
    a = chi
    if a <= 0.0:
        raise ValueError("a = 0: every spherical photon orbit is at r = 3 (b = sqrt 27); use critical_curve")
    r = xp.asarray(r, dtype=xp.float64)
    t = (r - 3.0) / a
    return a - r * (r * t + 2.0 * a) / (r - 1.0), r ** 3 * (4.0 - r * t * t) / (r - 1.0) ** 2


def critical_constants_t(t, chi, xp=np):
    """The same through t = (r - 3)/a: works for any chi including 0."""
    a = chi
    t = xp.asarray(t, dtype=xp.float64)
    r = 3.0 + a * t
    return a - r * (r * t + 2.0 * a) / (r - 1.0), r ** 3 * (4.0 - r * t * t) / (r - 1.0) ** 2, r


def _shell_t(chi):
    """t = (r - 3)/a at the two ends of the photon shell (exact as a -> 0: -+ 2/sqrt 3)."""
    a = chi
    if a == 0.0:
        return -2.0 / math.sqrt(3.0), 2.0 / math.sqrt(3.0)
    rm, rpl = photon_shell(chi)
    # r^(1/2) (r - 3) = -+ 2 a  ->  t = -+ 2/sqrt(r)
    return -2.0 / math.sqrt(rm), 2.0 / math.sqrt(rpl)


def _polar_orbit_t(chi):
    """t = (r - 3)/a of the bound orbit with lambda = 0 (the one seen by an observer on the axis)."""
    from scipy.optimize import brentq
    t_lo, t_hi = _shell_t(chi)
    return brentq(lambda t: float(critical_constants_t(t, chi)[0]), t_lo, t_hi, xtol=1e-16, rtol=8.9e-16,
                  maxiter=300)


def _visible_t(chi, beta2):
    """The interval of t = (r - 3)/a with beta^2(t) >= 0: bisection outwards from the lambda = 0 orbit to each end
    of the shell where beta^2 changes sign (or the end itself)."""
    from scipy.optimize import brentq
    t_lo, t_hi = _shell_t(chi)
    t0 = _polar_orbit_t(chi) if chi > 0.0 else 0.0
    lo = t_lo if beta2(t_lo) >= 0.0 else brentq(beta2, t_lo, t0, xtol=1e-16, rtol=8.9e-16, maxiter=300)
    hi = t_hi if beta2(t_hi) >= 0.0 else brentq(beta2, t0, t_hi, xtol=1e-16, rtol=8.9e-16, maxiter=300)
    return lo, hi


def face_on_shadow_radius(chi: float) -> tuple[float, float]:
    """(b, r): radius of the circular shadow seen from the axis, b = sqrt(eta + a^2) of the bound orbit with
    lambda = 0 (GL-b Eq. 61), and that orbit's radius."""
    if chi == 0.0:
        return math.sqrt(27.0), 3.0
    t0 = _polar_orbit_t(chi)
    lam, eta, r = critical_constants_t(t0, chi)
    return math.sqrt(float(eta) + chi * chi), float(r)


def critical_curve(chi: float, theta_o: float, n: int = 721):
    """The critical curve C on the screen of an observer at inclination theta_o (0 <= theta_o <= pi): the edge of
    the shadow (Bardeen 1973; GL-b Eq. 57). Returns dict with ``alpha``, ``beta`` (a closed curve: the upper half
    from the prograde (left) to the retrograde (right) side, then the lower half back), ``r`` (the radius of the
    bound orbit behind each point). On the axis: the circle of ``face_on_shadow_radius``."""
    _chk(chi)
    th = min(theta_o, math.pi - theta_o)
    if th == 0.0:
        b, r0 = face_on_shadow_radius(chi)
        ph = np.linspace(math.pi, -math.pi, n)
        return {"alpha": b * np.cos(ph), "beta": np.abs(b * np.sin(ph)) * np.where(np.arange(n) < n // 2, 1.0, -1.0),
                "r": np.full(n, r0)}
    s, c = math.sin(th), math.cos(th)
    a = chi

    def beta2(t):
        lam, eta, _ = critical_constants_t(t, chi)
        return float(eta + a * a * c * c - lam * lam * c * c / (s * s))

    # the visible range: beta^2 >= 0, an interval around the orbit with lambda = 0 (beta^2 = eta + a^2 cos^2 > 0
    # there); the whole shell for an edge-on observer
    lo, hi = _visible_t(chi, beta2)
    # cosine spacing resolves the square-root ends
    m = max(8, n // 2)
    tt = lo + (hi - lo) * 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, m)))
    lam, eta, r = critical_constants_t(tt, chi)
    al = -lam / s
    be = np.sqrt(np.maximum(eta + a * a * c * c - lam * lam * c * c / (s * s), 0.0))
    alpha = np.concatenate((al, al[::-1][1:]))  # (pi - theta_o: the same curve, symmetric under beta -> -beta)
    beta = np.concatenate((be, -be[::-1][1:]))
    rr = np.concatenate((r, r[::-1][1:]))
    return {"alpha": alpha, "beta": beta, "r": rr}


def critical_radius_at(chi: float, theta_o: float, angle: float, center=(0.0, 0.0)):
    """Distance from ``center`` to the critical curve along the screen direction ``angle`` (radians from the
    alpha axis): a root of the curve's polar angle along its closed-form parameter (bisection to round-off)."""
    from scipy.optimize import brentq
    th = min(theta_o, math.pi - theta_o)
    if th == 0.0:
        b, r0 = face_on_shadow_radius(chi)
        if math.hypot(*center) > 0.0:
            raise coded(ValueError(T("on the axis the shadow is centred on the origin")), "kerr.axis_view")
        return b, r0
    s, c = math.sin(th), math.cos(th)
    a = chi
    cx, cy = center
    upper = math.sin(angle) >= 0.0
    sgn = 1.0 if upper else -1.0

    def point(t):
        lam, eta, _ = critical_constants_t(t, chi)
        b2 = float(eta + a * a * c * c - lam * lam * c * c / (s * s))
        return float(-lam / s), sgn * math.sqrt(max(b2, 0.0)), b2

    def beta2(t):
        return point(t)[2]

    lo, hi = _visible_t(chi, beta2)

    def dang(t):
        x, y, _ = point(t)
        d = math.atan2(y - cy, x - cx) - angle
        return (d + math.pi) % (2.0 * math.pi) - math.pi

    # along t from lo to hi each branch runs from the prograde (left) to the retrograde (right) side
    grid = lo + (hi - lo) * 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, 2001)))
    vals = np.array([dang(t) for t in grid])
    for i in range(grid.size - 1):
        if vals[i] == 0.0:
            t0 = grid[i]
            break
        if vals[i] * vals[i + 1] < 0.0 and abs(vals[i] - vals[i + 1]) < math.pi:
            t0 = brentq(dang, grid[i], grid[i + 1], xtol=1e-16, rtol=8.9e-16, maxiter=300)
            break
    else:
        t0 = grid[int(np.argmin(np.abs(vals)))]
    x, y, _ = point(t0)
    return math.hypot(x - cx, y - cy), 3.0 + a * t0


def critical_radii(chi: float, theta_o: float, angles, center=(0.0, 0.0)):
    """``critical_radius_at`` along many screen directions at once (review B5-K10: the closed-form reference of a
    shadow measured in 128 directions): the curve's polar angle about ``center`` on the same cosine grid of the
    closed-form parameter (vectorized), the first bracket of its zero, then a vectorized bisection in the parameter to
    adjacent doubles. Returns (rho, r): the distances and the bound-orbit radii behind the points."""
    ang = np.atleast_1d(np.asarray(angles, dtype=float))
    th = min(theta_o, math.pi - theta_o)
    if th == 0.0:
        b, r0 = face_on_shadow_radius(chi)
        if math.hypot(*center) > 0.0:
            raise coded(ValueError(T("on the axis the shadow is centred on the origin")), "kerr.axis_view")
        return np.full(ang.shape, b), np.full(ang.shape, r0)
    s, c = math.sin(th), math.cos(th)
    a = chi
    cx, cy = center
    sgn = np.where(np.sin(ang) >= 0.0, 1.0, -1.0)

    def beta2(t):
        lam, eta, _ = critical_constants_t(t, chi)
        return float(eta + a * a * c * c - lam * lam * c * c / (s * s))

    lo, hi = _visible_t(chi, beta2)

    def dang(t, sg, an):
        lam, eta, _ = critical_constants_t(t, chi)
        x = -lam / s
        y = sg * np.sqrt(np.maximum(eta + a * a * c * c - lam * lam * c * c / (s * s), 0.0))
        d = np.arctan2(y - cy, x - cx) - an
        return (d + math.pi) % (2.0 * math.pi) - math.pi

    grid = lo + (hi - lo) * 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, 2001)))
    vals = dang(grid[None, :], sgn[:, None], ang[:, None])
    cross = (vals[:, :-1] * vals[:, 1:] < 0.0) & (np.abs(vals[:, :-1] - vals[:, 1:]) < math.pi)
    zero = vals[:, :-1] == 0.0
    hit = cross | zero
    first = np.argmax(hit, axis=1)
    found = hit[np.arange(ang.size), first]
    t_lo = grid[first]
    t_hi = np.where(zero[np.arange(ang.size), first], t_lo, grid[first + 1])
    f_lo = dang(t_lo, sgn, ang)
    for _ in range(200):
        mid = 0.5 * (t_lo + t_hi)
        live = (mid > t_lo) & (mid < t_hi)
        if not live.any():
            break
        fm = dang(mid, sgn, ang)
        same = (fm * f_lo > 0.0) & live
        t_lo = np.where(same, mid, t_lo)
        f_lo = np.where(same, fm, f_lo)
        t_hi = np.where(live & ~same, mid, t_hi)
    t0 = np.where(found, 0.5 * (t_lo + t_hi), grid[np.argmin(np.abs(vals), axis=1)])
    lam, eta, r = critical_constants_t(t0, chi)
    x = -lam / s
    y = sgn * np.sqrt(np.maximum(eta + a * a * c * c - lam * lam * c * c / (s * s), 0.0))
    return np.hypot(x - cx, y - cy), r


def shell_angles(r, chi):
    """u_pm and the polar turning points theta_pm of the bound orbit at r (GL-a Eqs. 19, 28 with the critical
    constants)."""
    a = chi
    lam, eta = critical_constants(r, chi)
    pol = polar_roots(np.asarray(lam), np.asarray(eta), chi)
    up = pol["u_plus"]
    return {"u_plus": up, "u_minus": -pol["A_m"] / (a * a), "theta_minus": np.arccos(np.sqrt(up)),
            "theta_plus": np.arccos(-np.sqrt(up))}


def lyapunov(r, chi):
    """Lyapunov exponent gamma of the bound photon orbit at r per half-orbit (Johnson et al. 2020 Eq. 8):
    gamma = 4 sqrt(r^2 - r Delta/(r - 1)^2) K(u+/u-)/sqrt(A_m). Works for chi = 0 through t = (r - 3)/a."""
    a = chi
    r = np.asarray(r, float)
    if a == 0.0:
        return np.full(r.shape, math.pi)
    lam, eta = critical_constants(r, chi)
    pol = polar_roots(lam, eta, chi)
    delta = r * r - 2.0 * r + a * a
    chi_t = r * r - r * delta / (r - 1.0) ** 2
    return 4.0 * np.sqrt(chi_t) * EL.ellipk(pol["m"]) / np.sqrt(pol["A_m"])


def lyapunov_second_route(r, chi):
    """gamma = sqrt(R''(r)/2) * G_theta over a half-orbit (Johnson et al. 2020 Eq. 29), R'' from the polynomial."""
    a = chi
    r = np.asarray(r, float)
    lam, eta = critical_constants(r, chi)
    pol = polar_roots(lam, eta, chi)
    g_half = 2.0 * EL.ellipk(pol["m"]) / np.sqrt(pol["A_m"])
    return np.sqrt(0.5 * radial_potential_d2(r, lam, eta, chi)) * g_half
