# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The image of a Kerr black hole on the screen of a distant observer: shadow, photon rings, an equatorial disk
(plan P7, physics of P14.3).

Every pixel (alpha, beta) of the screen (Bardeen's impact parameters, in M, GL-b Eq. 55) is a photon with
constants lambda = -alpha sin theta_o, eta = (alpha^2 - a^2) cos^2 theta_o + beta^2, traced back in time in closed
form (``kerr_null.trace_back``): its fate (it fell out of the white-hole horizon - the shadow - or came from
infinity), its equatorial crossings n = 0, 1, 2, ... in order along the ray traced back, and at each crossing the
radius r_n, the redshift factor g = E_observed/E_emitted of an emitter there, the sign of the photon's p^r and the
face of the disk the photon left (``face_n``: +1 the northern face, towards +z).

What n is (review B5-K9): the number of equatorial crossings before this one along the backward ray (GL-b's m-bar,
Eqs. 81-82) = the number of completed polar half-librations (Johnson et al. 2020's half-orbits, counted in theta).
For an observer above the plane even n are crossings from the near (northern) face, odd n from the far (southern)
face. For moderate inclinations n = 0 is the direct image, n = 1 the thin lensing ring, n >= 2 the photon ring; near
edge-on (theta_o >~ 75 deg for a disk of 20 M) a ray below the line of sight crosses the plane first far away
(r ~ |beta|/|cos theta_o|), so the direct image of the southern face is its n = 1 crossing - use ``face_n`` and r_n to
label images; at exactly theta_o = 90 deg (excluded by GL-b, footnote 15) the observer's own crossing is dropped and
that image is n = 0.

Emitters (the source model is an assumption, stated, not a law):
* "keplerian": gas on circular equatorial geodesics (prograde with the hole, or retrograde), only for r >= r_isco
  (none inside): u^t = (r^{3/2} +- a)/(r^{3/4} sqrt(r^{3/2} - 3 r^{1/2} +- 2 a)), Omega = +-1/(r^{3/2} +- a)
  (Bardeen, Press & Teukolsky 1972); g = 1/(u^t (1 - Omega lambda)).
* "cunningham": the same outside the ISCO; inside it the gas falls freely on the equatorial geodesic with the ISCO's
  energy and angular momentum (Cunningham 1975; Gralla, Lupsasca & Marrone 2020, PRD 102, 124004, Sec. III A: "We
  take the matter to orbit on circular geodesics outside of the Innermost Stable Circular Orbit (ISCO), and
  otherwise to infall on marginally stable geodesics"; App. B): u_t = -E_isco, u_phi = L_isco,
  u^r = -sqrt(R_timelike(r))/r^2; g = 1/(u^t - lambda u^phi - s_r u^r sqrt(R(r))/Delta), s_r the sign of the
  photon's p^r at emission (Chael, Johnson & Lupsasca 2021, ApJ 918, 6, Eq. 18).

Brightness is not computed by the kernel (review B5-K15): it returns r_n and g_n per crossing; ``disk_intensity``
forms I(alpha, beta) = sum_n f_n g_n^p J(r_n) with the choices stated: p = 4 gives the bolometric intensity
(Gralla, Lupsasca & Marrone 2020 Eq. 6), p = 3 the specific intensity of a flat spectrum (Chael et al. 2021 Eq. 16);
f_0 = 1 and f_n = f for n > 0 is a geometric fudge factor for a disk of finite thickness (GLM: f = 1.5, "a fudge
factor to account for the effects of geometrical thickness"; Chael et al.: f_n = 2/3). The default f = 1 is a
surface brightness per crossing, independent of the photon's angle to the disk; a thin optically thin layer would
instead weight each crossing by its path length through the layer (~ 1/|cos| of the angle between the photon and
the disk's normal in the gas frame), which this equatorial model omits.

The heavy part (all pixels at once) is the kernel "gravity.kerr_shadow" of ``lfphys.core.backend``: NumPy on the
CPU or CuPy on GPU 0 - elementwise closed forms (Ferrari roots, Carlson R_F, Jacobi functions by the AGM, the same
code on both devices); fp64 only. ``ShadowImage`` computes an image progressively, a band of rows per ``step()``, and
its state is a dict of NumPy arrays and floats (``state()``, ``ShadowImage.from_state``): saved and restored exactly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from lfphys.i18n import T

from .. import backend
from . import kerr, kerr_null as KN

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("The shadow of a Kerr black hole, photon rings and the image of a disk"),
    "statement": T("For every pixel of the distant observer's screen the ray is traced back in time in closed form: "
                   "whether it is captured (the shadow) or came from infinity; the equator crossings by order n = 0, "
                   "1, 2 … (the direct image of the disk, the lensing ring, the photon ring), the radius and redshift "
                   "g of the emitter at each crossing (a Keplerian disk outside the ISCO; inside it, free fall with "
                   "the ISCO constants after Cunningham). CPU or GPU."),
    "validity": T("vacuum solution of GR, 0 ≤ a < M; geometric optics; screen at infinity; the emitter is a thin "
                  "equatorial disk (a model of the source, not a law); no absorption or scattering; the brightness "
                  "(disk_intensity) is a choice of model: Σ f_n g_n^p J(r_n), p = 4 bolometric (p = 3 a flat "
                  "spectrum), f_n = 1 without a correction for the disk's thickness and the ray's path length in the "
                  "layer; n is the number of the equator crossing (half-periods in θ), not the number of turns around "
                  "the hole"),
    "basis": ["Bardeen, in Black Holes (Les Houches 1972), 1973", "Cunningham, ApJ 202, 788 (1975)",
              "Gralla & Lupsasca, Phys. Rev. D 101, 044031 and 044032 (2020)",
              "Johnson et al., Sci. Adv. 6, eaaz1310 (2020)", "Chael, Johnson & Lupsasca, ApJ 918, 6 (2021)",
              "Gralla, Lupsasca & Marrone, Phys. Rev. D 102, 124004 (2020)"],
    "conflicts": [],
}

KERNEL = "gravity.kerr_shadow"
EMITTERS = ("keplerian", "cunningham")


# --- emitters ------------------------------------------------------------------------------------------------------
def emitter_velocity(r, chi, model="cunningham", prograde=True, xp=np):
    """Contravariant (u^t, u^r, u^phi) of the equatorial emitter at radius r (NaN where the model has none)."""
    if model not in EMITTERS:
        raise ValueError(f"emitter must be one of {EMITTERS}")
    a = chi
    s = 1.0 if prograde else -1.0
    r = xp.asarray(r, dtype=xp.float64)
    r_isco = kerr.isco(chi, prograde)
    out = r >= r_isco
    rr = xp.where(out, r, 2.0 * r_isco)
    sr = xp.sqrt(rr)
    ut_k = (rr * sr + s * a) / (rr ** 0.75 * xp.sqrt(rr * sr - 3.0 * sr + s * 2.0 * a))
    om = s / (rr * sr + s * a)
    ut_k, ur_k, up_k = xp.where(out, ut_k, xp.nan), xp.where(out, 0.0, xp.nan), xp.where(out, ut_k * om, xp.nan)
    if model == "keplerian":
        return ut_k, ur_k, up_k
    E, L = kerr.circular_e_l(r_isco, chi, prograde)
    ri = xp.where(out, r_isco, r)
    dl = ri * ri - 2.0 * ri + a * a
    P = E * (ri * ri + a * a) - a * L
    # equatorial (Sigma = r^2): Sigma u^t = (r^2 + a^2) P/Delta - a (a E - L), Sigma u^phi = a P/Delta - (a E - L)
    ut = ((ri * ri + a * a) * P / dl - a * (a * E - L)) / (ri * ri)
    up = (a * P / dl - (a * E - L)) / (ri * ri)
    Rt = P * P - dl * (ri * ri + (L - a * E) ** 2)
    ur = -xp.sqrt(xp.maximum(Rt, 0.0)) / (ri * ri)
    return xp.where(out, ut_k, ut), xp.where(out, ur_k, ur), xp.where(out, up_k, up)


def redshift(r, lam, eta, kr_sign, chi, model="cunningham", prograde=True, xp=np):
    """g = E_obs/E_emit of a photon (lambda, eta) emitted at equatorial radius r by the model's emitter, the photon
    moving with sign(p^r) = kr_sign there."""
    a = chi
    ut, ur, up = emitter_velocity(r, chi, model, prograde, xp)
    dl = r * r - 2.0 * r + a * a
    R = (r * r + a * a - a * lam) ** 2 - dl * (eta + (lam - a) ** 2)
    pr = kr_sign * xp.sqrt(xp.maximum(R, 0.0)) / dl  # covariant p_r with E = 1
    return 1.0 / (ut - lam * up - pr * ur)


def redshift_tolerance(r, lam, eta, kr_sign, chi, model="cunningham", prograde=True, r_tol=0.0, k=16):
    """A-priori bound of the error of ``redshift`` at crossings (review B5-kerr-v15 K2): an error ``r_tol`` of the
    crossing radius propagated, |dg/dr| r_tol (dg/dr by central differences at fixed lambda, eta), plus the formula's
    own rounding. g = 1/D with D = u^t - lambda u^phi - p_r u^r, so dg = g^2 dD, dD <= k u (|u^t| + |lambda u^phi| +
    |p_r u^r|) + |u^r| e(p_r) + |p_r| e(u^r): the square roots of the photon's R (zero at its radial turning point)
    and, inside the ISCO, of the plunging gas's R_timelike (zero at the ISCO) amplify the rounding of the differences
    under them, e(sqrt X / d) = k u X_abs / (2 sqrt(X) |d|), X_abs the sum of the magnitudes X is formed from. k = 16:
    a few operations, each within 2 ulp on either device (CUDA's functions against glibc's). Measured 2026-10-29 on
    GPU 0 against the CPU (8 worlds, whole 160 x 160 screens, pixels farther than 0.05 M from the critical curve, r_tol
    from test_gpu_equals_cpu's bound): differences up to 9.8e-11 in g, within 0.36 of this bound everywhere; the input
    sensitivity |alpha dg/dalpha| + |beta dg/dbeta| + |g| times 128 u was exceeded up to 6600-fold inside the ISCO."""
    u = 2.0 ** -53
    a = chi
    r = np.asarray(r, dtype=float)
    lam, eta = np.asarray(lam, dtype=float), np.asarray(eta, dtype=float)
    ok = np.isfinite(r)
    rs = np.where(ok, r, 10.0)
    ks = np.where(ok, kr_sign, 1.0)
    g = redshift(rs, lam, eta, ks, chi, model, prograde)
    h = 1e-7 * rs
    dgdr = np.abs(redshift(rs + h, lam, eta, ks, chi, model, prograde)
                  - redshift(rs - h, lam, eta, ks, chi, model, prograde)) / (2.0 * h)
    ut, ur, up = emitter_velocity(rs, chi, model, prograde)
    dl = rs * rs - 2.0 * rs + a * a
    A = (rs * rs + a * a - a * lam) ** 2
    Bq = dl * (eta + (lam - a) ** 2)
    R = A - Bq
    pr = np.sqrt(np.maximum(R, 0.0)) / dl
    e_pr = k * u * (A + np.abs(Bq)) / (2.0 * np.sqrt(np.maximum(R, 1e-300)) * np.abs(dl))
    e_ur = np.zeros_like(rs)
    if model == "cunningham":
        r_isco = kerr.isco(chi, prograde)
        E, L = kerr.circular_e_l(r_isco, chi, prograde)
        P = E * (rs * rs + a * a) - a * L
        C = dl * (rs * rs + (L - a * E) ** 2)
        Rt = P * P - C
        e_ur = np.where(rs < r_isco, k * u * (P * P + np.abs(C)) / (2.0 * np.sqrt(np.maximum(Rt, 1e-300)) * rs * rs),
                        0.0)
    own = g * g * (k * u * (np.abs(ut) + np.abs(lam * up) + np.abs(pr * ur)) + np.abs(ur) * e_pr + np.abs(pr) * e_ur)
    return np.where(ok, dgdr * r_tol + own, np.nan)


def disk_intensity(r_n, g_n, emissivity, power=4.0, f_higher=1.0, r_out=math.inf):
    """I = sum_n f_n g_n^power J(r_n) over the crossings (n along axis 0; NaN crossings and r_n > r_out skipped):
    f_0 = 1, f_n = f_higher for n > 0 (module docstring: power 4 bolometric, 3 a flat spectrum; f a fudge factor for
    the disk's thickness). ``emissivity`` J(r): a function of radius, the source's emitted intensity profile."""
    r_n = np.asarray(r_n, float)
    g_n = np.asarray(g_n, float)
    ok = ~np.isnan(r_n) & ~np.isnan(g_n) & (r_n <= r_out)
    rr = np.where(ok, r_n, 1.0)
    f = np.ones(r_n.shape[0])
    f[1:] = f_higher
    f = f.reshape((-1,) + (1,) * (r_n.ndim - 1))
    return np.sum(np.where(ok, f * np.abs(g_n) ** power * emissivity(rr), 0.0), axis=0)


# --- the kernel ----------------------------------------------------------------------------------------------------
def _trace(xp, alpha, beta, theta_o, chi, n_max, emitter, prograde):
    res = KN.trace_back(alpha, beta, theta_o, chi, n_max, xp)
    g = []
    for n in range(n_max + 1):
        rn = res["r_n"][n]
        valid = ~xp.isnan(rn)
        rs = xp.where(valid, rn, 10.0)
        gn = redshift(rs, res["lam"], res["eta"], xp.where(valid, res["kr_sign_n"][n], 1.0), chi, emitter,
                      prograde, xp)
        g.append(xp.where(valid, gn, xp.nan))
    res["g_n"] = xp.stack(g)
    return res


def trace_screen(alpha, beta, theta_o, chi, n_max=2, emitter="cunningham", prograde=True, check=False,
                 aux=False) -> dict:
    """``kerr_null.trace_back`` plus the redshift ``g_n`` for the screen points (alpha, beta) (arrays of any shape),
    on the device chosen by ``core.backend`` (kernel "gravity.kerr_shadow"). Returns NumPy arrays: lam, eta, case,
    captured, tau_total, tau_turn, tau_n, r_n, kr_sign_n, face_n, g_n (the last five of shape (n_max + 1, ...)),
    n_cross."""
    if emitter not in EMITTERS:
        raise ValueError(f"emitter must be one of {EMITTERS}")
    alpha = np.asarray(alpha, float)
    beta = np.asarray(beta, float)
    alpha, beta = np.broadcast_arrays(alpha, beta)
    size = int(alpha.size)
    ch = backend.choose(KERNEL, size, check=check, footprint=size * 8 * (40 + 12 * (n_max + 1)), aux=aux)
    try:
        out = _trace(ch.xp, ch.xp.asarray(alpha), ch.xp.asarray(beta), theta_o, chi, n_max, emitter, prograde)
        res = {k: backend.to_numpy(v) for k, v in out.items()}
    except Exception as e:
        if not backend.is_out_of_memory(e):
            raise
        backend.release()
        backend.choose(KERNEL, size, check=check, force="cpu",
                       why=T("GPU: not enough memory, recomputed on the CPU"), aux=aux)
        res = _trace(np, alpha, beta, theta_o, chi, n_max, emitter, prograde)
    finally:
        if ch.device == "gpu":
            backend.release()
    return res


# --- the screen and a progressive image ----------------------------------------------------------------------------
@dataclass
class Screen:
    """A grid of square pixels on the observer's screen: ``nx`` x ``ny`` pixels, alpha in
    [alpha0 - half_width, alpha0 + half_width] (in M), beta centred on beta0 with the same pixel size. Row i has beta
    decreasing from the top; column j has alpha increasing."""
    nx: int
    ny: int
    half_width: float
    alpha0: float = 0.0
    beta0: float = 0.0

    @property
    def pixel(self) -> float:
        return 2.0 * self.half_width / self.nx

    def alpha(self):
        p = self.pixel
        return self.alpha0 - self.half_width + p * (np.arange(self.nx) + 0.5)

    def beta(self):
        """Square pixels: the rows span ny * pixel in beta."""
        p = self.pixel
        top = self.beta0 + 0.5 * p * self.ny
        return top - p * (np.arange(self.ny) + 0.5)

    def rows(self, i0, i1):
        """alpha, beta of rows i0..i1-1 as 2-D arrays."""
        a, b = np.meshgrid(self.alpha(), self.beta()[i0:i1])
        return a, b


_FIELDS_F = ("lam", "eta", "tau_total", "tau_turn")
_FIELDS_N = ("tau_n", "r_n", "kr_sign_n", "face_n", "g_n")


class ShadowImage:
    """The image of a Kerr black hole and an equatorial disk on a ``Screen``, computed a band of rows per ``step``.

    ``state()`` returns plain NumPy arrays and floats (the parameters, the next row and the filled arrays);
    ``ShadowImage.from_state(state)`` restores it exactly, and further steps give bit-identical results."""

    def __init__(self, chi, theta_o, screen: Screen, n_max=2, emitter="cunningham", prograde=True):
        KN._chk(chi)
        if not 0.0 <= theta_o <= math.pi:
            raise ValueError("theta_o must be in [0, pi] (radians)")
        if emitter not in EMITTERS:
            raise ValueError(f"emitter must be one of {EMITTERS}")
        self.chi, self.theta_o, self.screen = float(chi), float(theta_o), screen
        self.n_max, self.emitter, self.prograde = int(n_max), emitter, bool(prograde)
        ny, nx = screen.ny, screen.nx
        self.next_row = 0
        self.arrays = {k: np.full((ny, nx), np.nan) for k in _FIELDS_F}
        self.arrays.update({k: np.full((self.n_max + 1, ny, nx), np.nan) for k in _FIELDS_N})
        self.arrays["captured"] = np.zeros((ny, nx), np.int8)
        self.arrays["case"] = np.zeros((ny, nx), np.int8)
        self.arrays["n_cross"] = np.zeros((ny, nx), np.int8)

    @property
    def done(self) -> bool:
        return self.next_row >= self.screen.ny

    def step(self, rows: int = 32) -> int:
        """Compute the next ``rows`` rows; returns the number of rows computed (0 when done)."""
        if self.done:
            return 0
        i0 = self.next_row
        i1 = min(self.screen.ny, i0 + max(1, int(rows)))
        a, b = self.screen.rows(i0, i1)
        res = trace_screen(a, b, self.theta_o, self.chi, self.n_max, self.emitter, self.prograde)
        for k in _FIELDS_F:
            self.arrays[k][i0:i1] = res[k]
        for k in _FIELDS_N:
            self.arrays[k][:, i0:i1] = res[k]
        self.arrays["captured"][i0:i1] = res["captured"]
        self.arrays["case"][i0:i1] = res["case"]
        self.arrays["n_cross"][i0:i1] = res["n_cross"]
        self.next_row = i1
        return i1 - i0

    def run(self, rows: int = 64):
        while self.step(rows):
            pass
        return self

    def state(self) -> dict:
        sc = self.screen
        return {"chi": self.chi, "theta_o": self.theta_o, "n_max": self.n_max, "emitter": self.emitter,
                "prograde": self.prograde, "nx": sc.nx, "ny": sc.ny, "half_width": sc.half_width,
                "alpha0": sc.alpha0, "beta0": sc.beta0, "next_row": self.next_row,
                "arrays": {k: v.copy() for k, v in self.arrays.items()}}

    @classmethod
    def from_state(cls, st: dict) -> "ShadowImage":
        img = cls(st["chi"], st["theta_o"], Screen(st["nx"], st["ny"], st["half_width"], st["alpha0"], st["beta0"]),
                  st["n_max"], st["emitter"], st["prograde"])
        img.next_row = int(st["next_row"])
        arrays = {k: np.array(v, copy=True) for k, v in st["arrays"].items()}
        for k in _FIELDS_N:  # a state saved before a field existed (face_n, review B5-K9): NaN for the rows done
            arrays.setdefault(k, np.full((img.n_max + 1, img.screen.ny, img.screen.nx), np.nan))
        img.arrays = arrays
        return img


# --- the photon ring: images of a source ring along a screen direction ---------------------------------------------
def ring_image(chi, theta_o, r_source, angle, n, center=(0.0, 0.0)):
    """Screen distance rho_n from ``center`` along the direction ``angle`` (radians from the alpha axis) of the
    n-th image (n >= 1) of the equatorial circle r = r_source (> the photon orbit seen in that direction): the root
    of r_n(rho) = r_source outside the critical curve, by bisection on the closed-form tracer (r_n(rho) increases
    from the bound-orbit radius at the critical curve to infinity, then the n-th crossing ceases to exist).
    Returns (rho_n, rho_c), rho_c the critical-curve distance in that direction."""
    rho_c, _ = KN.critical_radius_at(chi, theta_o, angle, center)
    ca, sa = math.cos(angle), math.sin(angle)

    def rn(rho):
        res = KN.trace_back(np.array([center[0] + rho * ca]), np.array([center[1] + rho * sa]), theta_o, chi, n)
        v = float(res["r_n"][n][0])
        return math.inf if math.isnan(v) else v

    lo = rho_c * (1.0 + 1e-14)
    if rn(lo) >= r_source:
        raise ValueError("source ring inside the bound orbit seen in this direction")
    hi = rho_c * 1.001
    while rn(hi) < r_source:
        hi = rho_c + 2.0 * (hi - rho_c)
        if hi > 100.0 * rho_c:
            raise ValueError("no n-th image found")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi:
            break
        if rn(mid) < r_source:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi), rho_c


def capture_boundary(chi, theta_o, angle, center=(0.0, 0.0), rho_max=20.0):
    """Screen distance from ``center`` along ``angle`` at which the tracer's fate changes from captured to escaped
    (bisection to round-off): the computed shadow edge, for comparison with the closed-form critical curve."""
    ca, sa = math.cos(angle), math.sin(angle)

    def captured(rho):
        res = KN.trace_back(np.array([center[0] + rho * ca]), np.array([center[1] + rho * sa]), theta_o, chi, 0)
        return bool(res["captured"][0])

    lo, hi = 0.0, rho_max
    if not captured(lo) or captured(hi):
        raise ValueError("the center must be inside the shadow and rho_max outside")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi:
            break
        if captured(mid):
            lo = mid
        else:
            hi = mid
    return lo, hi


def capture_boundaries(chi, theta_o, angles, center=(0.0, 0.0), rho_max=20.0):
    """``capture_boundary`` along many screen directions at once: one call of the tracer per halving for all of them
    (each bisection stops at adjacent doubles, as the scalar one). Returns arrays (lo, hi): lo captured, hi escaped."""
    ang = np.atleast_1d(np.asarray(angles, dtype=float))
    ca, sa = np.cos(ang), np.sin(ang)
    cx, cy = center

    def captured(rho):
        return KN.trace_back(cx + rho * ca, cy + rho * sa, theta_o, chi, 0)["captured"].astype(bool)

    lo, hi = np.zeros(ang.shape), np.full(ang.shape, float(rho_max))
    if not captured(lo).all() or captured(hi).any():
        raise ValueError("the center must be inside the shadow and rho_max outside")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        live = (mid > lo) & (mid < hi)
        if not live.any():
            break
        cap = captured(mid)
        lo = np.where(live & cap, mid, lo)
        hi = np.where(live & ~cap, mid, hi)
    return lo, hi


def edge_tolerance(chi, theta_o, angles, rho, center=(0.0, 0.0), h=1e-6):
    """A-priori bound of the distance between the tracer's shadow edge and the exact critical curve along screen
    directions, at the edge's distance ``rho`` from ``center`` (review B5-K1; the derivation of
    test_kerr_shadow.test_shadow_edge_is_the_critical_curve). The fate is decided by the sign of
    d34 = -A/2 - z^2 - B/(4z) (= (r4 - r3)^2/4 where real), computed with round-off e_d <= 16 u (|A|/2 + z^2 +
    |B|/(4z)), so the edge may move by e_d/|d d34/d rho| (the slope by central differences over +-h); plus the
    closed-form curve's own error mapped to the screen (1e-13 rho: the gamma_12 bound of lambda, eta in
    test_kerr_null) and the bisection's resolution 2 u rho. The width of the final bracket (hi - lo) is the caller's
    to add."""
    u = 2.0 ** -53
    ang = np.atleast_1d(np.asarray(angles, dtype=float))
    rho = np.broadcast_to(np.asarray(rho, dtype=float), ang.shape)
    ca, sa = np.cos(ang), np.sin(ang)

    def d34(r):
        lam, eta = KN.screen_to_constants(center[0] + r * ca, center[1] + r * sa, theta_o, chi)
        ro = KN.radial_roots(lam, eta, chi)
        A, B, z = ro["A"], ro["B"], ro["z"]
        return -A / 2 - z * z - B / (4 * z), 16 * u * (np.abs(A) / 2 + z * z + np.abs(B) / (4 * z))

    d1, e1 = d34(rho + h)
    d0, _ = d34(rho - h)
    slope = np.abs(d1 - d0) / (2 * h)
    return e1 / slope + 1e-13 * rho + 2 * u * rho


def shadow_size(chi, theta_o, n_angles=128, rho_max=20.0):
    """The size of the shadow measured on the tracer's own edge (review B5-K10), in the convention of
    ``theories.alternatives.johannsen_metric.shadow_size`` ("extremes"): the centre half-way between the extreme
    alpha, which for the Kerr shadow (symmetric under beta -> -beta) lie on the symmetry axis (the edge along the
    directions 0 and pi from the screen origin); then the median diameter over ``n_angles`` equally spaced directions
    from it and delta = d/(6 sqrt 3) - 1 (EHT 2022 Sgr A* Paper VI Eq. 14). The same quantities of the closed-form
    critical curve (``kerr_null.critical_radii``, about the same centre) come with them, and a-priori bounds of the
    differences: each traced radius within ``edge_tolerance`` + its bracket of the curve, so the median diameter
    within twice the largest of them; the centre within the mean of the two axis bounds.
    Returns a dict: center_alpha, center_alpha_closed, center_tol; radii, radii_closed, radii_tol (arrays);
    median_diameter, median_diameter_closed, delta, delta_closed, delta_tol."""
    d_sch = 6.0 * math.sqrt(3.0)
    axis = np.array([0.0, math.pi])
    lo, hi = capture_boundaries(chi, theta_o, axis, rho_max=rho_max)
    edge = 0.5 * (lo + hi)
    tol_axis = edge_tolerance(chi, theta_o, axis, edge) + (hi - lo)
    rc_axis, _ = KN.critical_radii(chi, theta_o, axis)
    cx = 0.5 * (edge[0] - edge[1])
    cx_closed = 0.5 * (rc_axis[0] - rc_axis[1])
    ang = 2.0 * math.pi * np.arange(n_angles) / n_angles
    lo, hi = capture_boundaries(chi, theta_o, ang, (cx, 0.0), rho_max)
    rad = 0.5 * (lo + hi)
    rad_tol = edge_tolerance(chi, theta_o, ang, rad, (cx, 0.0)) + (hi - lo)
    rad_closed, _ = KN.critical_radii(chi, theta_o, ang, (cx, 0.0))
    d, d_closed = 2.0 * float(np.median(rad)), 2.0 * float(np.median(rad_closed))
    return {"center_alpha": cx, "center_alpha_closed": cx_closed, "center_tol": float(0.5 * tol_axis.sum()),
            "radii": rad, "radii_closed": rad_closed, "radii_tol": rad_tol,
            "median_diameter": d, "median_diameter_closed": d_closed,
            "delta": d / d_sch - 1.0, "delta_closed": d_closed / d_sch - 1.0,
            "delta_tol": 2.0 * float(rad_tol.max()) / d_sch}


# --- registration --------------------------------------------------------------------------------------------------
def _bench(size: int, xp, cplx):
    """One screen of ``size`` pixels as a call does it: the coordinates to the device, three ring orders, the
    results back to the host."""
    n = max(8, int(round(math.sqrt(size))))
    sc = Screen(n, n, 8.0)
    a, b = sc.rows(0, n)
    out = _trace(xp, xp.asarray(a), xp.asarray(b), math.radians(60.0), 0.9, 2, "cunningham", True)
    for v in out.values():
        backend.to_numpy(v)


backend.register(backend.KernelSpec(
    KERNEL, T("Kerr shadow: ray tracing of the screen"),
    T("for every pixel: the fate of the ray (shadow), the equator crossings n = 0, 1, 2, the radius and redshift of "
      "the emitter (P14.3)"),
    gpu=True,
    precisions={"fp64": {"allowed": True},
                "fp32": {"allowed": False, "why": T("the photon-ring radii lose accuracy near the critical curve "
                                                    "(k → 1); not tested")}},
    crossover=256 * 256,
    crossover_note=T("measured 2026-10-29 on an RTX 2080 Ti against one CPU thread (NumPy), fp64, with the results "
                     "transferred, χ = 0.9, 60°, n = 0…2: 128×128: CPU 36 ms, GPU 41 ms; 256×256: 134 and 42 ms "
                     "(×3.2); 512×512: 623 and 48 ms (×13); the GPU time is almost constant (kernel launches); "
                     "“Measure again” refines this"),
    bench=_bench, bench_sizes=(32 * 32, 64 * 64, 128 * 128, 256 * 256, 512 * 512)))
