# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The two-level atom in a near-resonant field (plan item P5): Rabi oscillations, the optical Bloch equations with
T1 and T2, their steady state, Torrey's transient solutions, and the waiting-time distribution of the fluorescence
photons.

Conventions (Steck, Quantum and Atom Optics, rev. 0.16.11, ch. 5; checked against the text): basis (|e>, |g>), so
that sigma_z = |e><e| - |g><g| = diag(1, -1) is the Pauli matrix of ``qubits``; sigma = |g><e| the lowering operator;
detuning Delta = omega - omega_0 (laser minus atom); rotating-frame Hamiltonian in the rotating-wave approximation

    H = -Delta |e><e| + (Omega/2)(sigma + sigma^+)                         (Steck 5.26, 5.27; hbar = 1)

Bloch vector (u, v, w) = (<sigma_x>, <sigma_y>, <sigma_z>), u = rho_eg + rho_ge, v = i(rho_eg - rho_ge),
w = rho_ee - rho_gg (Steck 5.107). Damping: longitudinal Gamma = 1/T1 (spontaneous decay, jump operator
sqrt(Gamma) sigma), transverse gamma_perp = 1/T2 = Gamma/2 + gamma_c with extra dephasing gamma_c >= 0 (jump operator
sqrt(gamma_c/2) sigma_z), so T2 <= 2 T1 (Steck 5.124, 5.177). Optical Bloch equations (Steck 5.127):

    du/dt = Delta v - u/T2,   dv/dt = -Delta u - Omega w - v/T2,   dw/dt = Omega v - (w + 1)/T1.

* Rabi (no damping): P_e(t) = (Omega^2/W^2) sin^2(W t/2), W = sqrt(Omega^2 + Delta^2) (Steck 5.54, 5.60); amplitudes
  for any initial state (Steck 5.58).
* Steady state (Steck 5.132, 5.133), written with D = Gamma (g^2 + Delta^2) + Omega^2 g, g = 1/T2:
  u = Omega Delta Gamma / D, v = Omega Gamma g / D, w = -Gamma (g^2 + Delta^2) / D (regular also for Gamma -> 0).
* General transient solution: x(t) = x_ss + exp(Q t)(x0 - x_ss) (Steck 5.149: Q and the cubic f(s) of its
  eigenvalues; Torrey 1949), computed exactly through the 4 x 4 augmented exponential (``bloch_solution``).
* Torrey's closed forms where they apply (Steck 5.5.2.3 lists Torrey's regimes: exact resonance; gamma_perp = Gamma;
  strong field): (1) ``torrey_resonance``: Delta = 0, any T1, T2 and initial vector: u decays as exp(-t/T2), (v, w)
  form a damped oscillator with rate kappa = (1/T1 + 1/T2)/2 and frequency lambda = sqrt(Omega^2 - delta^2),
  delta = (1/T2 - 1/T1)/2 (over-damped and critical cases included); for T2 = 2 T1 and a ground-state start it is
  Steck's 5.171 and 5.176 (tested); (2) ``torrey_equal_times``: T1 = T2 = T, any detuning: a rotation about the
  precession vector (Omega, 0, -Delta) (Steck 5.126) damped as exp(-t/T). Torrey's strong-field approximation is not
  used (``bloch_solution`` is exact everywhere).
* Fluorescence photon statistics: after each emission the atom is in |g>; with no emission it evolves under
  H_eff = H - (i Gamma/2)|e><e|. The probability of no emission for a time tau is P0(tau) = ||exp(-i H_eff tau)|g>||^2
  (Plenio & Knight, RMP 70, 101 (1998), eqs. 66, 67) and the waiting-time density is Gamma |c_e(tau)|^2 = -dP0/dtau
  (their eq. 30). With s_{1,2} the roots of s^2 - (i Delta - Gamma/2) s + Omega^2/4 = 0, sbar = (s1 + s2)/2,
  eps = (s1 - s2)/2: c_e = -i (Omega/2) exp(sbar tau) sinh(eps tau)/eps, c_g = exp(sbar tau)(cosh(eps tau) -
  sbar sinh(eps tau)/eps); at Delta = 0: w(tau) = Gamma Omega^2/(Omega^2 - Gamma^2/4) exp(-Gamma tau/2)
  sin^2(sqrt(Omega^2 - Gamma^2/4) tau/2) (derived here; tested against the engine's non-Hermitian propagation).
* Lab frame: H_lab(t) = (omega_0/2) sigma_z + (Omega/2)(cos(omega t) sigma_x + sin(omega t) sigma_y) (circular
  drive) is exactly the rotating-frame H (up to a constant) under rho_lab = R^+ rho_rot R, R = exp(i omega t
  sigma_z/2); the jump operators sigma and sigma_z only acquire phases, so the damped lab-frame dynamics is exact too
  (no RWA for a circular drive). A linear drive Omega cos(omega t) sigma_x adds the counter-rotating term, which the
  RWA drops; to lowest order it shifts the resonance by the Bloch-Siegert shift Omega^2/(4 omega_0) (Steck 5.556):
  the size of the RWA error stated in ``validity``. Such drives go through ``open_systems.evolve`` with the full
  H(t); this module does not model them.
"""

from __future__ import annotations

import cmath
import math

import numpy as np
from scipy import linalg

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "law",
    "title": T("Two-level atom: Rabi oscillations, optical Bloch equations, Torrey solutions"),
    "statement": T("H = −Δ|e⟩⟨e| + (Ω/2)σ_x; P_e = (Ω²/W²)sin²(Wt/2), W = √(Ω² + Δ²); the Bloch equations with T1, "
                   "T2 ≤ 2T1 and their steady state; Torrey's transient solutions (on resonance for any T1, T2; T1 = "
                   "T2 at any detuning) and the general exact solution; the distribution of intervals between "
                   "fluorescence photons."),
    "validity": T("the two-level approximation (the other levels far away), the dipole approximation; the "
                  "rotating-wave approximation: Ω, |Δ| ≪ ω0 (the correction is the Bloch–Siegert shift Ω²/(4ω0)); "
                  "exact for a circular field in the laboratory frame; damping is Markovian (the Lindblad equation, "
                  "core.quantum.open_systems)"),
    "basis": ["Rabi, Phys. Rev. 51, 652 (1937)", "Bloch, Phys. Rev. 70, 460 (1946)",
              T("Torrey, Phys. Rev. 76, 1059 (1949) — as presented by Steck, §5.5.2 (the paper itself was not "
                "retrieved)"),
              T("Steck, Quantum and Atom Optics, rev. 0.16.11 (2026), ch. 5: (5.26), (5.54)–(5.60), (5.124)–(5.138), "
                "(5.149)–(5.177), (5.556)"),
              "Plenio & Knight, Rev. Mod. Phys. 70, 101 (1998), eqs. (30), (66), (67)",
              T("Bloch & Siegert, Phys. Rev. 57, 522 (1940) — after Steck (5.556)"),
              T("lfphys/sources/verification_2026-10-29_p5.md — check of the quotations and derivations")],
    "conflicts": [],
}

U_ = 2.0 ** -53  # unit round-off of binary64

# basis (|e>, |g>)
E = np.array([1, 0], complex)
G = np.array([0, 1], complex)
SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)
SM = np.array([[0, 0], [1, 0]], complex)  # sigma = |g><e|
PE = np.array([[1, 0], [0, 0]], complex)  # |e><e|


def hamiltonian(Omega: float, Delta: float) -> np.ndarray:
    """Rotating-frame RWA Hamiltonian -Delta|e><e| + (Omega/2) sigma_x (hbar = 1)."""
    return -Delta * PE + 0.5 * Omega * SX


def rates(T1: float, T2: float) -> tuple[float, float, float]:
    """(Gamma, gamma_perp, gamma_c) from T1, T2 (math.inf allowed); ValueError unless 0 < T2 <= 2 T1."""
    if not (T1 > 0 and T2 > 0):
        raise ValueError("rates: T1 and T2 must be positive")
    G1 = 0.0 if math.isinf(T1) else 1.0 / T1
    gp = 0.0 if math.isinf(T2) else 1.0 / T2
    gc = gp - 0.5 * G1
    if gc < -4 * U_ * max(gp, G1):
        raise ValueError(f"rates: T2 = {T2} exceeds 2 T1 = {2 * T1} (complete positivity needs T2 <= 2 T1)")
    return G1, gp, max(gc, 0.0)


def collapse_operators(T1: float, T2: float) -> list[np.ndarray]:
    """Jump operators of the optical Bloch equations: sqrt(Gamma) sigma and sqrt(gamma_c/2) sigma_z."""
    G1, _, gc = rates(T1, T2)
    out = []
    if G1 > 0:
        out.append(math.sqrt(G1) * SM)
    if gc > 0:
        out.append(math.sqrt(0.5 * gc) * SZ)
    return out


def bloch_vector(rho) -> np.ndarray:
    rho = np.asarray(rho, complex)
    return np.real([np.trace(rho @ SX), np.trace(rho @ SY), np.trace(rho @ SZ)])


def density_matrix(x) -> np.ndarray:
    u, v, w = x
    return 0.5 * (np.eye(2) + u * SX + v * SY + w * SZ)


def excited_population(x) -> float | np.ndarray:
    return 0.5 * (1.0 + np.asarray(x)[..., 2])


# --- Rabi oscillations ----------------------------------------------------------------------------------------------

def generalized_rabi(Omega: float, Delta: float) -> float:
    return math.hypot(Omega, Delta)


def rabi_probability(t, Omega: float, Delta: float = 0.0):
    """P_e(t) from |g> without damping (Steck 5.60)."""
    W = generalized_rabi(Omega, Delta)
    if W == 0:
        return np.zeros_like(np.asarray(t, float))
    return (Omega / W) ** 2 * np.sin(0.5 * W * np.asarray(t, float)) ** 2


def rabi_amplitudes(t: float, Omega: float, Delta: float, cg0: complex = 1.0, ce0: complex = 0.0):
    """(c_e(t), c_g(t)) in the rotating frame for any initial amplitudes (Steck 5.58)."""
    W = generalized_rabi(Omega, Delta)
    ph = cmath.exp(0.5j * Delta * t)
    c, s = math.cos(0.5 * W * t), math.sin(0.5 * W * t)
    sw = 0.5 * t if W == 0 else s / W  # sin(W t/2)/W, its limit t/2 at W = 0
    ce = ph * (ce0 * c + 1j * (Delta * ce0 - Omega * cg0) * sw)
    cg = ph * (cg0 * c - 1j * (Delta * cg0 + Omega * ce0) * sw)
    return ce, cg


# --- optical Bloch equations ----------------------------------------------------------------------------------------

def bloch_matrix(Omega: float, Delta: float, T1: float, T2: float) -> tuple[np.ndarray, np.ndarray]:
    """(Q, b) with dx/dt = Q x + b (Steck 5.149: b = (0, 0, -Gamma))."""
    G1, gp, _ = rates(T1, T2)
    Q = np.array([[-gp, Delta, 0.0], [-Delta, -gp, -Omega], [0.0, Omega, -G1]])
    return Q, np.array([0.0, 0.0, -G1])


def bloch_steady_state(Omega: float, Delta: float, T1: float, T2: float) -> np.ndarray:
    """Steady Bloch vector in closed form (Steck 5.132, 5.133); ValueError where it is not unique."""
    G1, gp, _ = rates(T1, T2)
    D = G1 * (gp * gp + Delta * Delta) + Omega * Omega * gp
    if D == 0:
        raise ValueError("bloch_steady_state: no unique steady state (no damping, or no drive and no decay)")
    return np.array([Omega * Delta * G1 / D, Omega * G1 * gp / D, -G1 * (gp * gp + Delta * Delta) / D])


def steady_excited_population(Omega: float, Delta: float, T1: float, T2: float) -> float:
    """rho_ee(t -> inf) = (Omega^2/(2 gamma_perp Gamma)) / (1 + Delta^2/gamma_perp^2 + Omega^2/(gamma_perp Gamma))."""
    return float(excited_population(bloch_steady_state(Omega, Delta, T1, T2)))


def bloch_solution(t, Omega: float, Delta: float, T1: float, T2: float, x0=(0.0, 0.0, -1.0)) -> np.ndarray:
    """Exact Bloch vector(s) at t (scalar or array): the 4 x 4 exponential of [[Q, b], [0, 0]] (valid also without
    a unique steady state)."""
    Q, b = bloch_matrix(Omega, Delta, T1, T2)
    M = np.zeros((4, 4))
    M[:3, :3], M[:3, 3] = Q, b
    y0 = np.append(np.asarray(x0, float), 1.0)
    ts = np.atleast_1d(np.asarray(t, float))
    out = np.array([(linalg.expm(M * tk) @ y0)[:3] for tk in ts])
    return out[0] if np.ndim(t) == 0 else out


def _cos_sin_damped(t, kappa: float, delta: float, Omega: float):
    """exp(-kappa t) cosh(mu t) and exp(-kappa t) sinh(mu t)/mu, mu^2 = delta^2 - Omega^2 (cos and sin/lambda when
    mu^2 < 0), evaluated without overflow."""
    t = np.asarray(t, float)
    m2 = delta * delta - Omega * Omega
    if m2 < 0:
        lam = math.sqrt(-m2)
        e = np.exp(-kappa * t)
        return e * np.cos(lam * t), e * (np.sin(lam * t) / lam)
    if m2 == 0:
        e = np.exp(-kappa * t)
        return e, e * t
    mu = math.sqrt(m2)
    a, b = np.exp((mu - kappa) * t), np.exp(-(mu + kappa) * t)
    return 0.5 * (a + b), 0.5 * (a - b) / mu


def torrey_resonance(t, Omega: float, T1: float, T2: float, x0=(0.0, 0.0, -1.0)) -> np.ndarray:
    """Torrey's exact solution at resonance (Delta = 0) for any T1, T2 <= 2 T1 and any initial Bloch vector:
    u = u0 exp(-t/T2); (v, w) - (v_ss, w_ss) = exp(-kappa t)[cosh(mu t) I + sinh(mu t)/mu N](y0), N = [[-delta,
    -Omega], [Omega, delta]], kappa = (1/T2 + 1/T1)/2, delta = (1/T2 - 1/T1)/2, mu^2 = delta^2 - Omega^2.
    Returns (..., 3)."""
    G1, gp, _ = rates(T1, T2)
    xs = bloch_steady_state(Omega, 0.0, T1, T2)
    u0, v0, w0 = x0
    y1, y2 = v0 - xs[1], w0 - xs[2]
    kappa, delta = 0.5 * (gp + G1), 0.5 * (gp - G1)
    ch, sh = _cos_sin_damped(t, kappa, delta, Omega)
    t = np.asarray(t, float)
    u = u0 * np.exp(-gp * t)
    v = xs[1] + ch * y1 + sh * (-delta * y1 - Omega * y2)
    w = xs[2] + ch * y2 + sh * (Omega * y1 + delta * y2)
    return np.stack([u, v, w], axis=-1)


def torrey_equal_times(t, Omega: float, Delta: float, T: float, x0=(0.0, 0.0, -1.0)) -> np.ndarray:
    """Torrey's exact solution for T1 = T2 = T at any detuning: x(t) = x_ss + exp(-t/T) R(p, |p| t)(x0 - x_ss), a
    rotation about the precession vector p = (Omega, 0, -Delta) (Rodrigues' formula). Returns (..., 3)."""
    xs = bloch_steady_state(Omega, Delta, T, T)
    y0 = np.asarray(x0, float) - xs
    p = np.array([Omega, 0.0, -Delta])
    W = float(np.linalg.norm(p))
    t = np.asarray(t, float)[..., None]
    if W == 0:
        rot = np.broadcast_to(y0, t.shape[:-1] + (3,))
    else:
        k = p / W
        th = W * t
        rot = y0 * np.cos(th) + np.cross(k, y0) * np.sin(th) + k * (k @ y0) * (1 - np.cos(th))
    return xs + np.exp(-t / T) * rot


# --- photon waiting times -------------------------------------------------------------------------------------------

def _exp_cosh_sinh(sbar: complex, eps: complex, tau):
    """exp(sbar tau) cosh(eps tau) and exp(sbar tau) sinh(eps tau)/eps without overflow: through the two exponentials
    exp((sbar +- eps) tau), whose real parts are <= 0 here (eigenvalues of -i H_eff); the series of sinh(z)/z for
    |z| = |eps tau| < 1e-3 (relative error below z^6/5040 < 2e-22)."""
    tau = np.asarray(tau, float)
    e1 = np.exp((sbar + eps) * tau)
    e2 = np.exp((sbar - eps) * tau)
    z = eps * tau
    small = np.abs(z) < 1e-3
    with np.errstate(divide="ignore", invalid="ignore"):
        sh_big = (e1 - e2) / (2 * eps) if eps != 0 else np.zeros_like(e1)
    sh = np.where(small, np.exp(sbar * tau) * tau * (1 + z * z / 6 + z ** 4 / 120), sh_big)
    return 0.5 * (e1 + e2), sh


def no_emission_amplitudes(tau, Omega: float, Delta: float, Gamma: float):
    """(c_e, c_g) of exp(-i H_eff tau)|g> in closed form (see the module docstring)."""
    a = 1j * Delta - 0.5 * Gamma
    disc = cmath.sqrt(a * a - Omega * Omega)
    sbar, eps = 0.5 * a, 0.5 * disc
    ch, sh = _exp_cosh_sinh(sbar, eps, tau)
    return -0.5j * Omega * sh, ch - sbar * sh


def no_emission_probability(tau, Omega: float, Delta: float, Gamma: float):
    """P0(tau) = ||exp(-i H_eff tau)|g>||^2: the probability of no photon for a time tau after an emission."""
    ce, cg = no_emission_amplitudes(tau, Omega, Delta, Gamma)
    return np.abs(ce) ** 2 + np.abs(cg) ** 2


def waiting_time_density(tau, Omega: float, Delta: float, Gamma: float):
    """w(tau) = Gamma |c_e(tau)|^2 = -dP0/dtau."""
    ce, _ = no_emission_amplitudes(tau, Omega, Delta, Gamma)
    return Gamma * np.abs(ce) ** 2


def waiting_time_density_resonant(tau, Omega: float, Gamma: float):
    """Delta = 0: Gamma Omega^2/(Omega^2 - Gamma^2/4) exp(-Gamma tau/2) sin^2(sqrt(Omega^2 - Gamma^2/4) tau/2) (the
    hyperbolic form when Omega < Gamma/2)."""
    tau = np.asarray(tau, float)
    m2 = Omega * Omega - 0.25 * Gamma * Gamma
    e = np.exp(-0.5 * Gamma * tau)
    if m2 > 0:
        return Gamma * Omega ** 2 / m2 * e * np.sin(0.5 * math.sqrt(m2) * tau) ** 2
    if m2 == 0:
        return Gamma * Omega ** 2 * e * (0.5 * tau) ** 2
    return Gamma * Omega ** 2 / (-m2) * e * np.sinh(0.5 * math.sqrt(-m2) * tau) ** 2


# --- lab frame ------------------------------------------------------------------------------------------------------

def lab_hamiltonian_circular(t: float, omega0: float, omega: float, Omega: float) -> np.ndarray:
    """(omega0/2) sigma_z + (Omega/2)(cos(omega t) sigma_x + sin(omega t) sigma_y)."""
    return 0.5 * omega0 * SZ + 0.5 * Omega * (math.cos(omega * t) * SX + math.sin(omega * t) * SY)


def rotating_frame(t: float, omega: float) -> np.ndarray:
    """R(t) = exp(i omega t sigma_z/2): rho_rot = R rho_lab R^+."""
    return np.diag([cmath.exp(0.5j * omega * t), cmath.exp(-0.5j * omega * t)])


def to_lab(rho_rot, t: float, omega: float) -> np.ndarray:
    R = rotating_frame(t, omega)
    return R.conj().T @ np.asarray(rho_rot, complex) @ R
