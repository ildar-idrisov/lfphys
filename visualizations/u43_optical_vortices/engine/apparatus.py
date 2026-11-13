# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u43 apparatus over the engine lfphys (orchestration and drawing data, no physics of its own): the beam of a world
as a radial table of the engine's exact vector beam or of the paraxial mode (``lfphys.core.optics.beams.RadialTable``),
the grids the scene samples it on (volume, equiphase sheets, flow lines, slices), the masks of the generators, the
rotating elements and the detector's samples. Units: micrometres; world time in seconds."""

from __future__ import annotations

import math

import numpy as np

from lfphys.core.optics import angular_spectrum as AS
from lfphys.core.optics import beams as B
from lfphys.core.optics import beams_rotation as ROT
from lfphys.theories.approx import beams_paraxial as PX
from lfphys.theories.approx import beams_thin_masks as TM
from lfphys.i18n import T
from lfviz.errors import Refusal

POLS = {"+1": {1: 1.0}, "-1": {-1: 1.0}, "lin": {1: 1 / math.sqrt(2), -1: 1 / math.sqrt(2)}}
NR, NZ = 320, 200          # the radial table
AM_HALF_LAMS = 10.0        # the angular-momentum window's half width (in lambda) when the spectrum is cut at q = k
AM_HALF_LAMS_SPP = 25.0    # the same behind a spiral plate (its spectrum falls only as q^-2 up to the cut)
VOL = (56, 56, 56)         # the volume sent to the scene (nz, nx, ny)
HELIX_NZ_PER_LAM = 10      # z samples of the equiphase sheets per wavelength
HELIX_MAX_LAMS = 36.0      # at most this many wavelengths of z carry sheets (the region around the waist)
HELIX_NR = 12
HELIX_NPHI = 192
SAMPLES_PER_TURN = 64      # detector samples per turn of the rotating element
WINDOW = 128               # samples of one measurement (two turns)
# the propagating vector beam leaves out the source's evanescent part (q > k): a world is labelled when it drops more
# than DROP_LABEL of the named source's power (its field on z = 0 then differs from the named source by more than
# sqrt(1e-4) = 1 % in L2 norm); an LG world is refused above DROP_REFUSE (32 % in L2 norm: the name no longer describes
# the beam)
DROP_LABEL, DROP_REFUSE = 1e-4, 0.1
# the cost guard (review B8-beams, O5): the radial table's Bessel evaluations and its largest dense matrix, sized before
# anything is built. BESSEL_RATE: scipy.special.jv measured in the project image on this host's CPU, 2.8-3.8 M/s for
# orders 0-8 (single thread); the budget keeps a world's build to about 20 s there.
BESSEL_RATE = 3.0e6
BESSEL_BUDGET = 6.0e7
MATRIX_BUDGET = 0.5e9      # bytes of the largest dense matrix


def pol_vector(pol: str) -> np.ndarray:
    """The unit polarisation vector of the paraxial beam: e_+1, e_-1 or x^ (linear)."""
    return {"+1": np.array([1, 1j, 0]) / math.sqrt(2), "-1": np.array([1, -1j, 0]) / math.sqrt(2),
            "lin": np.array([1.0, 0.0, 0.0], complex)}[pol]


def detector_radius(beam, z_d: float) -> float:
    """The radius the disc's detector samples (its polar quadrature) at the element's plane z_d."""
    return 2.6 * beam.width(z_d) * math.sqrt(max(abs(beam.l), 1) / 2 + beam.p + 1)


def prism_half(beam, z_d: float) -> float:
    """Half the side of the square the Dove prism's detector samples at z_d (its corners lie at sqrt(2) times it)."""
    return 2.2 * beam.width(z_d) * math.sqrt(max(abs(beam.l), 1) / 2 + beam.p + 1)


class Beam:
    """The beam of a world: ``gen`` "mode" (LG_{p,l} with its waist w0 at z = 0) or "spp" (a Gaussian of waist w0
    behind a spiral phase plate at z = 0); ``model`` "exact" (the vector beam of helicities ``pol`` with the same
    spectrum: an exact Maxwell field, propagating waves only) or "paraxial" (LG closed form, or the Fresnel integral,
    times a uniform polarisation). For the exact model ``kept`` is the share of the named source's power the beam
    carries (``VortexBeam.propagating_fraction``); an LG world that keeps less than 1 - DROP_REFUSE is refused (behind
    a plate the dropped part is the plate's evanescent near field: stated, ``ev_near``), and so is a world whose table
    would exceed the cost budget (``cost``)."""

    def __init__(self, gen, model, l, p, w0, lam, pol, zspan):
        self.gen, self.model, self.l, self.p, self.w0, self.lam, self.pol = gen, model, int(l), int(p), w0, lam, pol
        self.k = 2 * math.pi / lam
        self.zr = PX.rayleigh(self.k, w0)
        if gen == "mode":
            self.z0, self.z1 = -zspan * self.zr, zspan * self.zr
            self.fn, self.qmax = B.lg_waist_spectrum(self.p, self.l, w0)
        else:
            self.z0, self.z1 = 0.0, 2 * zspan * self.zr
            self.fn, self.qmax = B.gaussian_vortex_spectrum(self.l, w0)
        self.amp = POLS[pol]
        zmax = max(abs(self.z0), abs(self.z1))
        self.wmax = float(PX.params(zmax, self.k, w0)[0])
        self.half = self.wmax * (2.2 + 0.75 * math.sqrt(2 * self.p + abs(self.l) + 1))
        # a spectrum cut at q = k while not negligible there (tight focusing, the plate's singular centre) has tails
        # falling only as r^-3/2: the angular momentum is measured over a wider window (and the table reaches it)
        qs = np.linspace(0.0, min(self.k, self.qmax), 2001)
        a = np.abs(np.asarray(self.fn(qs), complex))
        self.edge = float(a[-1] / max(float(a.max()), 1e-300)) if self.qmax >= self.k else 0.0
        # (25 lambda behind a spiral plate, whose q^-2 spectrum is cut at k: the default plate world then misses
        # 7e-4 of the energy instead of 1.3e-3, and its comparisons are checks; review B8-beams, O6)
        self.am_half = self.half if (model != "exact" or self.edge < 1e-6) else max(
            self.half, (AM_HALF_LAMS_SPP if gen == "spp" else AM_HALF_LAMS) * lam)
        # the table reaches every point a consumer samples (review B8-beams, O14): the volume's and the slices' corners
        # (sqrt2 half), the angular-momentum plane's corners, the disc's quadrature and the prism's square at the
        # widest plane the element can sit on (z1)
        self.r_need = max(math.sqrt(2) * self.half, math.sqrt(2) * self.am_half, detector_radius(self, self.z1),
                          math.sqrt(2) * prism_half(self, self.z1))
        r_far = 1.02 * self.r_need
        self.r = np.linspace(0.0, r_far, max(NR, int(math.ceil(r_far / (lam / 16)))))
        self.z = np.linspace(self.z0, self.z1, NZ)
        self.e_pol = pol_vector(pol)
        self.kept, self.dropped, self.ev_near = 1.0, 0.0, {}
        if model == "exact":
            self.vb = B.VortexBeam(self.l, self.k, self.fn, self.qmax, self.amp, max_elements=MATRIX_BUDGET / 8)
            self.kept = float(self.vb.propagating_fraction()[0])
            self.dropped = max(0.0, 1.0 - self.kept)
            # an LG waist sits in the middle of the region: what the beam drops is missing from the named mode at every
            # depth, so too much of it refuses the world. Behind a plate the dropped part is the plate's evanescent
            # near field, real but decaying with the distance from it: the beam is the plate's exact far field, and
            # the run states how much is missing near the plate (evanescent_fraction at lambda and 2 lambda)
            self.ev_near = ({1: self.vb.evanescent_fraction(lam), 2: self.vb.evanescent_fraction(2 * lam)}
                            if gen == "spp" else {})
            if gen == "spp":  # the incident Gaussian itself must be a beam: its own share beyond k (no plate)
                g0, gq = B.gaussian_vortex_spectrum(0, w0)
                inc = 1.0 - B.VortexBeam(0, self.k, g0, gq).propagating_fraction()[0]
                if inc > DROP_REFUSE:
                    raise Refusal(
                        T("the incident Gaussian beam with w0 = {w0:.3g} µm at λ = {lam:.3g} µm is not a beam: "
                          "{p:.3g} % of its power at z = 0 is in evanescent waves (q > k; the limit is {lim:.3g} %)",
                          w0=w0, lam=lam, p=100 * inc, lim=100 * DROP_REFUSE),
                        hint=T("increase w0 or decrease λ"))
            if gen == "mode" and self.dropped > DROP_REFUSE:
                raise Refusal(
                    T("the exact model cannot represent this source: {p:.3g} % of the power of the LG waist (w0 = "
                      "{w0:.3g} µm at λ = {lam:.3g} µm) is at q > k; these are evanescent waves, which a propagating "
                      "beam does not have (the limit is {lim:.3g} %)", p=100 * self.dropped, w0=w0, lam=lam,
                      lim=100 * DROP_REFUSE),
                    hint=T("increase w0 or decrease λ, or choose the paraxial model (marked as an approximation)"))
        self.cost = self._cost()
        if self.cost["bessel"] > BESSEL_BUDGET or self.cost["bytes"] > MATRIX_BUDGET:
            raise Refusal(
                T("the world is too expensive: a field table of {nr:d} radii × {nq:d} quadrature nodes, ~{nb:.3g} "
                  "million evaluations of Bessel functions (~{sec:.3g} s; the limit ~{lim_s:.3g} s), and a matrix of "
                  "~{gb:.2g} GB (the limit {lim_gb:.2g} GB)", nr=len(self.r), nq=int(self.cost["nq"]),
                  nb=self.cost["bessel"] / 1e6, sec=self.cost["seconds"], lim_s=BESSEL_BUDGET / BESSEL_RATE,
                  gb=self.cost["bytes"] / 1e9, lim_gb=MATRIX_BUDGET / 1e9),
                hint=T("decrease the length of the region, w0 or |l|, or increase λ"))
        if model == "exact":
            tables, self.table_err = {}, 0.0
            for s in self.amp:
                tab, e = self.vb.table(self.r, self.z, s, estimate=True)
                tables[s] = tab
                self.table_err = max(self.table_err, e)
        else:
            self.vb = None
            if gen == "mode":
                Z, R = np.meshgrid(self.z, self.r, indexing="ij")
                F0 = PX.lg(self.p, self.l, R, 0 * R, Z, self.k, w0) * np.exp(1j * self.k * Z)
            else:  # the Fresnel integral of the plate's spectrum, propagating part (q <= k)
                F0 = PX.fresnel_table(self.fn, self.l, self.k, self.r, self.z, self.k) * np.exp(1j * self.k * self.z)[:, None]
            # the paraxial beam is u e_pol: as helicity components with the polarisation's weights, F2 = F1 = 0
            tables = {s: np.stack([F0, 0 * F0, 0 * F0]) for s in self.amp}
            self.table_err = 0.0
        self.table = B.RadialTable(self.r, self.z, self.k, self.l, tables, self.amp)
        # the peak of |E|^2 (for normalisations): on the table's grid at r of the ring
        Ein = self.fields(self.r[None, :] * np.ones((5, 1)), 0 * self.r[None, :],
                          np.linspace(self.z0, self.z1, 5)[:, None] * np.ones((1, len(self.r))))[0]
        self.peak = float(np.max(np.sum(np.abs(Ein) ** 2, axis=0)))

    def _cost(self) -> dict:
        """The table's cost before it is built: Bessel evaluations (all helicities), the largest dense matrix in
        bytes, the quadrature nodes, and the time at BESSEL_RATE."""
        nr, nz = len(self.r), len(self.z)
        zmax = max(abs(self.z0), abs(self.z1))
        if self.model == "exact":
            c = self.vb.table_cost(nr, float(self.r[-1]), zmax, nz)
            out = {"nq": c["nq"], "bessel": c["bessel"] * len(self.amp), "bytes": c["bytes"]}
        elif self.gen == "spp":
            nq = PX.fresnel_table_nodes(self.l, self.k, float(self.r[-1]), zmax, self.k)
            out = {"nq": nq, "bessel": nr * nq, "bytes": 8 * nr * nq + 16 * nz * nq}
        else:
            out = {"nq": 0, "bessel": 0, "bytes": 16 * nr * nz}
        out["seconds"] = out["bessel"] / BESSEL_RATE
        return out

    # --- the field -------------------------------------------------------------------------------------------------
    def fields(self, x, y, z):
        """(E, H) from the table (fast, everywhere in the region)."""
        return self.table.fields(x, y, z)

    def direct(self, x, y, z):
        """E by the direct route (the engine's quadrature or closed form), for the checks."""
        x, y, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float))
        if self.model == "exact":
            return self.vb.fields(x, y, z)[0]
        if self.gen == "mode":
            u = PX.lg(self.p, self.l, x, y, z, self.k, self.w0) * np.exp(1j * self.k * z)
        else:
            u = np.empty(x.shape, complex)
            for zz in np.unique(z):
                m = z == zz
                u[m] = (PX.fresnel_vortex(self.fn, self.l, self.k, np.hypot(x[m], y[m]), float(zz), self.k)[0]
                        * np.exp(1j * (self.l * np.arctan2(y[m], x[m]) + self.k * zz)))
        return u[None] * self.e_pol.reshape((3,) + (1,) * u.ndim)

    def psi(self, x, y, z, E=None):
        """The scalar field shown as "the phase": the component along the input polarisation, e_pol* . E."""
        if E is None:
            E = self.fields(x, y, z)[0]
        return np.einsum("i,i...->...", np.conj(self.e_pol), E)

    def intensity(self, x, y, z):
        E = self.fields(x, y, z)[0]
        return np.sum(np.abs(E) ** 2, axis=0)

    def width(self, z):
        return float(PX.params(z, self.k, self.w0)[0])


# --- sampling for the scene ------------------------------------------------------------------------------------------
def volume(beam: Beam, z_end: float):
    """|E|^2 / peak on (nz, nx, ny) over the box (z from z0 to z1); zero beyond z_end (behind the rotating element
    the light is not computed), float32."""
    nz, nx, ny = VOL
    z = np.linspace(beam.z0, beam.z1, nz)
    x = np.linspace(-beam.half, beam.half, nx)
    Z, X, Y = np.meshgrid(z, x, x, indexing="ij")
    I = beam.intensity(X, Y, Z)
    I[Z > z_end] = 0.0
    return (I / max(float(I.max()), 1e-300)).astype(np.float32)


def helix_region(beam: Beam, z_end: float):
    """The z range that carries the equiphase sheets: all of it, or HELIX_MAX_LAMS wavelengths around the waist."""
    L = min(z_end - beam.z0, HELIX_MAX_LAMS * beam.lam)
    zc = 0.0 if beam.gen == "mode" else beam.z0 + 0.5 * L
    a = max(beam.z0, zc - 0.5 * L)
    return a, min(z_end, a + L)


def helix_grid(beam: Beam, z_end: float):
    """psi on the cylinder grid (z, r, phi) used by the sheets, and its axes."""
    a, b = helix_region(beam, z_end)
    nz = int(max(16, min(420, HELIX_NZ_PER_LAM * (b - a) / beam.lam)))
    z = np.linspace(a, b, nz)
    w = np.array([beam.width(zz) for zz in z])
    rho = np.linspace(0.25, 1.35, HELIX_NR) * math.sqrt(max(abs(beam.l), 1) / 2 + beam.p + 0.5)
    phi = np.linspace(0, 2 * math.pi, HELIX_NPHI, endpoint=False)
    # radii follow the beam's width: r = rho w(z) (a curvilinear grid; coords map it back)
    R = rho[None, :, None] * w[:, None, None] * np.ones((1, 1, HELIX_NPHI))
    P = np.broadcast_to(phi, R.shape)
    Z = np.broadcast_to(z[:, None, None], R.shape)
    E = beam.fields(R * np.cos(P), R * np.sin(P), Z)[0]
    return beam.psi(None, None, None, E), np.sum(np.abs(E) ** 2, axis=0), z, rho, w, phi


def helix_mesh(beam: Beam, grid, omega_t: float):
    """The sheets arg(psi e^{-i omega t}) = 0 at the display phase omega t (lfphys isophase_sheets), as (pos float32
    n x 3, idx uint32, rgb uint8 n x 3: brightness by |E|^2 there)."""
    psi, I, z, rho, w, phi = grid
    dphi = float(phi[1] - phi[0])

    def coords(iz, ir, s):
        ang = phi[0] + s * dphi
        rr = rho[ir] * w[iz]
        return np.stack([rr * np.cos(ang), rr * np.sin(ang), z[iz]], axis=-1)
    pos, tri = B.isophase_sheets(psi * np.exp(-1j * omega_t), coords, periodic=True,
                                 min_amp=1e-4 * float(np.max(np.abs(psi))))
    if len(pos):
        iz = np.clip(np.searchsorted(z, pos[:, 2]), 0, len(z) - 1)
        r = np.hypot(pos[:, 0], pos[:, 1])
        ir = np.clip(np.rint(np.interp(r / w[iz], rho, np.arange(len(rho)))).astype(int), 0, len(rho) - 1)
        b = np.sqrt(np.clip(I[iz, ir, 0] / max(float(I.max()), 1e-300), 0, 1))
        rgb = np.stack([60 + 195 * b, 110 + 120 * b, 255 - 120 * b], axis=1)
    else:
        rgb = np.zeros((0, 3))
    return pos.astype(np.float32), tri.astype(np.uint32).ravel(), np.clip(rgb, 0, 255).astype(np.uint8)


def sheet_count(grid) -> float:
    """The mean number of crossings of arg psi = 0 per (z, r) cell where the field is bright: |l| for a vortex."""
    psi, I, *_ = grid
    hits = np.sum(B.phase_crossings(psi)[0], axis=2)
    bright = I[:, :, 0] > 0.05 * I.max()
    return float(np.mean(hits[bright])) if np.any(bright) else 0.0


def poynting_current(beam: Beam):
    def j(x, y, z):
        E, H = beam.fields(x, y, z)
        return B.poynting(E, H)
    return j


def orbital_current(beam: Beam, h: float):
    """The canonical (orbital) momentum density p_o (lfphys.core.optics.beams.orbital_momentum) with gradients by
    fourth-order differences of the table's fields (step h)."""
    def j(x, y, z):
        x, y, z = (np.asarray(a, float) for a in (x, y, z))
        E, H = beam.fields(x, y, z)
        gE = np.zeros((3, 3) + x.shape, complex)
        gH = np.zeros_like(gE)
        for d in range(3):
            def at(s):
                q = [x, y, z]
                q[d] = q[d] + s * h
                return beam.fields(*q)
            a2, a1, m1, m2 = at(2), at(1), at(-1), at(-2)
            gE[:, d] = (-a2[0] + 8 * a1[0] - 8 * m1[0] + m2[0]) / (12 * h)
            gH[:, d] = (-a2[1] + 8 * a1[1] - 8 * m1[1] + m2[1]) / (12 * h)
        return B.orbital_momentum(E, H, gE, gH, beam.k)
    return j


def ring_radius(beam: Beam, z: float) -> float:
    """The radius of the brightest ring of |E|^2 at depth z (on the table's radial grid)."""
    r = beam.r[beam.r < beam.half]
    I = beam.intensity(r, 0 * r, np.full_like(r, z))
    return float(r[int(np.argmax(I))])


def flow_starts(beam: Beam, n_ring: int = 8):
    """Start points on the first plane: a ring at the intensity maximum of the first plane's radial profile."""
    r = beam.r[beam.r < beam.half]
    I = beam.intensity(r, 0 * r, np.full_like(r, beam.z0 if beam.gen == "mode" else beam.z0 + 0.02 * (beam.z1 - beam.z0)))
    r_pk = float(r[int(np.argmax(I))]) or 0.3 * beam.w0
    a = 2 * math.pi * (np.arange(n_ring) + 0.5) / n_ring
    zs = beam.z0 if beam.gen == "mode" else beam.z0 + 0.02 * (beam.z1 - beam.z0)
    starts = [np.stack([rr * np.cos(a), rr * np.sin(a), np.full(n_ring, zs)], axis=1) for rr in (0.75 * r_pk, 1.2 * r_pk)]
    return np.concatenate(starts), r_pk


def lines_message(lines, colour):
    """Polylines (n, m, 3) joined with NaN separators and a colour per point (0..1 floats for ``lines``)."""
    n, m, _ = lines.shape
    pts = np.full((n * (m + 1), 3), np.nan, np.float32)
    rgb = np.zeros((n * (m + 1), 3), np.float32)
    for i in range(n):
        pts[i * (m + 1):i * (m + 1) + m] = lines[i]
        rgb[i * (m + 1):i * (m + 1) + m] = colour
    return pts, rgb


# --- the apparatus' own drawings (geometry of devices, not consequences) ------------------------------------------
def disc_mesh(radius: float, thickness: float, n: int = 96, rgb_fn=None):
    """A flat disc (two faces) centred on the origin in the plane z = 0: (pos, idx, rgb); ``rgb_fn(x, y)`` colours it."""
    a = 2 * math.pi * np.arange(n) / n
    rings = np.linspace(0, radius, 13)
    pts = [[0.0, 0.0, 0.0]] + [[rr * math.cos(t), rr * math.sin(t), 0.0] for rr in rings[1:] for t in a]
    pts = np.array(pts)
    tris = []
    for j in range(n):
        tris.append((0, 1 + j, 1 + (j + 1) % n))
    for i in range(len(rings) - 2):
        b0, b1 = 1 + i * n, 1 + (i + 1) * n
        for j in range(n):
            j1 = (j + 1) % n
            tris += [(b0 + j, b1 + j, b1 + j1), (b0 + j, b1 + j1, b0 + j1)]
    front = pts + np.array([0, 0, -thickness / 2])
    back = pts + np.array([0, 0, thickness / 2])
    pos = np.concatenate([front, back])
    idx = np.concatenate([np.array(tris), np.array(tris) + len(pts)])
    if rgb_fn is None:
        rgb = np.full((len(pos), 3), 170)
    else:
        rgb = np.concatenate([rgb_fn(front[:, 0], front[:, 1])] * 2)
    return pos.astype(np.float32), idx.astype(np.uint32).ravel(), np.asarray(rgb, np.uint8)


def prism_mesh(length: float, height: float, width: float):
    """A Dove prism (a trapezoid prism, its long axis along z) centred on the origin, its base face normal to y: the
    reflection off the base mirrors y -> -y, the mirror line of the engine's image rotator at angle 0 (the x axis,
    ``beams_rotation.image_rotator``; review B8-beams, O13). (pos, idx, rgb)."""
    L, h, wd = length, height, width
    top = 0.45 * L
    prof = np.array([[-L / 2, -h / 2], [L / 2, -h / 2], [top / 2, h / 2], [-top / 2, h / 2]])  # (z, y) profile
    pts = []
    for x in (-wd / 2, wd / 2):
        for zz, yy in prof:
            pts.append([x, yy, zz])
    pts = np.array(pts)
    quads = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    # (x, y) swapped against a profile in (z, x): the winding is reversed so that the faces still face outwards
    tris = [t for a, b, c, d in quads for t in ((a, c, b), (a, d, c))]
    rgb = np.tile([[120, 190, 230]], (len(pts), 1))
    return pts.astype(np.float32), np.array(tris, np.uint32).ravel(), rgb.astype(np.uint8)


def spp_mesh(l: int, lam: float, radius: float, n_index: float = 1.5, exaggerate: float = 1.0, n: int = 96):
    """The spiral phase plate's top surface h(phi) (lfphys beams_thin_masks.spp_thickness), exaggerated for drawing,
    over a disc, centred on z = 0: (pos, idx, rgb)."""
    a = 2 * math.pi * (np.arange(n) + 0.5) / n
    rings = np.linspace(0.02 * radius, radius, 8)
    h = TM.spp_thickness(a, l, lam, n_index) * exaggerate
    pts = np.array([[rr * math.cos(t), rr * math.sin(t), -hh] for rr in rings for t, hh in zip(a, h)])
    tris = []
    for i in range(len(rings) - 1):
        for j in range(n - 1):
            b0, b1 = i * n, (i + 1) * n
            tris += [(b0 + j, b1 + j, b1 + j + 1), (b0 + j, b1 + j + 1, b0 + j + 1)]
    hn = h / max(float(h.max()), 1e-300)
    rgb = np.stack([np.tile(80 + 150 * hn, len(rings)), np.tile(140 + 60 * hn, len(rings)),
                    np.full(len(pts), 220)], axis=1)
    return pts.astype(np.float32), np.array(tris, np.uint32).ravel(), rgb.astype(np.uint8)


def surface_rgb(surface: TM.SpinningSurface):
    def fn(x, y):
        ph = surface.phase(x, y)
        v = 0.5 + 0.5 * np.tanh(ph / 1.5)
        return np.stack([90 + 120 * v, 80 + 90 * v, 70 + 40 * v], axis=1)
    return fn


def rot_z(angle: float) -> list:
    c, s = math.cos(angle), math.sin(angle)
    return [c, -s, 0.0, s, c, 0.0, 0.0, 0.0, 1.0]


# --- the detector --------------------------------------------------------------------------------------------------------
class SpinningDisc:
    """Lavery et al.'s mode filter over the engine: the beam's component psi at the disc's plane z_d scattered by a
    spinning rough surface; detected through a mode filter of the +l and -l superposition (the ``on_axis_amplitude``
    of conj(D) psi rho, D = (e^{i l phi} + e^{-i l phi}) g(r) / sqrt2 with g the incident ring's amplitude): the +l part
    is unshifted, the -l part (the surface's harmonic -2l) shifted by -2l Omega, the intensity beats at 2|l| Omega;
    and the on-axis (q = 0) amplitude, shifted by -l Omega."""

    def __init__(self, beam: Beam, z_d: float, seed: int):
        self.z_d = z_d
        r_max = detector_radius(beam, z_d)
        self.x, self.y, self.w = TM.polar_grid(r_max, 32, 192)
        self.surface = TM.SpinningSurface(seed, n=60, radius=0.8 * r_max, height=1.5,
                                           size=0.18 * r_max)
        psi = beam.psi(self.x, self.y, np.full_like(self.x, z_d))
        g = np.abs(psi)
        ph = np.arctan2(self.y, self.x)
        D = g * (np.exp(1j * beam.l * ph) + np.exp(-1j * beam.l * ph)) / math.sqrt(2) if beam.l else g
        self.UD = np.conj(D) * psi
        self.U0 = psi
        self.r_max = r_max

    def sample(self, angle: float):
        """(intensity through the mode filter, complex on-axis amplitude) at the surface's turn ``angle``."""
        a = TM.on_axis_amplitude(self.UD, self.x, self.y, self.w, self.surface, angle)
        b = TM.on_axis_amplitude(self.U0, self.x, self.y, self.w, self.surface, angle)
        return abs(a) ** 2, b


class DovePrism:
    """Two arms of a Mach-Zehnder interferometer, each with a Dove prism (one turning at Omega_p, one at rest): the
    power on a detector of the two arms' sum, psi_ref + psi_turned (the scalar image rotator: polarisation untouched,
    as in Courtial et al. 1998, PRL 80)."""

    def __init__(self, beam: Beam, z_d: float, n: int = 40):
        self.z_d = z_d
        h = prism_half(beam, z_d)
        xs = np.linspace(-h, h, n)
        X, Y = np.meshgrid(xs, xs, indexing="ij")
        self.X, self.Y = X, Y
        self.dA = float((xs[1] - xs[0]) ** 2)
        fn = lambda x, y, z: beam.psi(x, y, z)  # noqa: E731
        self.fn = fn
        self.ref = ROT.image_rotator(fn, 0.0, vector=False)(X, Y, np.full_like(X, z_d))

    def sample(self, angle: float):
        out = ROT.image_rotator(self.fn, angle, vector=False)(self.X, self.Y, np.full_like(self.X, self.z_d))
        return float(np.sum(np.abs(self.ref + out) ** 2) * self.dA), complex(np.sum(np.conj(self.ref) * out) * self.dA)


# --- the fork hologram (FFT route) ----------------------------------------------------------------------------------------
FORK_N = 512  # the fork's transverse grid (points per axis)


class Fork:
    """A Gaussian of waist w0 on a fork hologram of charge l and period Lambda at z = 0 (a thin mask,
    ``lfphys.theories.approx.beams_thin_masks``; the binary mask as its Fourier series up to the grid's band, the
    fork's centre sampled by the mask's mean), propagated by the angular spectrum: the volume, the transverse and
    axis-aligned longitudinal slices, the orders' charges and their shares of the power."""

    def __init__(self, l, w0, lam, period, kind, z_end, n=FORK_N):
        self.l, self.w0, self.lam, self.period, self.kind = int(l), w0, lam, period, kind
        self.k = 2 * math.pi / lam
        self.z0, self.z1 = 0.0, z_end
        x1 = abs(TM.order_position(1, period, self.k, z_end))
        w_end = float(PX.params(z_end, self.k, w0)[0])
        self.half = max(x1 + 3.2 * w_end, 3.5 * w0)
        self.n = n
        self.dx = 2 * self.half / n
        if self.dx > lam / 2:
            raise Refusal(T("a grid of {n:d} points over {w:.3g} µm is coarser than λ/2", n=n, w=2 * self.half),
                          hint=T("decrease z or increase the period"))
        self.x = (np.arange(n) - n // 2) * self.dx
        X, Y = np.meshgrid(self.x, self.x, indexing="ij")
        self.m_band = TM.fork_band(self.dx, period)
        self.U0 = np.exp(-(X * X + Y * Y) / w0 ** 2) * TM.fork_hologram(X, Y, self.l, period, kind, m_max=self.m_band)
        self.pad = 2

    def plane(self, z):
        return AS.propagate_field(self.U0, self.dx, self.k, z, pad=self.pad, check=True)

    def volume(self):
        nz, nx, ny = VOL
        z = np.linspace(self.z0, self.z1, nz)
        V = np.abs(AS.propagate_field(self.U0, self.dx, self.k, z, pad=self.pad)) ** 2
        ix = np.rint(np.linspace(0, self.n - 1, nx)).astype(int)
        V = V[:, ix][:, :, ix]
        return (V / max(float(V.max()), 1e-300)).astype(np.float32)

    def orders(self, z):
        """For orders m = -1, 0, 1: (position, charge measured in a disc of radius 1.3 w(z)). The disc stays where its
        order is bright: farther out, light the sharp hologram scatters to wide angles interferes with the order's
        tail and makes vortex pairs, one of which may fall inside a wider disc."""
        U = self.plane(z)
        w_z = float(PX.params(z, self.k, self.w0)[0])
        out = []
        for m in (-1, 0, 1):
            xm = TM.order_position(m, self.period, self.k, z)
            q = B.charge_in_disc(U, self.x, self.x, xm, 0.0, 1.3 * w_z)
            out.append((m, xm, q))
        return out, U

    def shares(self):
        """Each propagating order's share of the propagating power (review B8-beams, O8): measured in the angular
        spectrum of the run's field behind the mask (the same on every plane z: Parseval), against the thin mask's
        closed form on the same k grid (the orders' overlapping q^-2 tails included); the tolerance is twice the
        grid's aliasing, estimated by the closed form with the grid's periodic images; ``ideal`` is |c_m|^2 / sum over
        the propagating orders (no overlap)."""
        ideal = TM.order_power_reference(self.kind, self.period, self.k)
        orders = sorted(ideal)
        mm = self.m_band if self.kind == "binary" else 1
        meas = TM.order_powers(self.U0, self.dx, self.k, self.period, orders)
        cf = TM.order_powers_closed_form(self.kind, self.l, self.w0, self.period, self.k, self.dx, self.n, orders, mm)
        ci = TM.order_powers_closed_form(self.kind, self.l, self.w0, self.period, self.k, self.dx, self.n, orders, mm,
                                         images=1)
        alias = max(abs(ci[m] - cf[m]) for m in orders)
        return {"orders": orders, "meas": meas, "ref": cf, "ideal": ideal, "alias": alias, "tol": 2 * alias + 1e-5}
