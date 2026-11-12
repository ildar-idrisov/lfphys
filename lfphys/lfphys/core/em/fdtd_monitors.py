# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Monitors of the FDTD solver (``lfphys.core.em.fdtd``): probes, running discrete Fourier transforms, Poynting
fluxes, cross sections and the near-to-far-field transform.

Conventions: time dependence exp(-i omega t) for complex amplitudes; a running DFT is
F(omega) = sum_n F(t_n) exp(i omega t_n) dt over the steps since the monitor was added, each component at its own
sample times (E at t_n = n dt, H at t_n - dt/2), so E and H spectra refer to the same continuous-time spectrum.

* **Probes**: a component at a point, linearly interpolated from its Yee nodes, every step.
* **Fluxes** through a plane face (a line in 2-D) at an integer grid plane: the tangential E on the plane and the
  tangential H on the two half planes beside it are averaged to the centres of the face's cells (second-order
  accurate), S_n = E_t1 H_t2 - E_t2 H_t1 for (n, t1, t2) cyclic. Per frequency P(omega) = (1/2) Re sum S(Ê, Ĥ*) dA;
  in time, at t_n with H averaged over t_n -+ dt/2. A closed box sums its faces with outward normals.
  The face-centre averaging makes the monitor measure the grid's own plane wave weaker than its true flux density:
  a term E_t1 H_t2 is multiplied by cos(k_v dx/2) cos^2(k_t2 dx/2) (v the normal; no factor along a collapsed axis),
  i.e. 2-D TM cos(k_v dx/2) cos^2(k_t dx/2), 2-D TE cos(k_v dx/2), cos(k dx/2) = 1 - (k dx)^2/8 + ... at normal
  incidence (``fdtd_tfsf.monitor_factor``; measured on the incident wave to 2e-9). The bias depends on the wave's
  direction and is second order, like the averaging's error for any field.
* **Cross sections** (with a TF/SF plane wave): sigma_sca = P_sca / I_inc from a closed box in the scattered-field
  region; sigma_abs = -P_net / I_inc from a closed box in the total-field region; sigma_ext = sigma_sca + sigma_abs.
  I_inc is either (``normalisation="exact"``) (1/2) |G(omega)|^2 sqrt(eps / mu), the true intensity of the injected
  discrete plane wave, G the DFT of its E amplitude at the reference point over the same steps (its H / E is
  |K| / (Omega mu) = sqrt(eps / mu) by its dispersion relation) — exact, but not what the monitor measures for that
  wave — or (``"monitor"``) that times the monitor factor through planes normal to the incidence axis: the incident
  wave as the monitor measures it (Meep's normalisation run, in closed form), which cancels the monitor's bias exactly
  for reflected and transmitted plane waves along that axis. For scattering into all directions neither choice removes
  the bias on the scattered waves (review B8-fdtd F5: the earlier statement that I_inc is "exact for the grid's plane
  wave" hid that the monitor sees the wave weaker by (k dx)^2/8, error in earlier).
* **Near to far field**: on a closed box in the scattered-field region the equivalent currents J = n x H,
  M = -n x E (face-centred, as for the flux) radiate through the free-space Green's function of the background
  (derived from the vector potentials A = mu int J g, F = eps int M g, E = i omega A_t - (1/eps) curl F in the far
  zone, exp(-i omega t); checked in the tests against the cylinder series and the Mie series):
  3-D (radiation vectors N = sum J exp(-i k r.r') dA, L likewise with M): E_theta = i k g (eta N_theta + L_phi), E_phi = i k g (eta N_phi - L_theta),
  g = exp(i k r) / (4 pi r); 2-D (line integrals; g2 = exp(i (k rho + pi/4)) / sqrt(8 pi k rho)): TM
  E_z = i k g2 (eta N_z - L_phi), TE H_z = i k g2 (L_z / eta + N_phi). Differential cross sections:
  3-D dsigma/dOmega = r^2 |E|^2 / |E_inc|^2; 2-D dsigma/dphi = rho |E_z|^2 / |E_inc|^2 (TE with H). k is the
  continuum wavenumber of the background (the transform's error is second order in the cell like the fields').
"""

from __future__ import annotations

import math

import numpy as np

from ...i18n import T
from .. import backend

ABOUT = {
    "layer": "core", "kind": "numerics",
    "title": T("FDTD: probes, spectra, fluxes, cross sections, the far field"),
    "statement": T("Fields at points; a running discrete Fourier transform on lines, planes and in volumes; the "
                   "Poynting flux through planes and closed boxes (in time and per frequency); scattering, absorption "
                   "and extinction cross sections; the near-to-far-field transform (2-D and 3-D) through equivalent "
                   "currents on a closed surface."),
    "validity": T("second order in the cell (the fields are brought to the face centres by averaging neighbouring Yee "
                  "nodes, so the monitor sees the grid's plane wave weaker by a factor 1 − O((k dx)²) that depends on "
                  "the direction; at normal incidence cos(k dx/2)); cross sections with the exact or the “monitor” "
                  "normalisation of the incident wave; the far field by the Green's function of a homogeneous lossless "
                  "background"),
    "basis": [T("the equivalence theorem and the vector potentials in the far zone (derived; checked in the tests "
                "against the exact series of the cylinder and of Mie)"),
              T("the asymptotics of the Hankel function, DLMF 10.17.5 (2-D)")],
    "conflicts": [],
}


class Gather:
    """The nodes of one component in an index box (start, stop) per axis; stop may pass the end of a periodic axis
    (wrapped, with the Bloch phase)."""

    def __init__(self, sim, comp: str, ranges):
        self.comp = comp
        self.ranges = [(int(a), int(b)) for a, b in ranges]
        self.shape = tuple(b - a for a, b in self.ranges)
        idx, wrap = [], []
        ph = np.ones(self.shape, complex) if sim.complex else None
        for u, (a, b) in enumerate(self.ranges):
            n = sim.shape[u]
            r = np.arange(a, b)
            if (r < 0).any() or (r >= n).any():
                if not sim.periodic[u]:
                    raise ValueError(T("the monitor's region extends beyond the grid"))
                if ph is not None:
                    k = np.floor_divide(r, n)  # how many periods
                    f = np.exp(1j * sim.bloch[u] * sim.shape[u] * sim.dx * k)
                    sh = [1, 1, 1]
                    sh[u] = len(r)
                    ph = ph * f.reshape(sh)
                r = np.mod(r, n)
                wrap.append(True)
            else:
                wrap.append(False)
            idx.append(r)
        self.idx = idx
        self.contiguous = not any(wrap)
        self.slices = tuple(slice(a, b) for a, b in self.ranges) if self.contiguous else None
        self.phase = None if (ph is None or np.all(ph == 1)) else ph
        self._dev = None

    def take(self, sim):
        F = sim.F[self.comp]
        if self.contiguous:
            v = F[self.slices]
        else:
            if self._dev is None or self._dev[0] is not sim.xp:
                self._dev = (sim.xp, sim.xp.ix_(*[sim.xp.asarray(i) for i in self.idx]),
                             None if self.phase is None else sim.xp.asarray(self.phase))
            v = F[self._dev[1]]
            if self._dev[2] is not None:
                v = v * self._dev[2]
        return v


class Accumulator:
    """Running DFT of a gathered component at frequencies ``freqs`` (cycles per time unit)."""

    def __init__(self, sim, gather: Gather, freqs, h_time: bool):
        self.g = gather
        self.freqs = np.asarray(freqs, float)
        self.h_time = h_time  # sampled at t - dt/2
        self.acc = sim.xp.zeros((len(self.freqs),) + gather.shape, complex)

    def add(self, sim, t):
        ts = t - (0.5 * sim.dt if self.h_time else 0.0)
        ph = np.exp(2j * math.pi * self.freqs * ts) * sim.dt
        v = self.g.take(sim)
        xp = sim.xp
        self.acc += xp.asarray(ph).reshape((-1,) + (1,) * v.ndim) * v[None]

    def host(self):
        return backend.to_numpy(self.acc)

    def to(self, xp):
        self.acc = xp.asarray(backend.to_numpy(self.acc)) if xp is not np else backend.to_numpy(self.acc)
        self.g._dev = None


def _cyc(v):
    return (v + 1) % 3, (v + 2) % 3


class Face:
    """A face normal to axis ``v`` at the integer plane index ``p``, over cells [a_t, b_t) of the transverse axes;
    ``sign`` +1 or -1: the outward direction (for a box) or the flux direction (for a plane)."""

    def __init__(self, sim, v: int, p: int, cells, sign: int, freqs):
        self.v, self.p, self.sign = int(v), int(p), int(sign)
        self.cells = [tuple(int(c) for c in cc) for cc in cells]  # per axis (start, stop); the v entry ignored
        t1, t2 = _cyc(v)
        self.t1, self.t2 = t1, t2
        self.freqs = None if freqs is None else np.asarray(freqs, float)
        names = "xyz"
        self.E = {}
        self.H = {}
        for kind, store in (("e", self.E), ("h", self.H)):
            for t in (t1, t2):
                comp = kind + names[t]
                if comp not in sim.comps:
                    continue
                ranges, avg = [], []
                for u in range(3):
                    if u >= sim.dim:  # collapsed axis (2-D): one node
                        ranges.append((0, 1))
                        avg.append(False)
                        continue
                    off = sim.offset(comp, u)
                    if u == v:
                        if off == 0.0:
                            ranges.append((p, p + 1))
                            avg.append(False)
                        else:
                            ranges.append((p - 1, p + 1))
                            avg.append(True)
                    else:
                        a, b = self.cells[u]
                        if off == 0.5:
                            ranges.append((a, b))
                            avg.append(False)
                        else:
                            ranges.append((a, b + 1))
                            avg.append(True)
                g = Gather(sim, comp, ranges)
                store[t] = {"g": g, "avg": avg, "acc": None if freqs is None else Accumulator(sim, g, freqs,
                                                                                            kind == "h")}
        self.npts = tuple((self.cells[u][1] - self.cells[u][0]) if (u != v and u < sim.dim) else 1 for u in range(3))
        self.dA = sim.dx ** (sim.dim - 1)
        self._hprev = None

    @staticmethod
    def _average(a, avg, lead=0):
        for u, f in enumerate(avg):
            if f:
                ax = u + lead
                n = a.shape[ax]
                s0 = [slice(None)] * a.ndim
                s1 = [slice(None)] * a.ndim
                s0[ax] = slice(0, n - 1)
                s1[ax] = slice(1, n)
                a = 0.5 * (a[tuple(s0)] + a[tuple(s1)])
        return a

    def points(self, sim):
        """Coordinates (x, y, z arrays of the face's points)."""
        out = []
        for u in range(3):
            if u >= sim.dim:
                out.append(np.zeros(1))
            elif u == self.v:
                out.append(np.array([sim.coord(self.p, u)]))
            else:
                a, b = self.cells[u]
                out.append(sim.coord(np.arange(a, b) + 0.5, u))
        return np.meshgrid(*out, indexing="ij")

    def spectral_fields(self):
        """{"e1", "e2", "h1", "h2"}: tangential fields at the face points, arrays (nf, *npts) (zeros if absent)."""
        nf = len(self.freqs)
        out = {}
        for key, store, t in (("e1", self.E, self.t1), ("e2", self.E, self.t2), ("h1", self.H, self.t1),
                              ("h2", self.H, self.t2)):
            if t in store:
                out[key] = self._average(store[t]["acc"].host(), store[t]["avg"], lead=1)
            else:
                out[key] = np.zeros((nf,) + self.npts, complex)
        return out

    def flux_spectrum(self):
        f = self.spectral_fields()
        S = f["e1"] * np.conj(f["h2"]) - f["e2"] * np.conj(f["h1"])
        return self.sign * 0.5 * np.real(S.reshape(len(self.freqs), -1).sum(axis=1)) * self.dA

    def accumulate(self, sim, kind: str, t: float):
        if self.freqs is None:
            return
        for store in (self.E if kind == "e" else self.H).values():
            store["acc"].add(sim, t)

    def h_before(self, sim):
        self._hprev = {t: s["g"].take(sim).copy() for t, s in self.H.items()}

    def time_flux(self, sim):
        """Instantaneous power through the face at t_n: E^n with H averaged over t_n -+ dt/2 (call after the H
        update, with ``h_before`` called before it)."""
        xp = sim.xp
        f = {}
        for key, store, t in (("e1", self.E, self.t1), ("e2", self.E, self.t2)):
            if t in store:
                f[key] = self._average(store[t]["g"].take(sim), store[t]["avg"])
        for key, t in (("h1", self.t1), ("h2", self.t2)):
            if t in self.H:
                h = 0.5 * (self._hprev[t] + self.H[t]["g"].take(sim))
                f[key] = self._average(h, self.H[t]["avg"])
        s = 0.0
        if "e1" in f and "h2" in f:
            s = s + xp.sum(xp.real(f["e1"] * xp.conj(f["h2"])) if sim.complex else f["e1"] * f["h2"])
        if "e2" in f and "h1" in f:
            s = s - xp.sum(xp.real(f["e2"] * xp.conj(f["h1"])) if sim.complex else f["e2"] * f["h1"])
        return self.sign * s * self.dA

    def to(self, xp):
        for store in (self.E, self.H):
            for s in store.values():
                s["g"]._dev = None
                if s["acc"] is not None:
                    s["acc"].to(xp)
        self._hprev = None


def far_field_2d(faces, sim, freq_index: int, phis, k: float, eta: float, pol: str):
    """Radiation integrals of a closed contour (2-D) at angles ``phis`` (radians from +x): returns the far-field
    amplitude A(phi) with E_z (TM) or H_z (TE) = A exp(i (k rho + pi/4)) / sqrt(8 pi k rho) * i k."""
    phis = np.asarray(phis, float)
    rx, ry = np.cos(phis), np.sin(phis)
    N = np.zeros((3, len(phis)), complex)
    L = np.zeros((3, len(phis)), complex)
    for fc in faces:
        f = fc.spectral_fields()
        X, Y, _ = fc.points(sim)
        n = np.zeros(3)
        n[fc.v] = fc.sign
        E = np.zeros((3,) + fc.npts, complex)
        H = np.zeros((3,) + fc.npts, complex)
        E[fc.t1], E[fc.t2] = f["e1"][freq_index], f["e2"][freq_index]
        H[fc.t1], H[fc.t2] = f["h1"][freq_index], f["h2"][freq_index]
        J = np.cross(n, H, axis=0)
        M = -np.cross(n, E, axis=0)
        ph = np.exp(-1j * k * (np.outer(rx, X.ravel()) + np.outer(ry, Y.ravel())))  # (nphi, npts)
        N += (J.reshape(3, -1) @ ph.T) * fc.dA
        L += (M.reshape(3, -1) @ ph.T) * fc.dA
    Lphi = -L[0] * ry + L[1] * rx
    Nphi = -N[0] * ry + N[1] * rx
    if pol == "tm":
        return eta * N[2] - Lphi
    return L[2] / eta + Nphi


def far_field_3d(faces, sim, freq_index: int, theta, phi, k: float, eta: float):
    """(E_theta, E_phi) far-field amplitudes A with E = i k A exp(i k r) / (4 pi r) at directions (theta, phi)."""
    th, ph_ = np.broadcast_arrays(np.asarray(theta, float), np.asarray(phi, float))
    shp = th.shape
    th, ph_ = th.ravel(), ph_.ravel()
    r = np.stack([np.sin(th) * np.cos(ph_), np.sin(th) * np.sin(ph_), np.cos(th)])
    et = np.stack([np.cos(th) * np.cos(ph_), np.cos(th) * np.sin(ph_), -np.sin(th)])
    ep = np.stack([-np.sin(ph_), np.cos(ph_), np.zeros_like(ph_)])
    N = np.zeros((3, len(th)), complex)
    L = np.zeros((3, len(th)), complex)
    for fc in faces:
        f = fc.spectral_fields()
        X, Y, Z = fc.points(sim)
        n = np.zeros(3)
        n[fc.v] = fc.sign
        E = np.zeros((3,) + fc.npts, complex)
        H = np.zeros((3,) + fc.npts, complex)
        E[fc.t1], E[fc.t2] = f["e1"][freq_index], f["e2"][freq_index]
        H[fc.t1], H[fc.t2] = f["h1"][freq_index], f["h2"][freq_index]
        J = np.cross(n, H, axis=0).reshape(3, -1)
        M = -np.cross(n, E, axis=0).reshape(3, -1)
        P = np.stack([X.ravel(), Y.ravel(), Z.ravel()])
        ph = np.exp(-1j * k * (r.T @ P))  # (ndir, npts)
        N += (J @ ph.T) * fc.dA
        L += (M @ ph.T) * fc.dA
    Nt, Np = (N * et).sum(0), (N * ep).sum(0)
    Lt, Lp = (L * et).sum(0), (L * ep).sum(0)
    return (eta * Nt + Lp).reshape(shp), (eta * Np - Lt).reshape(shp)
