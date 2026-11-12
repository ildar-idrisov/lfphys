# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The Schroedinger equation in 2-D and 3-D (any dimension) on a uniform grid, with a vector potential and spin
(Pauli) (plan P6):

    i hbar dpsi/dt = [ (p - q A)^2 / 2m + V(r) - i W(r) + b(r) . sigma ] psi,     p = -i hbar grad.

psi is a scalar field, or a two-component spinor (the Pauli equation) when the spin coupling b is given (an energy:
b = -mu B for a magnetic moment mu in a field B; for a charged spin-1/2 particle b = -(g q hbar / 4m) B with g = 2,
``pauli_coupling``). W >= 0 is an absorbing potential: a model of detectors and of the window's open edges.

* **Time evolution: Strang split operator** (Feit, Fleck & Steiger 1982), psi(t + dt) = P K P psi with
  P = exp(-i (V - iW + b.sigma) dt / 2 hbar) per point (a closed-form 2 x 2 exponential for spinors) and the kinetic
  step K:
  - without a vector potential, exp(-i hbar |k|^2 dt / 2m) in Fourier space over all axes (exact for the grid);
  - with a vector potential, an alternating-direction product over the axes
        K = X_0(dt/2) ... X_{d-2}(dt/2) X_{d-1}(dt) X_{d-2}(dt/2) ... X_0(dt/2),
        X_i(tau) = exp(-i tau (p_i - q A_i)^2 / (2 m hbar)) = e^{i q chi_i / hbar} exp(-i tau p_i^2 / (2 m hbar)) e^{-i q chi_i / hbar},
    with chi_i(r) = int A_i dx_i along axis i (along one line A_i is always a pure gauge). Each X_i is exact; their
    product errs by O(dt^3) per step through the commutators [(p_i - qA_i)^2, (p_j - qA_j)^2], which are proportional
    to the magnetic field and its derivatives: zero where B = 0, so an Aharonov-Bohm flux kept where the wave does not
    go costs no splitting error.
  Unitary for W = 0; second order in dt (local error O(dt^3) with the commutator [T, V]). The probability W removes is
  accumulated point by point (``absorbed``): norm + absorbed = 1 holds for the scheme to round-off.
* **A second, independent route** (for tests and references): the Chebyshev expansion of exp(-iHt/hbar) (Tal-Ezer &
  Kosloff 1984) for the same spatial operator, exact to a set tolerance for any t in one go; with a vector potential
  H psi is formed as sum_i (p_i - q A_i)^2 psi / 2m by spectral derivatives, not by the split operator's gauge phases.
* **Stationary states:** LOBPCG (Knyazev 2001) with H psi spectral and a Fourier preconditioner (T + s)^-1: the
  lowest states of 2-D and 3-D problems without assembling a matrix.
* **Observables:** norm, <r>, <p>, <H>, the probability current j = (hbar/m) Im(psi^dag grad psi) - (q/m) A |psi|^2
  (spinors: summed over the components; the divergence-free spin term (hbar/2m) curl(psi^dag sigma psi) of the Pauli
  current on request), values and gradients of psi at arbitrary points (``sample``: Lagrange interpolation of the
  grid's samples), absorbing layers and their reflection.

* **A changed grid** (plan P16.1): ``resample`` carries a wave to a grid of another step or window exactly as the
  band-limited function the old grid holds (its trigonometric interpolant with numpy's modes, the split operator's
  function): Fourier zero padding or truncation on the same window, the samples themselves at the same step, the
  interpolant evaluated otherwise; ``regrid_losses`` measures what such a change cannot carry (the spectrum beyond a
  coarser band, the probability outside a smaller window, the wave at the faces a larger window pads); ``translate``
  moves a wave exactly (a phase ramp on its spectrum) and ``wrap_fraction`` says how much of it would cross a face;
  ``flux_tube_segment`` is the gauge factor of such a move past an Aharonov-Bohm tube in closed form (the line
  integral of the tube's A from r - s to r).

Grid convention (as ``lfphys.core.optics.angular_spectrum``): sample i of an axis with n points and spacing d sits at
center + (i - n//2) d. Requirements, which runs check: k_max = pi/d well above the wave's wavenumbers; the wave
negligible at the window's edges (the grid is periodic) or absorbed there; with a vector potential whose line integral
across the window does not vanish, psi must vanish at those edges (the gauge phase wraps there).

The heavy part (FFTs, phase factors) runs on the CPU or on GPU 0 (``lfphys.core.backend``, kernel
"quantum.split_operator"); eigenstates and the Chebyshev reference run on the CPU.
"""

from __future__ import annotations

import functools
import math
from typing import Callable

import numpy as np
from scipy import special
from scipy.sparse import linalg as sla

from lfphys.i18n import T

from .. import backend

ABOUT = {
    "layer": "core", "kind": "law",
    "title": T("The Schrödinger (and Pauli) equation in 2-D and 3-D"),
    "statement": T("Evolution of the wave function on a grid by the split-operator method (spectrally exact kinetic "
                   "term; the vector potential as gauge phases along the axes; spin ½ as an exact 2×2 exponential at "
                   "every point), absorbing detectors with the absorbed probability accounted for; an independent "
                   "reference: the Chebyshev expansion; stationary states by LOBPCG; the probability current and the "
                   "values of ψ at any points."),
    "validity": T("a non-relativistic particle (spin ½ after Pauli); the grid finer than the wavelength, the window "
                  "wider than the wave or with absorbers at its edges (the norm, the energy and the time step are "
                  "checked in every run)"),
    "basis": ["Schrödinger 1926; Pauli 1927",
              T("Feit, Fleck, Steiger, J. Comput. Phys. 47, 412 (1982) — split-operator method"),
              T("Tal-Ezer & Kosloff, J. Chem. Phys. 81, 3967 (1984) — Chebyshev expansion"),
              "Knyazev, SIAM J. Sci. Comput. 23, 517 (2001) — LOBPCG",
              "Aharonov & Bohm, Phys. Rev. 115, 485 (1959)"],
    "conflicts": [],
}

KERNEL = "quantum.split_operator"
SMALL_GATHER = 200_000  # sample(): below this many stencil values the contractions run on the host
SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)


def _bench(size: int, xp, cplx):
    """Four steps of a 2-D split operator held on the device, then the density back to the host (as a run draws)."""
    n = max(8, int(round(math.sqrt(size))))
    psi = xp.ones((n, n), dtype=cplx)
    P = xp.exp(-0.01j * xp.ones((n, n), dtype=xp.float64)).astype(cplx)
    K = xp.exp(-0.01j * xp.ones((n, n), dtype=xp.float64)).astype(cplx)
    for _ in range(4):
        psi = P * xp.fft.ifft2(K * xp.fft.fft2(P * psi))
    backend.to_numpy(psi.real * psi.real + psi.imag * psi.imag)


backend.register(backend.KernelSpec(
    KERNEL, T("The Schrödinger equation in 2-D/3-D (split operator)"),
    T("a time step of the wave function on a grid: FFT, phase factors, absorption (v11 and the later quantum worlds)"),
    gpu=True,
    precisions={"fp64": {"allowed": True},
                "fp32": {"allowed": False,
                         "why": T("thousands of steps: the fp32 round-off accumulates in the norm and the phase (not "
                                  "verified, so not offered)")}},
    crossover=128 * 128,
    crossover_note=T("measured 2026-10-28 on an RTX 2080 Ti against the container's CPU (6 cores, OMP 2), fp64, four "
                     "steps on the device and the density back: the GPU is faster from 128×128 points (×3), ×26–29 at "
                     "1024²–2048²; “Measure again” refines this"),
    bench=_bench, bench_sizes=(32 * 32, 64 * 64, 128 * 128, 256 * 256, 512 * 512, 1024 * 1024, 2048 * 2048)))


# --- the grid ----------------------------------------------------------------------------------------------------------
class Grid:
    """A uniform grid of ``shape`` points with ``spacing`` (scalar or per axis) about ``center``; a particle of mass m
    (units with hbar = ``hbar``)."""

    def __init__(self, shape, spacing, m: float = 1.0, hbar: float = 1.0, center=None):
        self.shape = tuple(int(n) for n in shape)
        self.ndim = len(self.shape)
        if self.ndim < 1:
            raise ValueError(T("grid: at least one axis"))
        self.d = np.broadcast_to(np.atleast_1d(np.asarray(spacing, float)), (self.ndim,)).copy()
        if np.any(self.d <= 0):
            raise ValueError(T("the grid step must be positive"))
        self.center = np.zeros(self.ndim) if center is None else np.asarray(center, float).reshape(self.ndim)
        self.axes = [c + (np.arange(n) - n // 2) * di for c, n, di in zip(self.center, self.shape, self.d)]
        self.k = [2 * math.pi * np.fft.fftfreq(n, di) for n, di in zip(self.shape, self.d)]
        self.dV = float(np.prod(self.d))
        self.size = int(np.prod(self.shape))
        self.m, self.hbar = float(m), float(hbar)

    def mesh(self, sparse: bool = True):
        """The coordinates as an open (broadcastable) or full mesh, axis order of the grid."""
        return np.meshgrid(*self.axes, indexing="ij", sparse=sparse)

    def kmesh(self):
        return np.meshgrid(*self.k, indexing="ij", sparse=True)

    def k2(self) -> np.ndarray:
        return sum(q * q for q in self.kmesh())

    def kinetic_max(self) -> float:
        """The largest kinetic energy the grid represents, hbar^2 sum_i (pi/d_i)^2 / 2m."""
        return self.hbar**2 * float(np.sum((math.pi / self.d) ** 2)) / (2 * self.m)

    # --- states --------------------------------------------------------------------------------------------------
    def gaussian(self, center, k0, sigma) -> np.ndarray:
        """Normalised product of Gaussian packets: position spreads sigma_i of |psi|^2, mean wavenumbers k0_i."""
        c = np.broadcast_to(np.asarray(center, float), (self.ndim,))
        k = np.broadcast_to(np.asarray(k0, float), (self.ndim,))
        s = np.broadcast_to(np.asarray(sigma, float), (self.ndim,))
        X = self.mesh()
        log = sum(-((X[i] - c[i]) ** 2) / (4 * s[i] ** 2) + 1j * k[i] * X[i] for i in range(self.ndim))
        psi = np.exp(log)
        return psi / math.sqrt(self.norm(psi))

    def free_gaussian(self, t: float, center, k0, sigma) -> np.ndarray:
        """The exact free evolution of ``gaussian(center, k0, sigma)`` in unbounded space: per axis
        (2 pi s^2)^(-1/4) (sigma/s_t) exp(-(x - x0 - v t)^2 / (4 s_t^2) + i k0 (x - x0) - i hbar k0^2 t / 2m) e^{i k0 x0},
        s_t^2 = sigma^2 + i hbar t / (2m), v = hbar k0 / m."""
        c = np.broadcast_to(np.asarray(center, float), (self.ndim,))
        k = np.broadcast_to(np.asarray(k0, float), (self.ndim,))
        s = np.broadcast_to(np.asarray(sigma, float), (self.ndim,))
        X = self.mesh()
        out = 1.0
        for i in range(self.ndim):
            st2 = s[i] ** 2 + 1j * self.hbar * t / (2 * self.m)
            v = self.hbar * k[i] / self.m
            out = out * ((2 * math.pi * s[i] ** 2) ** -0.25 * s[i] / np.sqrt(st2)
                         * np.exp(-((X[i] - c[i] - v * t) ** 2) / (4 * st2) + 1j * k[i] * X[i]
                                  - 1j * self.hbar * k[i] ** 2 * t / (2 * self.m)))
        return out

    # --- observables ----------------------------------------------------------------------------------------------
    def _comps(self, psi):
        psi = np.asarray(psi)
        return psi if psi.ndim == self.ndim + 1 else psi[None]

    def density(self, psi) -> np.ndarray:
        """|psi|^2 (summed over spinor components)."""
        p = self._comps(psi)
        return np.sum(p.real**2 + p.imag**2, axis=0)

    def norm(self, psi) -> float:
        return float(np.sum(self.density(psi)) * self.dV)

    def mean_x(self, psi) -> np.ndarray:
        rho = self.density(psi)
        X = self.mesh()
        return np.array([float(np.sum(X[i] * rho)) for i in range(self.ndim)]) / float(np.sum(rho))

    def grad(self, psi) -> np.ndarray:
        """Spectral gradient: (ncomp, ndim, *shape) for a spinor, (ndim, *shape) for a scalar field."""
        p = self._comps(psi)
        out = np.empty((p.shape[0], self.ndim) + self.shape, complex)
        for i in range(self.ndim):
            shape = [1] * (self.ndim + 1)
            shape[i + 1] = -1
            out[:, i] = np.fft.ifft(1j * self.k[i].reshape(shape) * np.fft.fft(p, axis=i + 1), axis=i + 1)
        return out if np.asarray(psi).ndim == self.ndim + 1 else out[0]

    def mean_p(self, psi) -> np.ndarray:
        """<p> (canonical momentum, hbar k), from the Fourier transform."""
        p = self._comps(psi)
        F = np.fft.fftn(p, axes=tuple(range(1, self.ndim + 1)))
        w = np.sum(np.abs(F) ** 2, axis=0)
        K = self.kmesh()
        return self.hbar * np.array([float(np.sum(K[i] * w)) for i in range(self.ndim)]) / float(np.sum(w))

    def current(self, psi, H: "Hamiltonian | None" = None, spin_term: bool = False) -> np.ndarray:
        """The probability current (ndim, *shape): (hbar/m) Im(psi^dag grad psi) - (q/m) A |psi|^2; with
        ``spin_term`` (spinors, 3-D) plus the Pauli magnetisation current (hbar/2m) curl(psi^dag sigma psi)."""
        p = self._comps(psi)
        g = self.grad(p)  # (nc, ndim, *shape)
        j = self.hbar / self.m * np.imag(np.sum(np.conj(p)[:, None] * g, axis=0))
        if H is not None and H.A is not None:
            rho = self.density(p)
            for i, Ai in enumerate(H.A_arrays()):
                j[i] -= H.q / self.m * Ai * rho
        if spin_term:
            if p.shape[0] != 2 or self.ndim != 3:
                raise ValueError("the spin term of the current needs a spinor in 3-D")
            s = spin_density(p)
            for i in range(3):
                a, b = (i + 1) % 3, (i + 2) % 3
                j[i] += self.hbar / (2 * self.m) * (self._d(s[b], a) - self._d(s[a], b))
        return j

    def _d(self, f, axis):
        shape = [1] * self.ndim
        shape[axis] = -1
        return np.real(np.fft.ifft(1j * self.k[axis].reshape(shape) * np.fft.fft(f, axis=axis), axis=axis))

    def flux(self, psi, axis: int, index: int, H: "Hamiltonian | None" = None, order: int = 8) -> np.ndarray:
        """The current j_axis on the grid plane ``index`` of ``axis`` (an array over the other axes): the derivative
        along ``axis`` by the centred finite difference of ``order`` (the derivative of the Lagrange polynomial
        through ``order`` + 1 samples), which needs only the neighbouring planes (no FFT)."""
        return plane_flux(self, np.asarray(psi), axis, index, H, order, np)

    def energy(self, psi, H: "Hamiltonian") -> float:
        """<H> (the Hermitian part: W is left out)."""
        p = self._comps(psi)
        Hp = H.apply(p)
        return float(np.real(np.vdot(p, Hp)) / np.real(np.vdot(p, p)))


def plane_values(grid: Grid, psi, axis: int, index: int, order: int = 8, xp=np):
    """psi and its derivative along ``axis`` on the grid plane ``index`` (arrays over the other axes, with the
    component axis first: shape (components, ...)), the derivative by the centred finite difference of ``order`` (the
    derivative of the Lagrange polynomial through ``order`` + 1 samples; no FFT). For a state on any device."""
    p = psi if psi.ndim == grid.ndim + 1 else psi[None]
    h = order // 2
    n = grid.shape[axis]
    if index - h < 0 or index + h >= n:
        raise ValueError(T("the flux plane is too close to the edge of the grid"))
    c = fd_weights(order)

    def sl(i):
        return tuple([slice(None)] + [i if a == axis else slice(None) for a in range(grid.ndim)])
    dpsi = sum(float(c[j]) * p[sl(index - h + j)] for j in range(order + 1) if c[j] != 0) / grid.d[axis]
    return p[sl(index)], dpsi


def plane_flux(grid: Grid, psi, axis: int, index: int, H=None, order: int = 8, xp=np):
    """``Grid.flux`` for a state on any device (``xp``: NumPy or CuPy); returns the array module's array."""
    pc, dpsi = plane_values(grid, psi, axis, index, order, xp)
    j = grid.hbar / grid.m * xp.imag(xp.sum(xp.conj(pc) * dpsi, axis=0))
    if H is not None and H.A is not None:
        sl = tuple(index if a == axis else slice(None) for a in range(grid.ndim))
        A = xp.asarray(np.ascontiguousarray(H.A_arrays()[axis][sl]))
        j = j - H.q / grid.m * A * xp.sum(pc.real**2 + pc.imag**2, axis=0)
    return j


def spin_density(p) -> np.ndarray:
    """psi^dag sigma psi (3, *shape) of a spinor (2, *shape)."""
    a, b = p[0], p[1]
    ab = np.conj(a) * b
    return np.stack([2 * ab.real, 2 * ab.imag, np.abs(a) ** 2 - np.abs(b) ** 2])


@functools.lru_cache(maxsize=16)
def fd_weights(order: int) -> np.ndarray:
    """Centred first-derivative weights on order + 1 equidistant nodes -order/2 .. order/2 (unit spacing, even
    order): the derivative of the Lagrange polynomial through them at the middle node."""
    if order % 2:
        raise ValueError("the order of the finite-difference derivative must be even")
    w = lagrange_weights(np.array([float(order // 2)]), order + 1, deriv=True)[1][0]
    w.setflags(write=False)
    return w


@functools.lru_cache(maxsize=16)
def _lagrange_denominators(n: int) -> np.ndarray:
    return np.array([math.prod(jj - mm for mm in range(n) if mm != jj) for jj in range(n)], float)


def lagrange_weights(t, n: int, deriv: bool = False):
    """Weights of the Lagrange polynomial through nodes 0..n-1 at positions t (array, in node units): w (len(t), n)
    and, with ``deriv``, the weights of its derivative. Barycentric form w_j = prod_m (t - m) / ((t - j) den_j),
    w'_j = w_j (sum_{m != j} 1 / (t - m)); points within 1e-4 of a node take the product form (no division), so
    that the barycentric terms lose at most eps / 1e-4 (the product form keeps a field even about a node exactly even)."""
    t = np.asarray(t, float)
    den = _lagrange_denominators(n)
    j = np.arange(n)
    diff = t[:, None] - j[None, :]
    near = np.any(np.abs(diff) < 1e-4, axis=1)
    safe = np.where(np.abs(diff) < 1e-4, 1.0, diff)
    full = np.prod(safe, axis=1, keepdims=True)
    w = full / (safe * den)
    dw = w * (np.sum(1.0 / safe, axis=1, keepdims=True) - 1.0 / safe) if deriv else None
    if np.any(near):  # the product form, built factor by factor (value and derivative together)
        tn = t[near]
        p = np.ones((tn.shape[0], n))
        dp = np.zeros((tn.shape[0], n))
        for m in range(n):
            f = (tn - m)[:, None]
            other = j != m
            dp = np.where(other, dp * f + p, dp)
            p = np.where(other, p * f, p)
        w[near] = p / den
        if deriv:
            dw[near] = dp / den
    return (w, dw) if deriv else w


def demodulated(w, dw, t, kappa, d: float):
    """Lagrange weights of a demodulated field (review B6-Q1). With a carrier wavenumber kappa per point (one axis),
    psi is interpolated as exp(i kappa x) times the Lagrange interpolant of phi_j = psi_j exp(-i kappa x_j): an exact
    identity on the samples (the interpolant still passes through every sample), whose error is that of phi, with
    local wavenumbers k - kappa instead of k. The weights become w_j e^{i kappa (x - x_j)}, those of the derivative
    (w'_j + i kappa w_j) e^{i kappa (x - x_j)}; ``t`` (N,): the point in node units from the stencil's first node,
    ``dw`` per unit length, ``d`` the grid step."""
    kappa = np.asarray(kappa, float)
    ph = np.exp(1j * (kappa * d)[:, None] * (t[:, None] - np.arange(w.shape[1])[None, :]))
    return w * ph, (dw + 1j * kappa[:, None] * w) * ph


def sample(grid: Grid, psi, X, order: int = 8, xp=None, host_ok: bool = False, carrier=None):
    """Values and gradients of psi at points X (N, ndim) by tensor-product Lagrange interpolation of degree ``order``
    (even) through the order + 1 samples centred on the nearest sample of each axis (the gradient: of the same
    polynomial). The stencils are mirror images about every sample, so the interpolant of a field even about a sample
    is even there: a symmetric wave keeps v_x = 0 exactly on its axis (an off-centre stencil made it jump across the
    axis and trapped trajectories there). Remainder per axis: max|prod_j (t - j)| (k dx)^(order+1) / (order+1)! of the
    field, 193.8 (k dx)^9 / 9! for order 8; for the derivative 576 (k dx)^8 / 9! of its size — measured exactly for a
    plane wave (max over the cell): 1.2e-3 at k dx = 1, 2.2e-2 at 1.5, 0.13 at 2 (and higher orders do not converge
    much faster at k dx >= 2: 2.7e-2 for order 16). ``carrier`` (N, ndim): a wavevector per point; psi is then
    interpolated demodulated, exp(i kappa.x) times the interpolant of psi exp(-i kappa.x) (exact on the samples), so the
    error is set by k - kappa: with kappa the local wavevector of a propagating wave the error falls from that of
    k dx to that of the local spread (review B6-Q1). Returns (val (nc, N), grad (nc, ndim, N)); spinor components
    first; arrays of the module ``xp`` (NumPy or CuPy, as psi)."""
    if order % 2:
        raise ValueError("the interpolation degree must be even (a stencil of an odd number of points about the nearest "
                         "node)")
    xp = xp or np
    p = psi if psi.ndim == grid.ndim + 1 else psi[None]
    X = np.asarray(backend.to_numpy(X), float)
    N, d, n = X.shape[0], grid.ndim, order + 1
    nc = p.shape[0]
    K = None if carrier is None else np.asarray(carrier, float).reshape(N, d)
    W, DW, flat = [], [], np.zeros((N,) + (1,) * d, np.int64)
    stride = 1
    for i in reversed(range(d)):  # row-major strides of the grid
        u = (X[:, i] - grid.axes[i][0]) / grid.d[i]
        i0 = np.clip(np.floor(u + 0.5).astype(np.int64) - order // 2, 0, grid.shape[i] - n)
        wi, dwi = lagrange_weights(u - i0, n, deriv=True)
        dwi = dwi / grid.d[i]
        if K is not None:
            wi, dwi = demodulated(wi, dwi, u - i0, K[:, i], grid.d[i])
        W.insert(0, wi)
        DW.insert(0, dwi)
        shape = [N] + [1] * d
        shape[i + 1] = n
        flat = flat + ((i0[:, None] + np.arange(n)[None, :]) * stride).reshape(shape)
        stride *= grid.shape[i]
    # one gather of every stencil on the device, then the contractions where they are cheapest (a few points: the
    # host, where dozens of tiny device kernels cost more than the arithmetic)
    T = p.reshape(nc, -1)[:, xp.asarray(flat.reshape(-1))].reshape((nc, N) + (n,) * d)
    host = xp is np or N * nc * n**d <= SMALL_GATHER
    if host:
        T = backend.to_numpy(T)
        mod, Wm, DWm = np, W, DW
    else:
        mod, Wm, DWm = xp, [xp.asarray(a) for a in W], [xp.asarray(a) for a in DW]
    letters = "defghij"[:d]  # not "c" or "n" (the component and point indices): "abc" broke 3-D (B6 finding)
    spec = "cn" + letters + "," + ",".join("n" + L for L in letters) + "->cn"
    vals = mod.einsum(spec, T, *Wm)
    grads = mod.stack([mod.einsum(spec, T, *[DWm[a] if a == i else Wm[a] for a in range(d)]) for i in range(d)],
                      axis=1)
    if host and xp is not np and not host_ok:  # ``host_ok``: the caller takes NumPy results as they are
        return xp.asarray(vals), xp.asarray(grads)
    return vals, grads


# --- vector potentials ---------------------------------------------------------------------------------------------
_GL_X, _GL_W = np.polynomial.legendre.leggauss(8)


class VectorPotential:
    """A vector potential A(r) given by ``fn(i, *coords) -> A_i`` (coords broadcastable arrays, one per axis of the
    grid); smooth on the scale of the grid. On a grid it gives the arrays A_i and the line integrals
    chi_i(r) = int_{x_i,0}^{x_i} A_i dx_i' along each axis from the first sample (8-point Gauss-Legendre in every cell,
    accumulated), which the split operator's gauge phases use."""

    def __init__(self, fn: Callable, label=""):  # label: a translatable text (lfphys.i18n.T)
        self.fn = fn
        self.label = label

    def arrays(self, grid: Grid):
        X = grid.mesh(sparse=False)
        return [np.broadcast_to(np.asarray(self.fn(i, *X), float), grid.shape).copy() for i in range(grid.ndim)]

    def line_integrals(self, grid: Grid):
        X = grid.mesh(sparse=False)
        out = []
        for i in range(grid.ndim):
            d = grid.d[i]
            cell = np.zeros(grid.shape)
            for xg, wg in zip(_GL_X, _GL_W):  # the cell [x_j, x_j + d] seen from its left sample x_j
                Y = list(X)
                Y[i] = X[i] + 0.5 * d * (1.0 + xg)
                cell += 0.5 * d * wg * np.asarray(self.fn(i, *Y), float)
            chi = np.cumsum(cell, axis=i)
            chi = np.roll(chi, 1, axis=i)  # chi at sample j = the cells 0 .. j-1
            sl = [slice(None)] * grid.ndim
            sl[i] = 0
            chi[tuple(sl)] = 0.0
            out.append(chi)
        return out

    def gauge(self, grid: Grid, ref, nodes: int = 16) -> np.ndarray:
        """Lambda(r) = int A . dl along the straight segment from ``ref`` to r (Gauss-Legendre with ``nodes`` points):
        where the region around ``ref`` holds no field (A = grad Lambda there), psi = e^{i q Lambda / hbar} phi has the
        kinetic momentum p - qA of phi. A packet prepared away from a flux must carry this factor; without it the same
        Gaussian is a different physical state in each gauge (it carries the extra momentum -qA)."""
        X = grid.mesh(sparse=False)
        ref = np.asarray(ref, float).reshape(grid.ndim)
        D = [X[i] - ref[i] for i in range(grid.ndim)]
        out = np.zeros(grid.shape)
        xg, wg = np.polynomial.legendre.leggauss(nodes)
        for s, w in zip(0.5 * (xg + 1.0), 0.5 * wg):
            P = [ref[i] + s * D[i] for i in range(grid.ndim)]
            out += w * sum(np.asarray(self.fn(i, *P), float) * D[i] for i in range(grid.ndim))
        return out

    def at(self, X) -> np.ndarray:
        """A at points X (N, ndim)."""
        X = np.asarray(X, float)
        return np.stack([np.broadcast_to(np.asarray(self.fn(i, *X.T), float), X.shape[:1]) for i in range(X.shape[1])],
                        axis=1)


def uniform_field(B: float, center=(0.0, 0.0), axes=(0, 1)) -> VectorPotential:
    """A uniform magnetic field B normal to the plane of grid axes (a, b) (along e_a x e_b), symmetric gauge
    A = (B/2) (-(x_b - c_b), x_a - c_a) in that plane."""
    a, b = axes
    ca, cb = center

    def fn(i, *X):
        if i == a:
            return -0.5 * B * (X[b] - cb)
        if i == b:
            return 0.5 * B * (X[a] - ca)
        return np.zeros_like(X[0])
    return VectorPotential(fn, T("uniform field B = {B}", B=float(B)))


def flux_tube(flux: float, center=(0.0, 0.0), radius: float = 1.0, axes=(0, 1)) -> VectorPotential:
    """An Aharonov-Bohm flux tube normal to the plane of grid axes (a, b) (flux ``flux`` along e_a x e_b) with a
    Gaussian profile of the field, B ∝ exp(-r^2/R^2): A = (flux / 2 pi) (1 - exp(-r^2/R^2)) / r^2 (-(x_b - c_b),
    x_a - c_a). Outside a few R the field vanishes and A = (flux / 2 pi) grad(angle): only the line integral around the
    tube (= flux) is physical there."""
    a, b = axes
    ca, cb = center
    R2 = float(radius) ** 2

    def f_over_r2(X):
        r2 = (X[a] - ca) ** 2 + (X[b] - cb) ** 2
        with np.errstate(invalid="ignore", divide="ignore"):
            g = np.where(r2 > 1e-12 * R2, -np.expm1(-r2 / R2) / np.where(r2 > 0, r2, 1.0), 1.0 / R2)
        return g

    def fn(i, *X):
        if i == a:
            return -flux / (2 * math.pi) * f_over_r2(X) * (X[b] - cb)
        if i == b:
            return flux / (2 * math.pi) * f_over_r2(X) * (X[a] - ca)
        return np.zeros(np.broadcast(*X).shape)
    return VectorPotential(fn, T("flux tube Φ = {flux}", flux=float(flux)))


def flux_tube_segment(grid: Grid, flux: float, shift, center=(0.0, 0.0), radius: float = 1.0,
                      axes=(0, 1)) -> np.ndarray:
    """chi(r) = int A . dl along the straight segment from r - ``shift`` to r, for the tube of ``flux_tube`` (same
    arguments), at every point of ``grid``, in closed form. Along a line at distance h from the tube's axis, with tau the
    coordinate along the line from the foot of the perpendicular, d theta = sgn h / (h^2 + tau^2) d tau and
    A . dl = (flux / 2 pi) (1 - exp(-rho^2/R^2)) d theta, rho^2 = h^2 + tau^2; so

        chi = (flux / 2 pi) sgn [ atan(tau_Q/h) - atan(tau_P/h) - 2 pi (T(sqrt2 h/R, tau_Q/h) - T(sqrt2 h/R, tau_P/h)) ]

    with Owen's T function T(h', a) = (1/2 pi) int_0^a exp(-h'^2 (1 + x^2)/2) / (1 + x^2) dx (``scipy.special.owens_t``)
    and sgn the side of the axis the line passes; 0 on a line through the axis (A is perpendicular to it there).

    This is the gauge factor of a wave moved by ``shift`` past the tube (``Scene.transform_particle``): grad chi =
    A(r) - A(r - s) + s x <B> over the segment (an identity: grad (A . s) = (s . grad) A + s x curl A), so it is the
    exact magnetic translation wherever the segment [r - s, r] misses the tube's field — everywhere except next to the
    path [c, c + s] the tube's axis takes relative to the moved wave. Exact also for a wave that goes round the tube on
    both sides; where the moved wave meets that path no translation keeps the wave (the flux it encloses changes)."""
    a, b = (int(v) for v in axes)
    s = np.asarray(shift, float).reshape(grid.ndim)
    u = np.array([s[a], s[b]])
    L = float(np.hypot(u[0], u[1]))
    if L == 0.0:
        return np.zeros(grid.shape)
    e = u / L
    X = grid.mesh()
    qa, qb = X[a] - float(center[0]), X[b] - float(center[1])  # Q = r - c (the segment's end) in the tube's plane
    cr = qa * e[1] - qb * e[0]                                  # Q x e: the signed distance of the axis from the line
    h = np.abs(cr)
    tq = qa * e[0] + qb * e[1]
    tp = tq - L
    R = float(radius)
    with np.errstate(divide="ignore", invalid="ignore"):
        hs = np.where(h > 0, h, 1.0)
        hp = math.sqrt(2.0) * hs / R
        val = (np.arctan(tq / hs) - np.arctan(tp / hs)
               - 2.0 * math.pi * (special.owens_t(hp, tq / hs) - special.owens_t(hp, tp / hs)))
    chi = float(flux) / (2.0 * math.pi) * np.sign(cr) * np.where(h > 0, val, 0.0)
    return np.broadcast_to(chi, grid.shape).copy()


def pauli_coupling(B, q: float, m: float, hbar: float = 1.0, g: float = 2.0):
    """The spin coupling b of a charged spin-1/2 particle in a field B: b.sigma = -(g q hbar / 4m) B.sigma."""
    return -(g * q * hbar / (4 * m)) * np.asarray(B, float)


# --- the Hamiltonian -------------------------------------------------------------------------------------------------
class Hamiltonian:
    """H = (p - qA)^2/2m + V - iW + b.sigma on a grid. V, W: arrays of the grid's shape (or scalars, or None);
    A: a ``VectorPotential`` or None; b: (3, *shape) or None (scalar wave). ``apply`` acts with the Hermitian part
    (W left out unless asked)."""

    def __init__(self, grid: Grid, V=None, W=None, A: VectorPotential | None = None, q: float = 1.0, b=None):
        self.grid, self.q, self.A = grid, float(q), A
        self.V = None if V is None else np.broadcast_to(np.asarray(V, float), grid.shape)
        self.W = None if W is None else np.broadcast_to(np.asarray(W, float), grid.shape)
        if self.W is not None and np.any(self.W < 0):
            raise ValueError(T("the absorbing potential W must be non-negative"))
        self.b = None if b is None else np.broadcast_to(np.asarray(b, float), (3,) + grid.shape)
        self._A = self._chi = None

    @property
    def spinor(self) -> bool:
        return self.b is not None

    def A_arrays(self):
        if self.A is None:
            return None
        if self._A is None:
            self._A = self.A.arrays(self.grid)
        return self._A

    def chi(self):
        if self.A is None:
            return None
        if self._chi is None:
            self._chi = self.A.line_integrals(self.grid)
        return self._chi

    def kinetic(self, p) -> np.ndarray:
        """sum_i (p_i - q A_i)^2 p / 2m by spectral derivatives (p: (nc, *shape))."""
        g = self.grid
        hb, m = g.hbar, g.m
        ax = tuple(range(1, g.ndim + 1))
        if self.A is None:
            K2 = g.k2()
            return np.fft.ifftn(hb * hb * K2 / (2 * m) * np.fft.fftn(p, axes=ax), axes=ax)
        out = np.zeros_like(p, dtype=complex)
        A = self.A_arrays()
        for i in range(g.ndim):
            shape = [1] * (g.ndim + 1)
            shape[i + 1] = -1
            k = g.k[i].reshape(shape)

            def pi_op(f):
                return hb * np.fft.ifft(k * np.fft.fft(f, axis=i + 1), axis=i + 1) - self.q * A[i] * f
            out += pi_op(pi_op(p))
        return out / (2 * m)

    def apply(self, psi, absorbing: bool = False) -> np.ndarray:
        g = self.grid
        p = np.asarray(psi, complex)
        scalar = p.ndim == g.ndim
        if scalar:
            p = p[None]
        out = self.kinetic(p)
        if self.V is not None:
            out += self.V * p
        if self.b is not None:
            bx, by, bz = self.b
            out[0] += bz * p[0] + (bx - 1j * by) * p[1]
            out[1] += (bx + 1j * by) * p[0] - bz * p[1]
        if absorbing and self.W is not None:
            out -= 1j * self.W * p
        return out[0] if scalar else out

    def bounds(self) -> tuple[float, float]:
        """Bounds of the Hermitian part's spectrum on the grid (for the Chebyshev expansion)."""
        g = self.grid
        lo = float(np.min(self.V)) if self.V is not None else 0.0
        hi = float(np.max(self.V)) if self.V is not None else 0.0
        if self.b is not None:
            bm = float(np.max(np.sqrt(np.sum(self.b**2, axis=0))))
            lo, hi = lo - bm, hi + bm
        if self.A is None:
            hi += g.kinetic_max()
        else:
            A = self.A_arrays()
            hi += sum((g.hbar * math.pi / g.d[i] + abs(self.q) * float(np.max(np.abs(A[i])))) ** 2
                      for i in range(g.ndim)) / (2 * g.m)
        pad = 1e-3 * (hi - lo) + 1e-12
        return lo - pad, hi + pad


# --- time evolution: the split operator ---------------------------------------------------------------------------------
class SplitOperator:
    """Strang split-operator steps of ``H`` with time step ``dt``, the state kept on the chosen device between steps.
    ``put``/``get`` move a state to and from the device; ``step(psi, n)`` returns psi after n steps; with
    ``track_absorbed`` the probability W removes is accumulated point by point (``absorbed``: probability per cell).
    ``rebuild`` changes the potentials (a live change of the set-up) between steps."""

    def __init__(self, H: Hamiltonian, dt: float, track_absorbed: bool = False, force_cpu: bool = False, why: str = ""):
        self.H, self.dt = H, float(dt)
        g = H.grid
        nc = 2 if H.spinor else 1
        # the state, the potential factors, the kinetic factor (or the gauge phases), temporaries: ~ 8 arrays
        footprint = 16 * g.size * nc * (6 + (2 * g.ndim if H.A is not None else 0)) + 16 * g.size * 2
        self.choice = backend.choose(KERNEL, g.size, footprint=footprint, force="cpu" if force_cpu else None, why=why)
        self.xp = self.choice.xp
        self.track = bool(track_absorbed)
        self.acc = None
        self._build()

    @property
    def device(self) -> str:
        return self.choice.device

    def _build(self):
        H, xp, g = self.H, self.xp, self.H.grid
        hb, m, dt = g.hbar, g.m, self.dt
        tau = dt / (2 * hb)
        V = np.zeros(g.shape) if H.V is None else np.asarray(H.V, float)
        W = None if H.W is None else np.asarray(H.W, float)
        damp = 1.0 if W is None else np.exp(-W * tau)
        if H.spinor:
            b = np.asarray(H.b, float)
            bm = np.sqrt(np.sum(b * b, axis=0))
            n = np.where(bm > 0, b / np.where(bm > 0, bm, 1.0), 0.0)
            c, s = np.cos(bm * tau), np.sin(bm * tau)
            ph = np.exp(-1j * V * tau) * damp
            self.U = [xp.asarray(ph * (c - 1j * s * n[2])), xp.asarray(ph * (-1j * s * (n[0] - 1j * n[1]))),
                      xp.asarray(ph * (-1j * s * (n[0] + 1j * n[1]))), xp.asarray(ph * (c + 1j * s * n[2]))]
            self.P = None
        else:
            self.P = xp.asarray(np.exp(-1j * V * tau) * damp)
            self.U = None
        self.loss = None if (W is None or not self.track) else xp.asarray(-np.expm1(-W * dt / hb))
        if self.loss is not None and self.acc is None:
            self.acc = xp.zeros(g.shape)
        if H.A is None:
            self.K = xp.asarray(np.exp(-1j * hb * g.k2() * dt / (2 * m)))
            self.G = None
        else:
            self.K = None
            self.G = [xp.asarray(np.exp(-1j * H.q * c / hb)) for c in H.chi()]
            self.Kh, self.Kf = [], []
            for i in range(g.ndim):
                shape = [1] * g.ndim
                shape[i] = -1
                k2 = (g.k[i] ** 2).reshape(shape)
                self.Kh.append(xp.asarray(np.exp(-1j * hb * k2 * dt / (4 * m))))
                self.Kf.append(xp.asarray(np.exp(-1j * hb * k2 * dt / (2 * m))))

    def rebuild(self, V=None, W=None, A=None, b=None, q=None, keep=("V", "W", "A", "b")):
        """New potentials from the next step on (a live change). Arguments left as None keep their current value
        unless their name is missing from ``keep``."""
        H = self.H
        new = Hamiltonian(H.grid, V=V if V is not None else (H.V if "V" in keep else None),
                          W=W if W is not None else (H.W if "W" in keep else None),
                          A=A if A is not None else (H.A if "A" in keep else None),
                          q=H.q if q is None else q,
                          b=b if b is not None else (H.b if "b" in keep else None))
        if new.spinor != H.spinor:
            raise ValueError(T("a scalar wave cannot be turned into a spinor or back while running"))
        self.H = new
        self._build()

    def put(self, psi):
        return self.xp.asarray(np.asarray(psi, complex))

    def get(self, psi) -> np.ndarray:
        return backend.to_numpy(psi)

    def absorbed(self) -> np.ndarray | None:
        """Probability removed by W so far, per cell (sums to the norm lost)."""
        return None if self.acc is None else backend.to_numpy(self.acc) * self.H.grid.dV

    def _rho(self, psi):
        return self.xp.sum(psi.real * psi.real + psi.imag * psi.imag, axis=0) if self.H.spinor else \
            psi.real * psi.real + psi.imag * psi.imag

    def _pot(self, psi):
        if self.loss is not None:
            self.acc += self._rho(psi) * self.loss
        if self.U is None:
            return self.P * psi
        a, b = psi[0], psi[1]
        return self.xp.stack([self.U[0] * a + self.U[1] * b, self.U[2] * a + self.U[3] * b])

    def _kin(self, psi):
        xp, g = self.xp, self.H.grid
        off = 1 if self.H.spinor else 0
        axes = tuple(range(off, off + g.ndim))
        if self.G is None:
            return xp.fft.ifftn(self.K * xp.fft.fftn(psi, axes=axes), axes=axes)
        order = list(range(g.ndim))
        seq = [(i, self.Kh[i]) for i in order[:-1]] + [(order[-1], self.Kf[order[-1]])] + \
              [(i, self.Kh[i]) for i in reversed(order[:-1])]
        for i, Ki in seq:
            Gi = self.G[i]
            psi = xp.conj(Gi) * xp.fft.ifft(Ki * xp.fft.fft(Gi * psi, axis=i + off), axis=i + off)
        return psi

    def step(self, psi, n: int = 1):
        for _ in range(int(n)):
            psi = self._pot(self._kin(self._pot(psi)))
        return psi

    def norm(self, psi) -> float:
        return float(backend.to_numpy(self.xp.sum(self._rho(psi)))) * self.H.grid.dV

    def flux(self, psi, axis: int, index: int, order: int = 8) -> np.ndarray:
        """The current through grid plane ``index`` of ``axis`` (``Grid.flux``), computed on the device."""
        return backend.to_numpy(plane_flux(self.H.grid, psi, axis, index, self.H, order, self.xp))

    def plane(self, psi, axis: int, index: int, order: int = 8):
        """psi and d psi / d(axis) on grid plane ``index`` (``plane_values``), moved to the host."""
        pc, d = plane_values(self.H.grid, psi, axis, index, order, self.xp)
        return backend.to_numpy(pc), backend.to_numpy(d)

    def absorbed_in(self, region) -> float:
        """Probability W has removed so far inside ``region`` (an index or a boolean mask of the grid), summed on the
        device (0 without ``track_absorbed``)."""
        if self.acc is None:
            return 0.0
        if isinstance(region, np.ndarray) and region.dtype == bool:
            region = self.xp.asarray(region)
        return float(backend.to_numpy(self.xp.sum(self.acc[region]))) * self.H.grid.dV

    def density(self, psi) -> np.ndarray:
        """|psi|^2 on the host."""
        return backend.to_numpy(self._rho(psi))


# --- the second route: Chebyshev -------------------------------------------------------------------------------------
def chebyshev(H: Hamiltonian, psi, t: float, tol: float = 1e-13) -> np.ndarray:
    """exp(-i H t / hbar) psi by the Chebyshev expansion (Tal-Ezer & Kosloff 1984): with H = E_mid + R Hn,
    exp(-iHt/hbar) = e^{-i E_mid t/hbar} sum_k (2 - delta_k0) (-i)^k J_k(R t/hbar) T_k(Hn); the series is cut where the
    Bessel coefficients fall below ``tol`` (beyond k ~ R t / hbar they fall faster than geometrically). The Hermitian
    part of H only (no absorbing W)."""
    g = H.grid
    lo, hi = H.bounds()
    R, Em = 0.5 * (hi - lo), 0.5 * (hi + lo)
    a = R * t / g.hbar
    K = int(a + 30 + 10 * a ** (1 / 3))
    J = special.jv(np.arange(K + 1), a)
    while K > a and abs(J[K]) < tol and abs(J[K - 1]) < tol:
        K -= 1
    p = np.asarray(psi, complex)

    def Hn(f):
        return (H.apply(f) - Em * f) / R
    f0, f1 = p, Hn(p)
    out = J[0] * f0 + 2 * (-1j) * J[1] * f1
    for k in range(2, K + 1):
        f0, f1 = f1, 2 * Hn(f1) - f0
        out += 2 * (-1j) ** k * J[k] * f1
    return np.exp(-1j * Em * t / g.hbar) * out


# --- stationary states -------------------------------------------------------------------------------------------------
def eigenstates(H: Hamiltonian, n: int, tol: float = 1e-9, maxiter: int = 600, seed: int = 0, guess=None):
    """The ``n`` lowest eigenstates of the Hermitian part of H: LOBPCG with H psi spectral (no matrix) and the
    preconditioner (T + s)^-1 in Fourier space. Returns (E (n,), states (n, [2,] *shape) normalised to
    int |psi|^2 dV = 1, residuals ||H psi - E psi|| / max(1, |E|))."""
    g = H.grid
    nc = 2 if H.spinor else 1
    N = nc * g.size
    shape = ((nc,) if H.spinor else ()) + g.shape
    ax = tuple(range(1 if H.spinor else 0, (1 if H.spinor else 0) + g.ndim))
    T = g.hbar**2 * g.k2() / (2 * g.m)
    vmin = float(np.min(H.V)) if H.V is not None else 0.0
    pre = 1.0 / (T + max(abs(vmin), 0.01 * g.kinetic_max()) + 1e-12)

    def mv(x):
        X = np.asarray(x).reshape(shape + (-1,))
        out = np.empty_like(X, dtype=complex)
        for c in range(X.shape[-1]):
            out[..., c] = H.apply(X[..., c])
        return out.reshape(N, -1)

    def pc(x):
        X = np.asarray(x).reshape(shape + (-1,))
        out = np.empty_like(X, dtype=complex)
        for c in range(X.shape[-1]):
            out[..., c] = np.fft.ifftn(pre * np.fft.fftn(X[..., c], axes=ax), axes=ax)
        return out.reshape(N, -1)

    A = sla.LinearOperator((N, N), matvec=lambda x: mv(x)[:, 0], matmat=mv, dtype=complex)
    M = sla.LinearOperator((N, N), matvec=lambda x: pc(x)[:, 0], matmat=pc, dtype=complex)
    rng = np.random.default_rng(seed)
    k = int(n) + max(2, int(n) // 2)  # a few extra vectors speed up convergence of the wanted ones
    X0 = rng.standard_normal((N, k)) + 1j * rng.standard_normal((N, k))
    if guess is not None:
        G = np.asarray(guess).reshape(len(guess), -1).T
        X0[:, :G.shape[1]] = G
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        E, Xv = sla.lobpcg(A, X0, M=M, tol=tol, maxiter=maxiter, largest=False)
    order = np.argsort(E.real)[:n]
    E, Xv = E.real[order], Xv[:, order]
    res = np.linalg.norm(mv(Xv) - Xv * E[None, :], axis=0) / np.maximum(1.0, np.abs(E)) / np.linalg.norm(Xv, axis=0)
    states = (Xv.T / np.sqrt(g.dV * np.sum(np.abs(Xv) ** 2, axis=0))[:, None]).reshape((n,) + shape)
    return E, states, res


# --- absorbing layers -----------------------------------------------------------------------------------------------------
def absorbing_layer(grid: Grid, axis: int, side: str, width: float, W0: float, power: int = 2) -> np.ndarray:
    """W = W0 (s/width)^power in a layer of ``width`` at the ``side`` ("low" | "high") end of ``axis``, s the depth
    into the layer (0 at its inner face); zero elsewhere. Arrays of the grid's shape."""
    x = grid.axes[axis]
    if side == "high":
        s = x - (x[-1] - width)
    elif side == "low":
        s = (x[0] + width) - x
    else:
        raise ValueError("absorber side: 'low' or 'high'")
    w1 = np.where(s > 0, W0 * np.clip(s / width, 0, 1) ** power, 0.0)
    shape = [1] * grid.ndim
    shape[axis] = -1
    return np.broadcast_to(w1.reshape(shape), grid.shape).copy()


def layer_reflection(kn, width: float, W0: float, m: float, hbar: float = 1.0, power: int = 2, slices: int = 2000):
    """Reflection and leak of the absorbing layer W0 (s/width)^power for waves whose wavenumber normal to the layer is
    ``kn`` (array): stationary 1-D transfer matrices (``lfphys.core.quantum.transfer.transmission_profile``) of the
    complex potential -iW, free space on both sides (what passes the layer wraps round the periodic window). Returns
    (R, T) per kn; 1 - R - T is absorbed. A wave at angle theta to the normal has kn = k cos(theta)."""
    from .transfer import transmission_profile
    kn = np.atleast_1d(np.asarray(kn, float))
    E = hbar**2 * kn**2 / (2 * m)

    def ramp(xx):  # the layer, then nothing: what passes it wraps round the periodic window (a leak)
        xx = np.asarray(xx, float)
        return -1j * W0 * np.clip(xx / width, 0.0, 1.0) ** power * ((xx > 0) & (xx <= width))
    T, R = transmission_profile(E, ramp, 0.0, width, slices, m, hbar, return_r=True)
    return R, T


# --- a changed grid: exact resampling of band-limited waves (plan P16.1) -----------------------------------------------
def window(grid: Grid, axis: int) -> tuple[float, float]:
    """The periodic cell of ``axis``: [x_0 - d/2, x_0 - d/2 + n d) (the samples sit at its cells' centres). Sample n//2
    sits at the centre, so for even n the cell is half a step longer on its low side, and a change of the grid on the
    same window length (``resample``) moves the cell by (d - d2)/2 — exactly so for the periodic wave the grid holds,
    while the drawn window and an open edge's layer (``absorbing_layer``, measured from the outermost samples) shift by
    up to half a step (review LB1-p02-ux Q9)."""
    x0, d = float(grid.axes[axis][0]), float(grid.d[axis])
    return x0 - 0.5 * d, x0 - 0.5 * d + grid.shape[axis] * d


def _modes(n: int) -> np.ndarray:
    """The integer mode numbers of an n-point FFT in numpy's order (k_m = 2 pi m / (n d); for even n the Nyquist mode is
    m = -n/2, as ``Grid.k`` and the split operator take it)."""
    return np.rint(np.fft.fftfreq(n) * n).astype(int)


def resample_axis(f, ax: int, n: int, d: float, c: float, n2: int, d2: float) -> np.ndarray:
    """The samples of the band-limited function held by ``f`` along array axis ``ax`` (n samples, spacing d, the
    sample n//2 at c: the grid's convention) at the n2 points c + (j - n2//2) d2 of a new grid with the same centre.

    The function the grid holds is its trigonometric interpolant f(x) = (1/n) sum_m F_m exp(i k_m (x - x_0)), k_m =
    2 pi m / (n d) with numpy's modes (the split operator evolves exactly this function). Three exact routes:

    * the same spacing (a larger or smaller window): the samples themselves, copied (the new points are old points),
      zeros where the new window reaches beyond the old one;
    * the same window (a finer or coarser grid): Fourier zero padding or truncation, F_m n2/n on the modes both grids
      hold (the modes beyond a coarser grid's band are dropped: the caller measures them first);
    * otherwise (window and spacing both changed): f evaluated at the new points inside the old window by the dense
      matrix exp(i k_m (x'_j - x_0)) / n, zero outside it; on a coarser grid only the modes with -pi/d2 <= k_m < pi/d2
      (the new band) are kept. Exact evaluation of the interpolant; that the zero padding meets a negligible wave at
      the old faces is the caller's test (``regrid_losses``).

    Returns a new complex array (the other axes untouched)."""
    f = np.asarray(f, complex)
    same_d = abs(d2 - d) <= 1e-12 * d
    if same_d and n2 == n:
        return f.copy()
    shape2 = list(f.shape)
    shape2[ax] = n2
    if same_d:
        s = n2 // 2 - n // 2  # new index of old sample i: i + s (both grids hold the point c at index n//2)
        out = np.zeros(shape2, complex)
        j0, j1 = max(0, s), min(n2, n + s)
        dst = [slice(None)] * f.ndim
        src = [slice(None)] * f.ndim
        dst[ax], src[ax] = slice(j0, j1), slice(j0 - s, j1 - s)
        out[tuple(dst)] = f[tuple(src)]
        return out
    m = _modes(n)
    k = 2.0 * math.pi * m / (n * d)
    x0 = c - (n // 2) * d
    x0n = c - (n2 // 2) * d2
    F = np.fft.fft(f, axis=ax)
    bshape = [1] * f.ndim
    bshape[ax] = -1
    if abs(n2 * d2 - n * d) <= 1e-12 * n * d:  # the same window: zero padding or truncation of the spectrum
        m2 = _modes(n2)
        pos2 = {int(v): j for j, v in enumerate(m2)}
        idx_old = np.array([i for i, v in enumerate(m) if int(v) in pos2], int)
        idx_new = np.array([pos2[int(m[i])] for i in idx_old], int)
        ph = np.exp(1j * k[idx_old] * (x0n - x0)) * (n2 / n)
        F2 = np.zeros(shape2, complex)
        dst = [slice(None)] * f.ndim
        dst[ax] = idx_new
        F2[tuple(dst)] = np.take(F, idx_old, axis=ax) * ph.reshape(bshape)
        return np.fft.ifft(F2, axis=ax)
    keep = np.ones(n, bool)
    if d2 > d * (1 + 1e-12):  # coarser: the new band -pi/d2 <= k < pi/d2 (in modes: -r <= m < r, r = n d / (2 d2))
        r = n * d / (2.0 * d2)
        keep = (m >= -r - 1e-9) & (m < r - 1e-9)
    xn = c + (np.arange(n2) - n2 // 2) * d2
    lo, hi = x0 - 0.5 * d, x0 - 0.5 * d + n * d
    inside = (xn >= lo - 1e-12 * d) & (xn < hi - 1e-12 * d)
    M = np.exp(1j * np.outer(xn - x0, k[keep])) / n
    M[~inside] = 0.0
    Fk = np.moveaxis(np.compress(keep, F, axis=ax), ax, -1)
    return np.moveaxis(Fk @ M.T, -1, ax)


def resample(psi, old: Grid, new: Grid) -> np.ndarray:
    """``resample_axis`` along every axis of a scalar wave (shape) or a spinor (2, shape): the band-limited wave on the
    grid ``new`` (same dimension and centre as ``old``)."""
    p = np.asarray(psi, complex)
    off = 1 if p.ndim == old.ndim + 1 else 0
    if new.ndim != old.ndim or not np.allclose(new.center, old.center, rtol=0, atol=1e-12 * float(max(old.d))):
        raise ValueError(T("new grid: the same dimension and the same window centre"))
    for a in range(old.ndim):
        p = resample_axis(p, a + off, old.shape[a], float(old.d[a]), float(old.center[a]), new.shape[a],
                          float(new.d[a]))
    return p


def regrid_losses(psi, old: Grid, new: Grid, face_cells: int = 4) -> dict:
    """What a change of the grid ``old`` -> ``new`` (``resample``) cannot carry, as fractions of the wave's norm on
    ``old``: ``spectrum`` — the spectrum beyond a coarser axis's band (-pi/d2 <= k < pi/d2), dropped; ``outside`` — the
    probability outside a smaller window, dropped; ``face`` — the probability in the ``face_cells`` outermost cells of
    the old window along every axis the new window extends beyond it (where the zero padding meets the wave: the grid is
    periodic, so a wave there continues on the other side, which a larger window does not). An axis whose window keeps
    its length (n2 d2 = n d) has neither: the periodic function is carried whole."""
    p = np.asarray(psi, complex)
    comps = p if p.ndim == old.ndim + 1 else p[None]
    rho = np.sum(comps.real ** 2 + comps.imag ** 2, axis=0)
    tot = float(rho.sum())
    out = {"spectrum": 0.0, "outside": 0.0, "face": 0.0}
    if not tot > 0:
        return out
    cut = np.zeros(old.shape, bool)
    face = np.zeros(old.shape, bool)
    for a in range(old.ndim):
        if abs(new.shape[a] * float(new.d[a]) - old.shape[a] * float(old.d[a])) <= 1e-12 * old.shape[a] * float(old.d[a]):
            continue  # the same periodic window: a finer or coarser grid has no faces to meet (its cell may start half a
            # step elsewhere: the sample n//2 sits at the centre on both grids)
        lo, hi = window(old, a)
        lo2, hi2 = window(new, a)
        tiny = 1e-9 * float(old.d[a])
        shp = [1] * old.ndim
        shp[a] = -1
        x = old.axes[a].reshape(shp)
        if lo2 > lo + tiny or hi2 < hi - tiny:
            cut |= np.broadcast_to((x < lo2 - tiny) | (x >= hi2 - tiny), old.shape)
        if lo2 < lo - tiny or hi2 > hi + tiny:
            i = np.arange(old.shape[a]).reshape(shp)
            face |= np.broadcast_to((i < face_cells) | (i >= old.shape[a] - face_cells), old.shape)
    out["outside"] = float(rho[cut].sum()) / tot
    out["face"] = float(rho[face].sum()) / tot
    coarse = [a for a in range(old.ndim) if float(new.d[a]) > float(old.d[a]) * (1 + 1e-12)]
    if coarse:
        F = np.fft.fftn(comps, axes=tuple(range(1, old.ndim + 1)))
        w = np.sum(F.real ** 2 + F.imag ** 2, axis=0)
        drop = np.zeros(old.shape, bool)
        for a in coarse:
            r = old.shape[a] * float(old.d[a]) / (2.0 * float(new.d[a]))
            shp = [1] * old.ndim
            shp[a] = -1
            m = _modes(old.shape[a]).reshape(shp)
            drop |= np.broadcast_to((m < -r - 1e-9) | (m >= r - 1e-9), old.shape)
        out["spectrum"] = float(w[drop].sum() / w.sum())
    return out


def translate(psi, grid: Grid, shift) -> np.ndarray:
    """psi(r - shift) of the band-limited wave (the spectrum times exp(-i k . shift)): exact for the periodic
    interpolant, unitary on the grid; what lies within |shift| of the face it moves towards comes in on the other side
    (the caller measures it, ``wrap_fraction``)."""
    p = np.asarray(psi, complex)
    off = 1 if p.ndim == grid.ndim + 1 else 0
    axes = tuple(range(off, off + grid.ndim))
    F = np.fft.fftn(p, axes=axes)
    ph = 1.0
    for a, K in enumerate(grid.kmesh()):
        ph = ph * np.exp(-1j * K * float(shift[a]))
    return np.fft.ifftn(F * ph, axes=axes)


def wrap_fraction(psi, grid: Grid, shift, margin: float = 0.0) -> float:
    """The fraction of the wave's norm that ``translate`` by ``shift`` carries across a face of the periodic window
    (the probability within |shift_a| of the face it moves towards, along any axis). With ``margin`` > 0 (the width of
    open edges' absorbing layers, ``absorbing_layer``) only what lands beyond the far side's layer, inside the window,
    is counted: what lands in that layer is absorbed by it like any wave entering it (review LB1-p02-ux Q8)."""
    p = np.asarray(psi, complex)
    comps = p if p.ndim == grid.ndim + 1 else p[None]
    rho = np.sum(comps.real ** 2 + comps.imag ** 2, axis=0)
    tot = float(rho.sum())
    if not tot > 0:
        return 0.0
    m = np.zeros(grid.shape, bool)
    w = float(margin)
    for a in range(grid.ndim):
        s = float(shift[a])
        if s == 0:
            continue
        lo, hi = window(grid, a)
        shp = [1] * grid.ndim
        shp[a] = -1
        x = grid.axes[a].reshape(shp)
        m |= np.broadcast_to((x + s >= hi + w) if s > 0 else (x + s < lo - w), grid.shape)
    return float(rho[m].sum()) / tot
