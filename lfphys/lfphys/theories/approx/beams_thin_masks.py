# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Thin masks that make or probe optical vortices (plan P14.7; moved here from the core after review B8-beams, O7):
a spiral phase plate and a fork hologram as transmissions t(x, y) on the plane z = 0, and a spinning rough surface as
a thin phase screen. The field just behind the mask is taken to be the incident field times t (the thin-element, i.e.
Kirchhoff, boundary condition, as in ``lfphys.theories.approx.kirchhoff``); from there on the propagation is exact
(``lfphys.core.optics.angular_spectrum``, or for the spiral plate the order-l Hankel route of
``lfphys.core.optics.beams``). The boundary condition is the approximation: a real plate or hologram has a thickness,
edges and a vector response, which the engine solves in full in ``lfphys.core.em.fdtd`` (structured media) and
``lfphys.core.em.slit`` (a conducting screen); the thin mask differs from them where the structure is of the order of
the wavelength (the step of a plate, a hologram period of a few lambda, the scale of the roughness).

* **Spiral phase plate** of charge l: transmission exp(i l phi) (continuous), or with N steps
  exp(i 2 pi l floor(N phi / 2 pi) / N) (phi in [0, 2 pi)); its thickness h(phi) = l lambda phi / (2 pi (n - 1)) for a
  plate of index n in air (for drawing). A Gaussian behind a continuous plate is an eigenstate of L_z with l per
  photon, but not one Laguerre-Gauss mode (a superposition over p: E. Karimi et al., Opt. Lett. 32, 3053 (2007),
  arXiv:0712.0782, verified). Its order-l spectrum: ``lfphys.core.optics.beams.gaussian_vortex_spectrum``.
* **Fork hologram** of charge l and period Lambda (K = 2 pi / Lambda), the phase function f = l phi - K x:
  amplitude t = (1 + cos f)/2, binary amplitude t = [cos f > 0], or a blazed phase t = exp(i (f mod 2 pi)) (= e^{if}).
  Its Fourier series t = sum_m c_m exp(i m f) gives the orders: order m carries exp(i m l phi) (charge m l) and the
  transverse wave number -m K, i.e. leaves at sin(theta_m) = -m K / k (the fork-hologram principle; V. Yu. Bazhenov,
  M. V. Vasnetsov, M. S. Soskin, JETP Lett. 52, 429 (1990); N. R. Heckenberg et al., Opt. Lett. 17, 221 (1992):
  texts not obtained, the series is derived here and the charges are measured in the tests).
  c_m: amplitude c_0 = 1/2, c_+-1 = 1/4; binary c_0 = 1/2, c_m = sin(m pi/2)/(m pi); blazed c_1 = 1, others 0.
  **On a grid** the binary mask's sharp edges carry all orders; point samples alias the orders beyond the grid's band
  back into it (on 9.8 samples per period the sampled duty cycle is 0.526, c_0 5 % too large, and orders near
  m = 2 pi / (K dx) land among the propagating ones; review B8-beams, O8). ``fork_hologram(..., m_max=M)`` therefore
  gives the binary mask as its Fourier series up to the grid's band (``fork_band``): the orders |m| <= M are exactly
  the declared c_m, the rest (evanescent for any grid finer than lambda / 2 with K <= k) are left out.
  At the fork's centre a sample takes the mask's mean around it (c_0): the phase l phi is undefined there.
  ``order_powers`` measures each order's share of the propagating power in the angular spectrum of a sampled field
  (the cell |k_x + m K| < K / 2); the thin mask's prediction of the same quantity is ``order_powers_closed_form``
  (each order m is a Gaussian behind a spiral plate of charge m l, shifted by -m K: ``fork_spectrum`` from the
  closed-form ``beams.gaussian_vortex_spectrum``), the orders' overlapping wide-angle tails included (their spectra
  fall only as q^-2: ``order_leakage`` gives the share of an order's own power outside its cell). Without the overlap
  the share would be ``order_power_reference``, |c_m|^2 / sum over the propagating orders of |c_j|^2 (Parseval); for
  the default fork of v16 the overlap moves it by 0.01-0.03, more than the grid's error (review B8-beams, O8).
* **Spinning rough surface** (M. P. J. Lavery, F. C. Speirits, S. M. Barnett, M. J. Padgett, Science 341, 537 (2013),
  accepted manuscript, Eqs. 3-4; the closed forms of the shifts are in ``lfphys.core.optics.beams_rotation``): a thin
  phase screen rho = exp(i phase(r)) of seeded Gaussian bumps, turned exactly; the light scattered onto the axis is
  int U rho dA (``on_axis_amplitude``, polar quadrature ``polar_grid``), scalar ("there is no dependence upon
  polarisation").
"""

from __future__ import annotations

import math

import numpy as np

from ...core.optics import angular_spectrum as AS
from ...core.optics import beams as B

ABOUT = {
    "layer": "theories", "kind": "approximation",
    "title": "Тонкие маски для оптических вихрей: спиральная пластинка, голограмма-«вилка», вращающийся шероховатый экран",
    "statement": "Маска — пропускание t(x, y) в плоскости z = 0 (граничное условие тонкого элемента, как у Кирхгофа): "
                 "спиральная пластинка exp(ilφ) (или ступенчатая), голограмма-вилка с фазой lφ − Kx (амплитудная, "
                 "бинарная — на сетке рядом Фурье до полосы сетки, блазированная); m-й порядок вилки несёт заряд m·l "
                 "и уходит под углом sin θ_m = −mK/k; мощность порядков по угловому спектру; шероховатый диск — тонкий "
                 "фазовый экран, свет, рассеянный на ось. Дальше поле распространяется точно (ядро).",
    "validity": "структуры много больше длины волны: тонкий элемент без толщины, краёв и векторного отклика; "
                "скалярно (поляризация не участвует)",
    "basis": ["Karimi et al., Opt. Lett. 32, 3053 (2007) — пучок за спиральной пластинкой",
              "Bazhenov, Vasnetsov, Soskin, JETP Lett. 52, 429 (1990); Heckenberg et al., Opt. Lett. 17, 221 (1992) "
              "(тексты не получены)",
              "Lavery, Speirits, Barnett, Padgett, Science 341, 537 (2013), ур. 3, 4"],
    "conflicts": ["lfphys.core.em.fdtd: пластинка или голограмма конечной толщины с векторным откликом отличается от "
                  "тонкой маски, когда структура порядка длины волны (ступень пластинки, период в несколько λ)",
                  "lfphys.core.em.slit: векторное решение для щелей в проводящем экране расходится с граничными "
                  "значениями тонкой маски у структур в несколько λ (как у theories.approx.kirchhoff)"],
}


def azimuth(x, y):
    """phi in [0, 2 pi)."""
    return np.mod(np.arctan2(np.asarray(y, float), np.asarray(x, float)), 2 * math.pi)


# --- the spiral phase plate -----------------------------------------------------------------------------------------
def spiral_phase_plate(x, y, l: int, steps: int | None = None):
    """Transmission of a spiral phase plate of charge l: exp(i l phi), or with ``steps`` steps per turn. A sample at
    the centre (x = y = 0, phi undefined) takes the plate's mean around it: 0 for the continuous plate (l != 0),
    (1/N) sum_j exp(2 pi i l j / N) for N steps."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    phi = azimuth(x, y)
    if steps:
        phi = 2 * math.pi * np.floor(steps * phi / (2 * math.pi)) / steps
        centre = complex(np.mean(np.exp(2j * math.pi * l * np.arange(steps) / steps)))
    else:
        centre = 0.0 if l else 1.0
    return np.where((x == 0) & (y == 0), centre, np.exp(1j * l * phi))


def spp_thickness(phi, l: int, lam: float, n_index: float = 1.5, steps: int | None = None):
    """Thickness of the plate (index n_index in air) along the azimuth phi in [0, 2 pi): l lam phi / (2 pi (n - 1))."""
    phi = np.mod(np.asarray(phi, float), 2 * math.pi)
    if steps:
        phi = 2 * math.pi * np.floor(steps * phi / (2 * math.pi)) / steps
    return abs(l) * lam * (phi if l >= 0 else 2 * math.pi - phi) / (2 * math.pi * (n_index - 1))


# --- the fork hologram ----------------------------------------------------------------------------------------------
KINDS = ("amplitude", "binary", "blazed")


def fork_order_coefficient(kind: str, m: int) -> float:
    """c_m of the hologram's Fourier series in exp(i m f)."""
    if kind == "amplitude":
        return {0: 0.5, 1: 0.25, -1: 0.25}.get(m, 0.0)
    if kind == "binary":  # sin(m pi/2) / (m pi), with the even orders exactly 0 (not ~1e-17 from the sine)
        if m == 0:
            return 0.5
        return 0.0 if m % 2 == 0 else (1.0 if ((m - 1) // 2) % 2 == 0 else -1.0) / (m * math.pi)
    if kind == "blazed":
        return 1.0 if m == 1 else 0.0
    raise ValueError(f"fork_order_coefficient: kind one of {KINDS}")


def fork_band(dx: float, period: float) -> int:
    """The largest order |m| a grid of step dx represents: |m| K < pi / dx (K = 2 pi / period)."""
    return max(0, int(math.ceil(period / (2 * dx))) - 1)


def fork_hologram(x, y, l: int, period: float, kind: str = "amplitude", m_max: int | None = None):
    """Transmission of a fork hologram of charge l and period ``period`` (see the module's docstring). With ``m_max``
    the binary mask is its Fourier series sum_{|m| <= m_max} c_m exp(i m f) (for a grid: ``fork_band``; the amplitude
    and blazed masks are smooth in f and need no band limit). At the fork's centre (x = y = 0, where the phase l phi is
    undefined, l != 0) a sample takes the mask's mean around it, c_0 (a point value there would put a spurious flat
    spectrum of the cell's size into every order)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    f = l * np.arctan2(y, x) - 2 * math.pi / period * x
    if kind == "amplitude":
        t = (0.5 * (1 + np.cos(f))).astype(complex)
    elif kind == "binary":
        if m_max is None:
            t = (np.cos(f) > 0).astype(complex)
        else:
            t = sum(fork_order_coefficient("binary", m) * np.exp(1j * m * f) for m in range(-m_max, m_max + 1)
                    if fork_order_coefficient("binary", m) != 0) + 0 * f
    elif kind == "blazed":
        t = np.exp(1j * np.mod(f, 2 * math.pi))
    else:
        raise ValueError(f"fork_hologram: kind one of {KINDS}")
    if l:
        t = np.where((x == 0) & (y == 0), fork_order_coefficient(kind, 0), t)
    return t


def order_direction(m: int, period: float, k: float) -> float:
    """sin(theta_m) = -m K / k of order m (NaN for an evanescent order)."""
    s = -m * 2 * math.pi / period / k
    return s if abs(s) < 1 else float("nan")


def order_position(m: int, period: float, k: float, z: float) -> float:
    """x of the centre of order m at distance z (a beam leaving the axis at z = 0 along its direction)."""
    s = order_direction(m, period, k)
    return z * s / math.sqrt(1 - s * s)


def propagating_orders(kind: str, period: float, k: float, m_max: int = 60) -> list:
    """The orders m (|m| <= m_max) with c_m != 0 that propagate (|m| K < k)."""
    K = 2 * math.pi / period
    return [m for m in range(-m_max, m_max + 1) if abs(m) * K < k and fork_order_coefficient(kind, m) != 0]


def order_power_reference(kind: str, period: float, k: float) -> dict:
    """The thin mask's share of the propagating power in each propagating order: |c_m|^2 / sum_j |c_j|^2 over the
    propagating orders (Parseval for the mask's Fourier series; the orders leave as separate beams)."""
    ms = propagating_orders(kind, period, k)
    tot = sum(fork_order_coefficient(kind, m) ** 2 for m in ms)
    return {m: fork_order_coefficient(kind, m) ** 2 / tot for m in ms}


def order_powers(U, dx: float, k: float, period: float, orders, pad: int = 1) -> dict:
    """The share of the propagating power of a field sampled on a square grid (step dx; axes x, y) in the
    angular-spectrum cell of each order m: |k_x + m K| < K / 2, |k| < k (Parseval: the same on every plane z behind
    the mask). ``pad`` > 1 zero-pads the FFT (a finer spectral grid, the same sums)."""
    U = np.asarray(U, complex)
    n = U.shape[0] * pad
    F = np.fft.fft2(U, (n, n))
    kx = 2 * math.pi * np.fft.fftfreq(n, dx)
    KX, KY = np.meshgrid(kx, kx, indexing="ij")
    prop = KX * KX + KY * KY < k * k
    P = np.abs(F) ** 2
    tot = float(np.sum(P[prop]))
    K = 2 * math.pi / period
    return {m: float(np.sum(P[prop & (np.abs(KX + m * K) < 0.5 * K)])) / tot for m in orders}


def fork_spectrum(kind: str, l: int, w0: float, period: float, KX, KY, m_max: int):
    """The angular spectrum U~(k) = int U0 e^{-i k.r} d^2r of a Gaussian exp(-r^2/w0^2) on the fork hologram, in
    closed form from the mask's Fourier series (orders |m| <= m_max): sum_m c_m 2 pi (-i)^{m l} e^{i m l phi'}
    A_{m l}(|k'|), k' = (k_x + m K, k_y), A_n = ``beams.gaussian_vortex_spectrum`` (each order is a Gaussian behind a
    plate of charge m l, shifted by -m K). A second route to the field the grid's FFT gives."""
    K = 2 * math.pi / period
    KX, KY = np.asarray(KX, float), np.asarray(KY, float)
    out = np.zeros(np.broadcast(KX, KY).shape, complex)
    for m in range(-m_max, m_max + 1):
        c = fork_order_coefficient(kind, m)
        if c == 0:
            continue
        n = m * l
        fn, _ = B.gaussian_vortex_spectrum(n, w0)
        kx = KX + m * K
        out += c * 2 * math.pi * (-1j) ** n * np.exp(1j * n * np.arctan2(KY, kx)) * fn(np.hypot(kx, KY))
    return out


def order_powers_closed_form(kind: str, l: int, w0: float, period: float, k: float, dx: float, n: int, orders,
                             m_max: int, images: int = 0) -> dict:
    """What ``order_powers`` measures, from ``fork_spectrum`` on the same k grid (an n x n FFT of step dx, the
    propagating points only): the thin mask's prediction of each order's share of the propagating power, the orders'
    overlapping wide-angle tails included. ``images`` > 0 adds the grid's periodic images k + 2 pi p / dx,
    |p_x|, |p_y| <= images: what sampling the mask on that grid folds back (the difference from images = 0 estimates
    the grid's aliasing error)."""
    kx = 2 * math.pi * np.fft.fftfreq(n, dx)
    KX, KY = np.meshgrid(kx, kx, indexing="ij")
    prop = KX * KX + KY * KY < k * k
    qx, qy = KX[prop], KY[prop]
    g = 2 * math.pi / dx
    F = np.zeros(qx.shape, complex)
    for px in range(-images, images + 1):
        for py in range(-images, images + 1):
            F += fork_spectrum(kind, l, w0, period, qx + px * g, qy + py * g, m_max)
    P = np.abs(F) ** 2
    tot = float(np.sum(P))
    K = 2 * math.pi / period
    return {m: float(np.sum(P[np.abs(qx + m * K) < 0.5 * K])) / tot for m in orders}


def fork_alias_bound(kind: str, l: int, w0: float, period: float, dx: float, m_max: int) -> float:
    """The share of the band-limited mask's power behind the Gaussian that lies beyond the grid's band (|k_x| or
    |k_y| > pi / dx) and is folded back by sampling: sum_m |c_m|^2 int_{q > pi/dx - |m| K} |A_{ml}|^2 q dq /
    sum_m |c_m|^2 int |A_{ml}|^2 q dq (each order's tail beyond the nearest edge of the band; an upper bound)."""
    K = 2 * math.pi / period
    num = den = 0.0
    for m in range(-m_max, m_max + 1):
        c = fork_order_coefficient(kind, m)
        if c == 0:
            continue
        fn, qmax = B.gaussian_vortex_spectrum(m * l, w0)
        vb = B.VortexBeam(m * l, 2.0 / w0, fn, qmax)
        tot, _ = vb.spectrum_power()
        edge = max(math.pi / dx - abs(m) * K, 0.0)
        num += c * c * vb.spectrum_power(edge)[0]
        den += c * c * tot
    return num / den


def order_leakage(l: int, m: int, w0: float, period: float) -> float:
    """The share of order m's power that lies beyond |k - k_m| = K / 2 in its own spectrum (a Gaussian of waist w0
    behind a plate of charge m l, ``beams.gaussian_vortex_spectrum``): an upper bound on what it puts outside its
    cell; 0 for m l = 0 up to the Gaussian's own tail."""
    K = 2 * math.pi / period
    fn, qmax = B.gaussian_vortex_spectrum(m * l, w0)
    vb = B.VortexBeam(m * l, 2.0 / w0, fn, qmax)  # k only sets the scale of the unbounded band's mapping here
    tot, _ = vb.spectrum_power()
    out, _ = vb.spectrum_power(0.5 * K)
    return out / tot


def propagate(U0, dx: float, k: float, z, pad: int = 2):
    """The field behind a mask sampled on a grid (U0 = incident x transmission on z = 0), propagated exactly by the
    angular spectrum (``lfphys.core.optics.angular_spectrum.propagate_field``, fp64)."""
    return AS.propagate_field(np.asarray(U0, complex), dx, k, z, pad=pad, check=True)


# --- the spinning rough surface (thin phase screen) ---------------------------------------------------------------
class SpinningSurface:
    """A rough surface as a thin phase screen: phase(r) = sum_j h_j exp(-|r - c_j|^2 / s_j^2) of ``n`` Gaussian bumps
    with seeded random centres (uniform in a disc of radius ``radius``), heights (uniform in +-``height`` rad) and
    widths (``size`` times 0.5..1.5); turned by angle a, its bumps' centres are turned by a (exact, no resampling).
    The reflectance is rho = exp(i phase)."""

    def __init__(self, seed: int, n: int = 120, radius: float = 1.0, height: float = 1.5, size: float = 0.2):
        rng = np.random.default_rng(seed)
        r = radius * np.sqrt(rng.uniform(0, 1, n))
        a = rng.uniform(0, 2 * math.pi, n)
        self.cx, self.cy = r * np.cos(a), r * np.sin(a)
        self.h = rng.uniform(-height, height, n)
        self.s = size * rng.uniform(0.5, 1.5, n)

    def phase(self, x, y, angle: float = 0.0):
        c, s = math.cos(angle), math.sin(angle)
        cx, cy = c * self.cx - s * self.cy, s * self.cx + c * self.cy
        x, y = np.asarray(x, float), np.asarray(y, float)
        out = np.zeros(np.broadcast(x, y).shape)
        for j in range(len(self.h)):
            out += self.h[j] * np.exp(-((x - cx[j]) ** 2 + (y - cy[j]) ** 2) / self.s[j] ** 2)
        return out

    def reflectance(self, x, y, angle: float = 0.0):
        return np.exp(1j * self.phase(x, y, angle))


def polar_grid(r_max: float, nr: int = 64, nphi: int = 256):
    """Nodes and weights of a polar quadrature: Gauss-Legendre in r on [0, r_max] (4 panels), uniform in phi
    (spectrally accurate for periodic integrands). Returns (x, y, weights) flattened."""
    gx, gw = np.polynomial.legendre.leggauss(max(1, nr // 4))
    e = np.linspace(0.0, r_max, 5)
    r = np.concatenate([0.5 * (b - a) * gx + 0.5 * (b + a) for a, b in zip(e[:-1], e[1:])])
    wr = np.concatenate([0.5 * (b - a) * gw for a, b in zip(e[:-1], e[1:])])
    ph = 2 * math.pi * np.arange(nphi) / nphi
    R, P = np.meshgrid(r, ph, indexing="ij")
    W = (wr * r)[:, None] * np.full(nphi, 2 * math.pi / nphi)[None, :]
    return (R * np.cos(P)).ravel(), (R * np.sin(P)).ravel(), W.ravel()


def on_axis_amplitude(U, x, y, weights, surface: SpinningSurface, angle: float) -> complex:
    """int U rho dA on a quadrature (``polar_grid``): the amplitude of the light the surface, turned by ``angle``,
    scatters onto the axis (zero transverse spatial frequency); U are the incident field's values at the nodes."""
    return complex(np.sum(weights * U * surface.reflectance(x, y, angle)))
