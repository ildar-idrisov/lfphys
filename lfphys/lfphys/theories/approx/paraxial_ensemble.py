# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The run's expected screen distribution, near-field map and flow lines, computed without Monte-Carlo noise.

In the paraxial engine every random transverse influence on a particle SHIFTS its pattern rigidly:
* a source point x_s (line source of width s at distance L1): at the plane z the pattern moves by -x_s z / L1;
* a momentum kick kappa in the slit plane (a scattered probe photon): it moves by kappa z / k;
* a GRW hit at distance z' < z (a Gaussian localisation of width r_C is, for the density matrix, a random kick
  q ~ N(0, 1/(2 r_C^2))): it moves by q (z - z') / k.
These are exact identities of the Fresnel solution (in fresnel.py the amplitude depends on x only through
x - shift, up to a phase common to all slits). The ensemble pattern is the pattern of the averaged marks convolved
with the distribution of the total shift Delta, done by FFT with the characteristic function phi(w) = E[exp(-i w Delta)]:
* source:      sinc(w S),  S = s z / (2 L1)                                        (uniform source)
* microscope:  (1 - p) + p exp(-i w c n_ix) I(w c),  c = k_p z / k,  I(a) = Integral_{-1}^{1} f(u) exp(i a u) du,
               f(u) = (3/8) [(1 + p_x^2) + (1 - 3 p_x^2) u^2]: the dipole pattern (3/8pi)(1 - (n.p)^2) marginalised
               to n_x = u (p_x: the x component of the dipole axis); I in closed form;
* GRW:         exp(-Lam_z [1 - sqrt(pi) erf(a) / (2a)]),  a = |w| z / (2 k r_C),  Lam_z = rate * z / v.
The spectrum (log-normal in lambda) is integrated by Gauss-Hermite nodes; each node is divided by its own Parseval
flux lambda z a N, so the result is the detection density per emitted particle.

Flow lines of the averaged current: for a slit-plane kick kappa, Im(Psi^dag dPsi) gains kappa |Psi|^2, so
J_ens = J_0 (*) rho + D_0 (*) (kappa rho), with E[kappa exp(-i w Delta)] = (k/z) E[Delta exp(-i w Delta)] in closed
form. A GRW kick acts at z' > 0 with momentum q, not as a slit-plane kick, so flow lines are not drawn for GRW runs.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special

from lfphys.i18n import T
from ..alternatives.collapse import grw_shift_cf
from . import paraxial as fresnel

ABOUT = {
    "layer": 'theories', "kind": 'approximation',
    "title": T("The expected pattern of an ensemble in the paraxial approximation (without Monte Carlo)"),
    "statement": T("Each random transverse kick (a point of the source, the recoil of a scattered photon, a GRW hit) "
                   "shifts the paraxial pattern as a whole; the ensemble's pattern is a convolution with the "
                   "distribution of the shift, through characteristic functions in closed form; the spectrum: "
                   "Gauss–Hermite nodes."),
    "validity": T("paraxial approximation (the shift identity is exact within it)"),
    "basis": ['van Cittert 1934, Zernike 1938', 'Chapman et al., PRL 75, 3783 (1995)'],
    "conflicts": [T("lfphys.core.optics.scalar: the shift identity is exact only in the paraxial approximation; "
                    "outside it the ensemble's pattern differs from exact propagation")],
}

GH_NODES = 24


def lam_nodes(lam0: float, sigma: float, n: int = GH_NODES):
    """Log-normal spectrum ln(lambda/lambda0) ~ N(0, sigma^2): nodes and weights (sum 1)."""
    if sigma <= 0:
        return np.array([lam0]), np.array([1.0])
    x, w = special.roots_hermitenorm(n)
    return lam0 * np.exp(sigma * x), w / w.sum()


def _moments(a):
    """Integral_{-1}^{1} u^m exp(i a u) du for m = 0..3 (vectorised; series for small |a|)."""
    a = np.asarray(a, float)
    s = np.abs(a) < 1e-2
    b = np.where(s, 1.0, a)
    sn, cs = np.sin(b), np.cos(b)
    m0 = np.where(s, 2 - a**2 / 3 + a**4 / 60, 2 * sn / b)
    m2 = np.where(s, 2 / 3 - a**2 / 5 + a**4 / 84, 2 * ((b * b - 2) * sn + 2 * b * cs) / b**3)
    m1 = np.where(s, 1j * (2 * a / 3 - a**3 / 15), 2j * (sn - b * cs) / b**2)
    m3 = np.where(s, 1j * (2 * a / 5 - a**3 / 21), 2j * ((3 * b * b - 6) * sn - (b**3 - 6 * b) * cs) / b**4)
    return m0, m1, m2, m3


class Model:
    """The distributions of the shifts, independent of individual particles."""

    def __init__(self, k0, lam_sigma, slits, a, L1, src_width, p_scat, kp, n_ix, p_x, grw_rate, v_of_k, rc):
        self.k0, self.sigma, self.slits, self.a, self.L1 = k0, lam_sigma, np.asarray(slits, float), a, L1
        self.s = src_width if math.isfinite(L1) else 0.0
        self.p, self.kp, self.n_ix, self.p_x = p_scat, kp, n_ix, p_x
        self.grw, self.v_of_k, self.rc = grw_rate, v_of_k, rc
        self.lams, self.wls = lam_nodes(2 * math.pi / k0, lam_sigma)

    @property
    def shifts(self) -> bool:
        return self.s > 0 or self.p > 0 or self.grw > 0

    def _src(self, w, z):
        if self.s <= 0:
            return np.ones_like(w, complex), np.zeros_like(w, complex)
        S = self.s * z / (2 * self.L1)
        x = w * S
        sm = np.abs(x) < 1e-4
        xb = np.where(sm, 1.0, x)
        phi = np.where(sm, 1 - x * x / 6, np.sin(xb) / xb)
        # E[Delta e^{-i w Delta}] = i dphi/dw = i S (cos x / x - sin x / x^2)
        e1 = 1j * S * np.where(sm, -x / 3, np.cos(xb) / xb - np.sin(xb) / xb**2)
        return phi.astype(complex), e1

    def _mic(self, w, k, z):
        if self.p <= 0:
            return np.ones_like(w, complex), np.zeros_like(w, complex)
        c = self.kp * z / k
        m0, m1, m2, m3 = _moments(w * c)
        A, B = 0.375 * (1 + self.p_x**2), 0.375 * (1 - 3 * self.p_x**2)
        ph = np.exp(-1j * w * c * self.n_ix)
        Iu0 = A * m0 + B * m2  # Integral f(u) e^{i a u}
        Iu1 = A * m1 + B * m3  # Integral u f(u) e^{i a u}
        phi = (1 - self.p) + self.p * ph * Iu0
        # Delta = c (n_ix - u):  E[Delta e^{-i w Delta}] = p c ph (n_ix Iu0 - Iu1)
        e1 = self.p * c * ph * (self.n_ix * Iu0 - Iu1)
        return phi, e1

    def _grw(self, w, k, z):
        if self.grw <= 0:
            return np.ones_like(w, complex)
        return grw_shift_cf(w, k, z, self.grw * z / self.v_of_k(k), self.rc)

    def cf(self, w, k, z, with_grw=True):
        ps, _ = self._src(w, z)
        pm, _ = self._mic(w, k, z)
        f = ps * pm
        return f * self._grw(w, k, z) if with_grw else f

    def kick_cf(self, w, k, z):
        """E[kappa exp(-i w Delta)] for the slit-plane shifts (source tilt and microscope), kappa = k Delta / z."""
        ps, es = self._src(w, z)
        pm, em = self._mic(w, k, z)
        return (k / z) * (es * pm + ps * em)

    def max_shift(self, z, k):
        sh = 0.0
        if self.s > 0:
            sh += 0.5 * self.s * z / self.L1
        if self.p > 0:
            sh += 2 * self.kp * z / k
        if self.grw > 0:
            lz = self.grw * z / self.v_of_k(k)
            sh += 6 * math.sqrt(max(lz, 1.0)) * z / (k * self.rc * math.sqrt(2))
        return sh


def _convolve(P, dx, cf):
    """Linear convolution of a grid function with the shift distribution (characteristic function cf(w), w in rad/m):
    density moves from x to x + Delta; mass moved beyond the grid leaves it (zero padding, no wrap-around)."""
    n = len(P)
    m = 1 << int(math.ceil(math.log2(2 * n + 2)))
    w = 2 * math.pi * np.fft.fftfreq(m, d=dx)
    return np.real(np.fft.ifft(np.fft.fft(P, m) * cf(w))[:n])


def _extended(x, pad):
    dx = float(x[1] - x[0])
    npad = int(math.ceil(pad / dx)) + 4
    xe = np.concatenate([x[0] - dx * np.arange(npad, 0, -1), x, x[-1] + dx * np.arange(1, npad + 1)])
    return xe, npad


def screen(model: Model, x, z, Gs, eff=1.0):
    """Expected detection density per emitted particle on the grid x at distance z, one row per Gram matrix in Gs
    (the readouts; unnormalised marks, so absorption by elements is included). Born rule p = 2."""
    dx = float(x[1] - x[0])
    out = np.zeros((len(Gs), len(x)))
    nsl = len(model.slits)
    for lam, wl in zip(model.lams, model.wls):
        k = 2 * math.pi / lam
        xe, npad = _extended(x, model.max_shift(z, k))
        A = fresnel.slit_amplitudes(xe, z, k, model.slits, model.a, model.L1)
        norm = lam * z * model.a * nsl
        for r, G in enumerate(Gs):
            P0 = fresnel.intensity(A, G) / norm
            if model.shifts:
                P0 = _convolve(P0, dx, lambda w: model.cf(w, k, z))
            out[r] += wl * eff * P0[npad:npad + len(x)]
    return out


def near_field(model: Model, G, z_max, n_z=260, n_xi=300, half0=None, theta_env=None, with_current=False):
    """Ensemble |Psi|^2 behind the slits on the display grid (z from 2a to z_max, log; x = xi w(z)), each column
    normalised to its maximum; with_current: also the averaged-current ratio dx/dz on the same grid (no GRW)."""
    lam0 = 2 * math.pi / model.k0
    span = (model.slits.max() - model.slits.min()) + model.a
    half0 = half0 or 0.75 * span
    theta_env = theta_env or 2.5 * lam0 / model.a
    z0 = 2.0 * model.a
    zs = z0 * (z_max / z0) ** np.linspace(0.0, 1.0, n_z)
    xi = np.linspace(-1.0, 1.0, n_xi)
    wz = np.sqrt(half0**2 + (theta_env * zs) ** 2)
    I = np.zeros((n_z, n_xi))
    J = np.zeros((n_z, n_xi))
    Dk = np.zeros((n_z, n_xi))
    nsl = len(model.slits)
    for iz, z in enumerate(zs):
        x = xi * wz[iz]
        dx = float(x[1] - x[0])
        for lam, wl in zip(model.lams, model.wls):
            k = 2 * math.pi / lam
            xe, npad = _extended(x, min(model.max_shift(z, k), 40 * wz[iz]))
            norm = lam * z * model.a * nsl
            sl = slice(npad, npad + n_xi)
            if with_current:
                A, dA = fresnel.slit_amplitudes(xe, z, k, model.slits, model.a, model.L1, deriv=True)
                Jn, Dn = fresnel.current(A, dA, G)
                Jn, Dn = Jn / norm, Dn / norm
            else:
                Dn = fresnel.intensity(fresnel.slit_amplitudes(xe, z, k, model.slits, model.a, model.L1), G) / norm
            if model.shifts:
                Dc = _convolve(Dn, dx, lambda w: model.cf(w, k, z))
                if with_current:
                    Jc = _convolve(Jn, dx, lambda w: model.cf(w, k, z, with_grw=False))
                    Jc += _convolve(Dn, dx, lambda w: model.kick_cf(w, k, z))
            else:
                Dc = Dn
                if with_current:
                    Jc = Jn
            I[iz] += wl * Dc[sl]
            if with_current:
                J[iz] += wl * Jc[sl]
                Dk[iz] += wl * k * Dc[sl]
    out = {"z": zs, "xi": xi, "w": wz, "I": (I / np.maximum(I.max(axis=1, keepdims=True), 1e-300)).astype(np.float32),
           "half0": half0, "theta_env": theta_env}
    if with_current:
        floor = 1e-12 * np.max(Dk, axis=1, keepdims=True)
        out["vel"] = np.where(Dk > floor, J / np.maximum(Dk, 1e-300), 0.0)
    return out


def flow_lines(mp, slits, a, weights, n=40, rng=None):
    """Flow lines dx/dz of the averaged current through the gridded field (linear in xi, Heun between columns),
    started in the slits proportionally to the transmitted intensity."""
    rng = rng or np.random.default_rng(0)
    w = np.asarray(weights, float)
    if w.sum() <= 0 or "vel" not in mp:
        return None
    zs, xi, wz, V = mp["z"], mp["xi"], mp["w"], mp["vel"]
    js = rng.choice(len(slits), size=n, p=w / w.sum())
    u = (np.arange(n) + 0.5) / n
    rng.shuffle(u)
    x = np.sort(np.asarray(slits)[js] + (u - 0.5) * a * 0.96)
    out = np.empty((len(zs), n))
    out[0] = x

    def vel(xx, iz):
        q = np.clip((xx / wz[iz] + 1) / 2 * (len(xi) - 1), 0, len(xi) - 1.000001)
        i = q.astype(int)
        f = q - i
        return V[iz, i] * (1 - f) + V[iz, i + 1] * f

    for iz in range(len(zs) - 1):
        h = zs[iz + 1] - zs[iz]
        k1 = vel(x, iz)
        k2 = vel(x + h * k1, iz + 1)
        x = x + 0.5 * h * (k1 + k2)
        out[iz + 1] = x
    return {"z": zs, "x": out}
