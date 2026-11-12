# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""One-dimensional Schroedinger equation  i hbar dpsi/dt = -hbar^2/(2m) psi'' + V(x) psi  on a uniform grid.

* Time evolution: Strang split-operator method,
      psi(t + dt) = e^{-iV dt/2hbar} F^-1 e^{-i hbar k^2 dt/2m} F e^{-iV dt/2hbar} psi(t),
  unitary, exact for V = 0 (up to the periodic box), local error O(dt^3) per step with commutator [T, V].
* Stationary states: the Fourier-grid (sinc-DVR) Hamiltonian of Colbert & Miller (1992), whose kinetic matrix
      T_ii = hbar^2 pi^2 / (6 m dx^2),  T_ij = hbar^2 (-1)^(i-j) / (m dx^2 (i-j)^2)
  converges exponentially for smooth potentials.
* Observables: norm, <x>, <p>, <H>, probability current j = (hbar/m) Im(psi* psi').
* Packets: Gaussian with closed-form free evolution (width sigma(t) = sigma sqrt(1 + (hbar t / (2 m sigma^2))^2));
  ``FreeGaussians``: superpositions of them in closed form (psi, dpsi/dx, current, momentum amplitude, P(x < L)).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import linalg

ABOUT = {
    "layer": "core", "kind": "law",
    "title": "Уравнение Шрёдингера в одном измерении",
    "statement": "Унитарная эволюция волновой функции (метод расщепления оператора), стационарные состояния "
                 "(спектральный метод Колберта–Миллера), наблюдаемые и ток вероятности, свободный гауссов пакет.",
    "validity": "нерелятивистская частица без спина; на сетке — достаточно мелкий шаг и широкое окно (контроль "
                "нормы и энергии в каждом запуске)",
    "basis": ["Schrödinger 1926", "Feit, Fleck, Steiger, J. Comput. Phys. 47, 412 (1982)",
              "Colbert & Miller, J. Chem. Phys. 96, 1982 (1992)"],
    "conflicts": [],
}


class Grid:
    def __init__(self, x, m: float, hbar: float = 1.0):
        self.x = np.asarray(x, float)
        self.n = len(self.x)
        self.dx = float(self.x[1] - self.x[0])
        self.m, self.hbar = m, hbar
        self.k = 2 * math.pi * np.fft.fftfreq(self.n, self.dx)

    # --- states ---------------------------------------------------------------------------------------------
    def gaussian(self, x0: float, k0: float, sigma: float) -> np.ndarray:
        """Normalised packet with position spread sigma (of |psi|^2) and mean wavenumber k0."""
        psi = np.exp(-((self.x - x0) ** 2) / (4 * sigma**2) + 1j * k0 * self.x)
        return psi / math.sqrt(self.norm(psi))

    def free_gaussian_width(self, sigma: float, t):
        return sigma * np.sqrt(1 + (self.hbar * np.asarray(t) / (2 * self.m * sigma**2)) ** 2)

    # --- observables ------------------------------------------------------------------------------------------
    def norm(self, psi) -> float:
        return float(np.sum(np.abs(psi) ** 2) * self.dx)

    def mean_x(self, psi) -> float:
        return float(np.sum(self.x * np.abs(psi) ** 2) * self.dx / self.norm(psi))

    def mean_p(self, psi) -> float:
        phi = np.fft.fft(psi)
        w = np.abs(phi) ** 2
        return float(self.hbar * np.sum(self.k * w) / np.sum(w))

    def energy(self, psi, V) -> float:
        phi = np.fft.fft(psi)
        w = np.abs(phi) ** 2
        T = np.sum(self.hbar**2 * self.k**2 / (2 * self.m) * w) / np.sum(w)
        return float(T + np.sum(V * np.abs(psi) ** 2) * self.dx / self.norm(psi))

    def current(self, psi) -> np.ndarray:
        dpsi = np.fft.ifft(1j * self.k * np.fft.fft(psi))
        return self.hbar / self.m * np.imag(np.conj(psi) * dpsi)

    # --- dynamics -------------------------------------------------------------------------------------------
    def stepper(self, V, dt: float, absorb=None):
        """A function psi -> psi(t + dt) (Strang splitting). ``absorb``: optional imaginary potential W >= 0 at the
        edges (multiplies by exp(-W dt/hbar)), a numerical device to let outgoing waves leave the window."""
        half = np.exp(-0.5j * np.asarray(V, float) * dt / self.hbar)
        if absorb is not None:
            half = half * np.exp(-0.5 * np.asarray(absorb, float) * dt / self.hbar)
        kin = np.exp(-0.5j * self.hbar * self.k**2 * dt / self.m)

        def step(psi):
            return half * np.fft.ifft(kin * np.fft.fft(half * psi))
        return step

    # --- stationary states -------------------------------------------------------------------------------------
    def hamiltonian(self, V) -> np.ndarray:
        i = np.arange(self.n)
        d = i[:, None] - i[None, :]
        with np.errstate(divide="ignore"):
            T = np.where(d == 0, math.pi**2 / 6.0, (-1.0) ** np.abs(d) / np.where(d == 0, 1, d) ** 2)
        T = T * self.hbar**2 / (self.m * self.dx**2)
        return T + np.diag(np.asarray(V, float))

    def eigenstates(self, V, n_states: int = 10):
        """Lowest energies and normalised eigenfunctions (columns)."""
        E, vec = linalg.eigh(self.hamiltonian(V), subset_by_index=[0, n_states - 1])
        return E, vec / math.sqrt(self.dx)


def harmonic_levels(n, hbar: float, omega: float):
    return hbar * omega * (np.asarray(n) + 0.5)


class FreeGaussians:
    """A superposition of Gaussian packets on a line evolving freely, in closed form (no grid): packet j is
    c_j (2 pi s_j^2)^(-1/4) exp(-(x - x_j)^2 / (4 s_j^2) + i k_j x) at t = 0 (as ``Grid.gaussian``) and spreads to the
    width ``Grid.free_gaussian_width``; the sum is normalised. Gives psi, dpsi/dx, the current, the cumulative
    probability left of a point and the momentum amplitude psi~(k) = (2 pi)^(-1/2) int psi(x, 0) e^{-ikx} dx
    (normalised in k), e.g. for arrival-time distributions (``lfphys.theories.interpretations.arrival_times``)."""

    def __init__(self, packets, m: float = 1.0, hbar: float = 1.0):
        self.p = [(complex(c), float(x0), float(k0), float(s)) for c, x0, k0, s in packets]
        self.m, self.hbar = float(m), float(hbar)
        self.norm2 = self._overlap()

    def _overlap(self) -> float:
        """<psi|psi> of the unnormalised sum: the Gaussian integral of conj(phi_i) phi_j over k in closed form."""
        tot = 0.0
        for ci, xi, ki, si in self.p:
            for cj, xj, kj, sj in self.p:
                a = si * si + sj * sj
                b = 2 * si * si * ki + 2 * sj * sj * kj + 1j * (xi - xj)
                c = -(si * ki) ** 2 - (sj * kj) ** 2 - 1j * ki * xi + 1j * kj * xj
                tot += (np.conj(ci) * cj * math.sqrt(2 * si * sj / math.pi) * np.sqrt(math.pi / a)
                        * np.exp(b * b / (4 * a) + c))
        return float(np.real(tot))

    def _parts(self, x, t):
        x = np.asarray(x, float)
        t = np.asarray(t, float)
        psi = 0.0
        dpsi = 0.0
        for c, x0, k0, s in self.p:
            st2 = s * s + 1j * self.hbar * t / (2 * self.m)
            v = self.hbar * k0 / self.m
            g = c * (2 * math.pi * s * s) ** -0.25 * s / np.sqrt(st2) * np.exp(
                -((x - x0 - v * t) ** 2) / (4 * st2) + 1j * k0 * x - 1j * self.hbar * k0 * k0 * t / (2 * self.m))
            psi = psi + g
            dpsi = dpsi + g * (-(x - x0 - v * t) / (2 * st2) + 1j * k0)
        n = math.sqrt(self.norm2)
        return psi / n, dpsi / n

    def psi(self, x, t):
        return self._parts(x, t)[0]

    def dpsi(self, x, t):
        return self._parts(x, t)[1]

    def current(self, x, t):
        p, d = self._parts(x, t)
        return self.hbar / self.m * np.imag(np.conj(p) * d)

    def phi(self, k):
        """Momentum amplitude (normalised in k)."""
        k = np.asarray(k, float)
        out = 0.0
        for c, x0, k0, s in self.p:
            # (2 pi)^(-1/2) int (2 pi s^2)^(-1/4) e^{-(x-x0)^2/(4 s^2) + i k0 x} e^{-ikx} dx
            #   = (2 s^2/pi)^(1/4) e^{-s^2 (k-k0)^2} e^{-i (k - k0) x0}
            out = out + c * (2 * s * s / math.pi) ** 0.25 * np.exp(-(s * (k - k0)) ** 2 - 1j * (k - k0) * x0)
        return out / math.sqrt(self.norm2)

    def cdf(self, L: float, t, n: int = 4001, width: float = 12.0) -> np.ndarray:
        """P(x < L) at times t (array): the density integrated from far left (``width`` spreads before the leftmost
        packet) to L by Simpson's rule on ``n`` points."""
        from scipy.integrate import simpson
        t = np.atleast_1d(np.asarray(t, float))
        out = np.empty(len(t))
        for i, ti in enumerate(t):
            lo = min(x0 + self.hbar * k0 / self.m * ti
                     - width * s * math.sqrt(1 + (self.hbar * ti / (2 * self.m * s * s)) ** 2)
                     for _, x0, k0, s in self.p)
            if lo >= L:
                out[i] = 0.0
                continue
            x = np.linspace(lo, L, n)
            out[i] = simpson(np.abs(self.psi(x, ti)) ** 2, x=x)
        return out
