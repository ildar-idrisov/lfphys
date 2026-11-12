# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v17: light scattered by a sphere — the rainbow, its supernumerary bows, Alexander's dark band and the glory (a
wrapper over lfphys; plan P14.8, on P1).

One drop at one wavelength: the exact Mie series (lfphys.core.optics.mie) gives the phase function and the
polarisation at every angle, the scattered intensity as a polar surface around the drop for either incident
polarisation, and, for drops of a few wavelengths, the near field inside and around the drop on slice planes and in
the volume; the Debye series (core.optics.mie_debye) splits the same field into the light reflected by the surface
(p = 0), transmitted (p = 1) and reflected once or twice inside (p = 2, 3: the primary and secondary rainbows),
compared with Descartes' rays and Airy's theory (theories.approx.rainbow). A cloud of drops in sunlight: the size
average of the series (core.optics.mie_poly) wavelength after wavelength, each weighted by the Sun's spectrum (a black
body at the IAU's 5772 K, stated) and turned into a colour (tools.colour): the colour of the sky against the scattering
angle grows as the run's time adds the wavelengths, and the sky around the antisolar point is drawn from it.

World time: seconds of the run; one wavelength of white light is added every T_LAM seconds. Lengths in the 3-D scene
in units of the drop's radius a.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import data as D
from lfphys.core import geometry as G
from lfphys.core.optics import mie, mie_debye as DB, mie_poly as MP
from lfphys.i18n import T, join
from lfphys.theories.approx import rainbow as RB
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.planes3d import SlicePlanes
from lfviz.sim import Simulation as BaseSimulation

from .engine import drops as DR

T_LAM = 0.5                                   # world seconds per wavelength of white light
SKY_DEG = np.linspace(125.0, 180.0, 551)      # scattering angles of the sky window (0.1 deg)
SKY_TH = np.radians(SKY_DEG)
DISP_DEG = np.linspace(0.0, 180.0, 3601)      # the phase-function window (0.05 deg)
POLAR_DEG = np.linspace(0.0, 180.0, 91)       # the polar surface (2 deg bins)
X_NEAR = 45.0                                 # near fields only for drops of a few wavelengths (x <= 45)
MAX_NODES = 1600                              # size nodes per wavelength at most (beyond: coarser, flagged); the
                                              # rainbow preset at 380 nm needs 1589 with the +-4 sigma cut
N_QUAD = 3000                                 # the angular quadrature of the energy check up to N terms (~0.8 s)
AIR_SHIFT = (-0.054, 0.096)                   # deg: p = 2, 3 bows of water (10 C, 550 nm) in air against vacuum for
                                              # an illustrative n_air - 1 = 2.77e-4 (review B8-mie s11; not sourced)
MAX_PLANES = 3
DEFAULT_NORMALS = {1: (0.0, -1.0, 0.0), 2: (1.0, 0.0, 0.0), 3: (0.0, 0.0, 1.0)}
BOX = ((-2.5, -2.5, -2.5), (2.5, 2.5, 2.5))
NV = 40                                       # the near-field volume: NV^3 points
NS = 121                                      # a slice: NS x NS points
EPS = np.finfo(float).eps
M_MATCHED = 1e-3                              # |m - 1| below this: nearly index-matched, refused (P16)
STEP_BUDGET_S = 10.0                          # one wavelength of the sky at most ~this long (P16): beyond it the size
SKY_S_PER_UNIT = 1.4e-9                       # nodes get coarser (flagged); measured cost of MP.average per node x
                                              # term x angle on the CPU of 2026-11-05 (1.2-1.5 ns; a single node ~90 ns)


def _p(*a, **k):
    return Param(*a, **k)


WATER = {"index": ["water"]}
CUSTOM = {"index": ["custom"]}
G_DROPS, G_LIGHT = T("Drops"), T("Light")
SCHEMA = Schema([
    _p("radius_um", T("Drop radius ⟨r⟩, µm"), "float", 150.0, group=G_DROPS, min=0.05, max=1000.0, log=True,
       help=T("Rain drops are {r1}–{r2} mm, fog drops {f1}–{f2} µm, cloud drops {c1}–{c2} µm. The near field is "
              "computed for drops up to ~{rn} µm (x ≤ {xn} at every wavelength)", r1=0.1, r2=1, f1=5, f2=50, c1=2,
              c2=20, rn=2.7, xn=45)),
    _p("width", T("Spread of the sizes σ/⟨r⟩"), "float", 0.02, group=G_DROPS, min=0.0, max=0.3,
       help=T("A gamma distribution of the sizes with this relative spread; 0: all drops of one size")),
    _p("index", T("Substance of the drop"), "select", "water", group=G_DROPS,
       options=[("water", T("water: the index of IAPWS R9-97 (with dispersion)")),
                ("custom", T("a given index n + iκ (without dispersion)"))]),
    _p("t_c", T("Water temperature, °C"), "float", 10.0, group=G_DROPS, min=0.0, max=40.0, show_if=WATER),
    _p("n_re", T("n, the real part of the index"), "float", 1.5, group=G_DROPS, min=0.2, max=10.0, show_if=CUSTOM),
    _p("n_im", T("κ, the imaginary part (absorption, ≥ 0)"), "float", 0.0, group=G_DROPS, min=0.0, max=10.0,
       show_if=CUSTOM),
    _p("n_medium", T("Index of the medium around"), "float", 1.0, group=G_DROPS, min=1.0, max=1.6,
       help=T("1 is vacuum; the drop's index is taken relative to the medium")),
    _p("n_lam", T("Wavelengths of white light ({lo}–{hi} nm)", lo=380, hi=760), "select", 24, group=T("Computation"),
       options=[(8, "8"), (16, "16"), (24, "24"), (32, "32")]),
    _p("light", T("Light"), "select", "white", group=G_LIGHT, live=True,
       options=[("white", T("sunlight (white): a black body at {T} K", T=5772)), ("mono", T("one wavelength"))]),
    _p("lam_nm", T("Wavelength, nm"), "float", 550.0, group=G_LIGHT, live=True, min=380.0, max=760.0,
       help=T("For one drop (the phase function, the Debye series, the near field) and for the sky in the "
              "one-wavelength mode")),
], presets={
    "rainbow": {"label": T("Rainbow: drops of {r} mm ± {w} % in sunlight: the primary and secondary bows, Alexander's "
                           "band, the supernumerary bows", r=0.15, w=2), "params": {}},
    "supernumerary": {"label": T("Supernumerary bows: equal drops of {r} mm ± {w} %", r=0.1, w=0.5),
                      "params": {"radius_um": 100.0, "width": 0.005}},
    "big_drops": {"label": T("Large drops of {r} mm ± {w} %: the supernumerary bows are washed out (a heavy "
                             "computation, ~a minute)", r=0.3, w=10),
                  "params": {"radius_um": 300.0, "width": 0.10, "n_lam": 16}},
    "fogbow": {"label": T("Fogbow: drops of {r} µm ± {w} %, a wide white bow", r=15, w=15),
               "params": {"radius_um": 15.0, "width": 0.15}},
    "glory": {"label": T("Glory: cloud drops of {r} µm ± {w} %, coloured rings around the antisolar point", r=8, w=10),
              "params": {"radius_um": 8.0, "width": 0.10}},
    "near": {"label": T("Near field: a drop of {r} µm in light of {lam} nm, the focus inside and behind the drop", r=1,
                        lam=550),
             "params": {"radius_um": 1.0, "width": 0.0, "light": "mono", "n_lam": 8}},
    "absorbing": {"label": T("An absorbing sphere of {r} µm, n = {n} + {k}i: the inner rays die out, no rainbow", r=2,
                             n=1.6, k=0.05),
                  "params": {"radius_um": 2.0, "width": 0.05, "index": "custom", "n_re": 1.6, "n_im": 0.05}},
})


def _check_matched(p, lam_nm):
    """Review UX-params P16: a drop whose index equals the medium's (m = 1) scatters nothing; its checks divided by the
    zero scattering (NaN, the Debye route 1163 against 0). Nearly matched drops fail the series' checks too: the Debye
    route up to |m - 1| ~ 3e-5, the energy identity of large drops up to ~1e-4 (r = 150 µm), all pass from 3e-4
    (measured: response_checks_v-worlds/v17_m1.out, v17_m1b.out; the cause is open, STATUS). Such a drop is refused at
    the display wavelength, saying what to change. Cheap: also used by ``check_params``."""
    m = DR.index(p, lam_nm)
    if abs(m - 1.0) < M_MATCHED:
        n_drop = abs(m * float(p["n_medium"]))
        raise Refusal(T("the drop is almost indistinguishable from the medium at {lam} nm: its index {nd:.7g} against "
                        "the medium's index {nm} (m = {mr:.7g}{mi:+.2g}i, |m − 1| < {lim}); it scatters almost "
                        "nothing (the scattering ∝ |m − 1|²), and the series' checks (the Debye series, the energy) "
                        "do not hold their accuracy here", lam=float(lam_nm), nd=n_drop, nm=float(p["n_medium"]),
                        mr=float(m.real), mi=float(m.imag), lim=M_MATCHED),
                      hint=T("change the drop's index or “{medium}” so that |m − 1| ≥ {lim}, or choose another "
                             "wavelength", medium=SCHEMA.by_id["n_medium"].label, lim=M_MATCHED))


class Simulation(SlicePlanes, BaseSimulation):
    default_speed = 1.0
    speed_range = (0.05, 20.0)

    @classmethod
    def check_params(cls, params):
        """Cheap refusals before anything is built: an index-matched drop (P16)."""
        _check_matched(params, float(params["lam_nm"]))

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = p = dict(params)
        self._buf = []
        if p["index"] == "custom" and float(p["n_im"]) < 0:
            raise Refusal(T("κ ≥ 0 is required: an absorbing substance (the time factor exp(−iωt))"),
                          hint=T("set κ to zero or above"))
        self.r_um = float(p["radius_um"])
        self.width = float(p["width"])
        self.n_med = float(p["n_medium"])
        self.lams, self.lam_w = DR.wavelengths(int(p["n_lam"]))
        self.live = {k: p[k] for k in SCHEMA.live_ids()}
        self.x_max = float(mie.size_parameter(self.r_um, DR.LAM_MIN * 1e-3, self.n_med))
        self.near = self.x_max <= X_NEAR
        if float(mie.size_parameter(self.r_um * (1 + 3 * self.width), DR.LAM_MIN * 1e-3, self.n_med)) > 2e4:
            raise Refusal(T("the drops are too large: x > {xmax} at {lam} nm (the limit of the series' verified "
                            "accuracy)", xmax=2e4, lam=380),
                          hint=T("decrease the drop radius or the spread of the sizes"))
        self._ang = None   # the angular functions of the sky window (a cache, rebuilt after a checkpoint)
        self.seq = 0       # the set-up's number (a live change starts a new one)
        self.sky_seq = 0
        self.vol = None
        self._init_planes()
        self.box = BOX
        self.plane_center = (0.0, 0.0, 0.0)
        self.default_normals = DEFAULT_NORMALS
        self.plane_min_step = 0.05
        self._setup()
        if self.near:
            self._set_plane(1, self.plane_center, DEFAULT_NORMALS[1])

    def __getstate__(self):
        d = dict(self.__dict__)
        d["_ang"] = None  # recomputed on demand: identical (deterministic), and 10-20 MB smaller checkpoints
        return d

    # --- the set-up: one drop at the display wavelength, the cloud in the chosen light ------------------------------
    @property
    def lam_nm(self):
        return float(self.live["lam_nm"])

    def _setup(self):
        lam = self.lam_nm
        _check_matched(self.params, lam)  # before anything changes: a refused live change leaves the world as it was
        self.seq += 1
        self.m = DR.index(self.params, lam)
        self.x = float(mie.size_parameter(self.r_um, lam * 1e-3, self.n_med))
        self._mono()
        if self.near:
            self._volume()
            for pid in sorted(self.planes):
                pl = self.planes[pid]
                self._set_plane(pid, pl["origin"], pl["normal"], auto=pl["auto"], speed=pl["speed"])
        self._start_sky()

    def _mono(self):
        """The drop at the display wavelength: Mie on a fine angular grid (bin means for display), the Debye terms,
        ray optics and Airy, the polar surfaces, the checks."""
        m, x = self.m, self.x
        a, b = mie.coefficients(m, x)
        N = len(a)
        q = mie.efficiencies_from(a, b, x)
        self.coef = (a, b)
        n_fine = int(min(20001, max(3601, 180.0 * x / 4.0 + 1)))
        if n_fine <= 3601:
            S1, S2 = mie.amplitudes(a, b, np.radians(DISP_DEG))
            i1, i2 = np.abs(S1) ** 2, np.abs(S2) ** 2
            s11 = 0.5 * (i1 + i2)
            lo = hi = s11
            fine_deg, f1, f2 = DISP_DEG, i1, i2
        else:
            fine_deg = np.linspace(0.0, 180.0, n_fine)
            S1, S2 = mie.amplitudes(a, b, np.radians(fine_deg))
            f1, f2 = np.abs(S1) ** 2, np.abs(S2) ** 2
            edges = np.concatenate([[-1e-9], 0.5 * (DISP_DEG[1:] + DISP_DEG[:-1]), [180.0 + 1e-9]])
            i1, _, _ = DR.bin_mean(fine_deg, f1, edges)
            i2, _, _ = DR.bin_mean(fine_deg, f2, edges)
            s11 = 0.5 * (i1 + i2)
            _, lo, hi = DR.bin_mean(fine_deg, 0.5 * (f1 + f2), edges)
        # the phase function normalised to 4 pi over the sphere and the polarisation, from the bins' intensities by the
        # engine's formulas (review B8-mie, M12: they were recomputed here)
        pf = mie.phase_function_from_intensities(i1, i2, x, q["Qsca"])
        norm = 4.0 / (x * x * q["Qsca"])  # the same scale for the Debye terms, the envelope and Airy (pf = norm s11)
        P = mie.polarisation_from_intensities(i1, i2)
        # Debye terms p = 0..3 on the display grid
        dd = DB.amplitudes(m, x, np.radians(DISP_DEG), p_max=3)
        deb = [mie.phase_function_from_intensities(np.abs(dd["S1"][p]) ** 2, np.abs(dd["S2"][p]) ** 2, x, q["Qsca"])
               for p in range(4)]
        deb_P2 = mie.polarisation_from_intensities(np.abs(dd["S1"][2]) ** 2, np.abs(dd["S2"][2]) ** 2)
        self.debye_div = int(np.count_nonzero(dd["diverges_a"] | dd["diverges_b"]))
        self.debye_amp = float(dd["amplification"])
        # ray optics and Airy (approximations, for comparison) for a transparent drop
        mr = float(m.real)
        bows = {}
        airy = {}
        for p in (2, 3):
            try:
                d = RB.descartes(mr, p)
            except ValueError:
                continue
            am = RB.airy_maxima(mr, p, x, 3)
            bows[p] = {"theta": math.degrees(d["theta"]), "airy": [math.degrees(v) for v in am], "b": d["b"]}
            win = np.abs(DISP_DEG - math.degrees(d["theta"])) <= 25.0
            a2 = np.full(len(DISP_DEG), np.nan)
            th = np.radians(DISP_DEG[win])
            a2[win] = 0.5 * (RB.airy(mr, p, x, th, "s") + RB.airy(mr, p, x, th, "p")) * norm
            if float(m.imag) > 0:
                a2[:] = np.nan  # Airy's theory here is for a transparent drop
            airy[p] = a2
        self.bows = bows
        # the measured bow of the Debye term p = 2 (its maximum within 15 deg on the bright side of Descartes)
        meas = {}
        for p in bows:
            th0 = bows[p]["theta"]
            side = 1.0 if p == 2 else -1.0
            win = (side * (DISP_DEG - th0) >= -1.0) & (side * (DISP_DEG - th0) <= 15.0)
            if win.any() and np.isfinite(deb[p][win]).any():
                k = int(np.nanargmax(np.where(win, deb[p], -np.inf)))
                meas[p] = float(DISP_DEG[k])
        self.measured_bows = meas
        blobs = {"theta": DISP_DEG.astype(np.float32), "s11": pf.astype(np.float32),
                 "lo": (np.asarray(lo) * norm).astype(np.float32), "hi": (np.asarray(hi) * norm).astype(np.float32),
                 "pol": P.astype(np.float32), "pol_p2": deb_P2.astype(np.float32)}
        for p in range(4):
            blobs[f"deb{p}"] = deb[p].astype(np.float32)
        for p, a2 in airy.items():
            blobs[f"airy{p}"] = a2.astype(np.float32)
        self._msg({"type": "mono", "t": self.t, "seq": self.seq, "lam_nm": self.lam_nm, "x": x,
                   "m": [float(m.real), float(m.imag)], "n_terms": N, "n_fine": n_fine,
                   "Q": {k: float(q[k]) for k in ("Qext", "Qsca", "Qabs", "Qback", "Qpr", "g")},
                   "bows": {str(k): v for k, v in bows.items()}, "measured": {str(k): v for k, v in meas.items()},
                   "alexander": ([bows[3]["theta"], bows[2]["theta"]] if 2 in bows and 3 in bows else None),
                   "r_um": self.r_um, "debye": {"diverging_orders": self.debye_div, "amplification": self.debye_amp}},
                  blobs)
        if self.debye_div or self.debye_amp > 10.0:
            what = (T("the Debye series diverges at {n:d} orders (|R¹¹| > 1: this happens for a weakly absorbing drop "
                      "with m ≈ 1)", n=int(self.debye_div)) if self.debye_div else
                    T("the terms nearly cancel each other (this happens at m ≈ 1: diffraction against a passage with "
                      "almost no refraction)"))
            self._msg({"type": "notice", "t": self.t,
                       "text": T("The terms p = 0–3 of the Debye series of this drop are up to {amp:.2g} times larger "
                                 "than the full answer: {what}. The coloured curves are not paths of light but terms "
                                 "that cancel; their sum in closed form is right (the check “Debye series”).",
                                 amp=float(self.debye_amp), what=what)})
        # the polar surfaces (2-deg bin means of the fine grid)
        edges = np.concatenate([[-1e-9], 0.5 * (POLAR_DEG[1:] + POLAR_DEG[:-1]), [180.0 + 1e-9]])
        p1, _, _ = DR.bin_mean(fine_deg, f1, edges)
        p2, _, _ = DR.bin_mean(fine_deg, f2, edges)
        for mode, label, vis in (("u", T("Scattered light, unpolarised incident light (log scale, {n:d} decades)",
                                         n=5), True),
                                 ("x", T("Scattered light, the incident light polarised along x"), False),
                                 ("y", T("Scattered light, the incident light polarised along y"), False)):
            pos, idx, rgb = DR.polar_mesh(POLAR_DEG, p2, p1, mode)
            self._msg({"type": "mesh", "t": self.t, "id": f"polar_{mode}", "count": int(len(pos)), "opacity": 0.55,
                       "visible": vis, "label": label}, {"pos": pos, "idx": idx, "rgb": rgb})
        pts, col = DR.ray_fans(mr)
        self._msg({"type": "lines", "t": self.t, "id": "rays",
                   "label": join([T("Rays (geometric optics, m = {m:.4g}): grey, reflection p = 0; blue, passage "
                                    "p = 1; yellow, one internal reflection p = 2; violet, two, p = 3", m=float(mr)),
                                  T("bright: Descartes' rays") if bows else
                                  T("no Descartes' rays (a rainbow p = 2 only at 1 < m < 2)"),
                                  T("at m < 1 only the rays with b < m enter") if mr < 1.0 else ""])},
                  {"pts": pts.reshape(-1), "rgb": col.reshape(-1)})
        self._mono_checks(a, b, q, dd)

    def _mono_checks(self, a, b, q, dd):
        """The drop's checks. Which of them test the coefficients' values (review B8-mie, M3): only `debye` (a second
        route to the same coefficients) and `wiscombe` (the engine against published numbers, at fixed spheres);
        `theorem`, `energy` and `mueller` are identities of the series' structure, labelled as such: they test the
        angular functions, the quadrature and the arithmetic, and stay at round-off when D_n, psi_n or chi_n are
        wrong (tests/test_v17_mie_scattering.py shows what each one catches)."""
        x, m = self.x, self.m
        N = len(a)
        S1, S2 = mie.amplitudes(a, b, np.array([0.0]))
        G_SERIES = T("Drop: the exact series")
        self._check("theorem", T("Angular sum at θ = 0 against Q_ext (the optical theorem in the series' form)"),
                    q["Qext"], 4.0 / x ** 2 * float(S1[0].real), tol=100 * N * EPS, group=G_SERIES,
                    note=T("an identity of the series' form (πₙ(1) = τₙ(1) = n(n+1)/2): it holds for any coefficients "
                           "and tests the angular functions and the sum at θ = 0, not aₙ, bₙ; N = {N:d} terms, "
                           "tolerance: 100 N ε of round-off", N=N))
        if m.imag == 0 and N <= N_QUAD:
            r = mie.angular_integrals(a, b, x)
            self._check("energy", T("Energy: scattered over all angles against Q_ext (the drop does not absorb)"),
                        r["Qsca"], q["Qext"], tol=r["rel_bound"], group=G_SERIES,
                        note=T("∫(|S₁|² + |S₂|²) over the sphere by Fejér's quadrature (the second rule, {k:d} nodes, "
                               "exact for these polynomials) against Q_ext from the coefficients. At a real m this is "
                               "an identity of the series' form (every aₙ = A/(A − iB) with real A, B, Re aₙ = |aₙ|² "
                               "for any Dₙ, ψₙ, χₙ): it tests the angular functions, the sums and the quadrature, not "
                               "the coefficients. Tolerance: the derived bound of round-off "
                               "u(x²Q²_ext/(2Q_sca) + 8N + 16): the nodes are rounded cosines under the forward peak "
                               "of width ~1/x²", k=int(r["n_nodes"])))
        elif m.imag == 0:
            dev = max(float(np.max(np.abs(a.real - np.abs(a) ** 2))), float(np.max(np.abs(b.real - np.abs(b) ** 2))))
            tol = 16 * mie.U
            self._check("energy", T("Energy: Re aₙ = |aₙ|², Re bₙ = |bₙ|² (the drop does not absorb)"), dev, 0.0,
                        tol=tol, ok=dev <= tol, group=G_SERIES,
                        note=T("the largest deviation over {N:d} orders. An identity of the series' form: it holds for "
                               "any Dₙ, ψₙ, χₙ as long as the computation is real; it tests that no imaginary part got "
                               "into the coefficients, not their values. Tolerance 16u: the real part of the "
                               "denominator equals the numerator bit for bit, what remains is the round-off of the "
                               "complex division. The angular quadrature is used up to N = {nq:d}", N=N, nq=N_QUAD))
        c = DB.check_against_mie(m, x, c=dd)
        k = int(np.argmax(c["err"] / c["tol"]))
        self._check("debye", T("Debye series: the sum over all p against the Mie coefficients (a second route)"),
                    c["max_err"], 0.0, tol=float(c["tol"][k]), ok=c["ok"], group=G_SERIES,
                    note=T("(1 − R²² − T²¹T¹²/(1 − R¹¹))/2 from the ratios of the Hankel functions and the Wronskian "
                           "against aₙ, bₙ of the Mie series (Dₙ downwards, ψₙ by Miller, χₙ upwards), over all "
                           "{N:d} orders, as fractions of the largest coefficient: a test of the coefficients' values. "
                           "The tolerance per order u(1000N + 32x|daₙ/dx|/max|a|) (the conditioning at narrow "
                           "resonances; mie_debye.ACCURACY): from {lo:.1e} to {hi:.1e}; the largest ratio of the "
                           "deviation to the tolerance {w:.2g} (order {k:d})", N=int(c["N"]),
                           lo=float(c["tol"].min()), hi=float(c["tol"].max()), w=float(c["worst"]), k=k + 1))
        w = mie.wiscombe_self_test()
        self._check("wiscombe", T("The engine against Wiscombe's published values (1979, x = {x:d}, m = {m1} and "
                                  "{m1} − {k}i)", x=100, m1=1.5, k=0.1),
                    w["worst"], None, tol=1.0, ok=w["worst"] <= 1.0, group=G_SERIES,
                    note=T("{n:d} printed quantities (Q_ext, Q_sca, g, S₁(0), S₁(90°), S₂(90°), S₁(180°)): the largest "
                           "deviation in halves of the last printed digit (≤ 1: agrees); a test of the coefficients' "
                           "values against published numbers, for two spheres, not for this drop", n=int(w["n"])))
        r = mie.mueller(*mie.amplitudes(a, b, np.radians(DISP_DEG[::10])))
        dev = float(np.max(np.abs(r["S11"] ** 2 - r["S12"] ** 2 - r["S33"] ** 2 - r["S34"] ** 2) / r["S11"] ** 2))
        self._check("mueller", T("Mueller matrix: S11² = S12² + S33² + S34² (an identity)"), dev, 0.0, tol=1e-10,
                    ok=dev <= 1e-10, group=G_SERIES,
                    note=T("it holds for any complex S₁, S₂ (the matrix of one particle is pure): it tests only the "
                           "arithmetic of mie.mueller; the largest deviation over {n:d} angles, rel.", n=361))
        if self.params["index"] == "water":
            lam, n_tab = D.IAPWS97_RINDEX_CHECK_0C_01MPA[1]
            n_eng = float(D.water_index(lam * 1e3, 0.0))
            self._check("water", T("Index of water by IAPWS at {lam} nm and {tc} °C against the verification table "
                                   "(Table 3)", lam=589, tc=0), n_eng,
                        n_tab, tol=1e-6 / n_tab, ok=abs(n_eng - n_tab) <= 1e-6, group=T("Water"),
                        note=T("the density by IAPWS SR6-08; this world: n({lam} nm, {tc} °C) = {n:.6f}",
                               lam=self.lam_nm, tc=float(self.params["t_c"]), n=abs(self.m * self.n_med)))
        transparent = abs(m.imag) <= 1e-6 and x >= 50.0
        G_BOW = T("Rainbow")
        for p, label in ((2, T("Rainbow p = {p:d} (primary): the maximum of the Debye term against Airy's maximum", p=2)),
                         (3, T("Rainbow p = {p:d} (secondary): the maximum of the Debye term against Airy's maximum",
                               p=3))):
            if transparent and p in self.bows and p in self.measured_bows:
                bw = self.bows[p]
                d = self.measured_bows[p] - bw["airy"][0]
                self._check(f"bow{p}", label,
                            self.measured_bows[p], bw["airy"][0], "°", tol=None, info=True, group=G_BOW,
                            note=T("the maximum of |S^({p:d})|² by the Debye series (grid {step}°): {mb:.3f}°, the "
                                   "difference from Airy {d:+.3f}°; Descartes' angle {th:.3f}°, Airy's first maximum "
                                   "{ai:.3f}° (shifted by ~x^(−2/3) to the bright side); at x = {x:.4g} Airy's theory "
                                   "is an approximation", p=p, step=0.05, mb=self.measured_bows[p], d=d,
                                   th=bw["theta"], ai=bw["airy"][0], x=x))
        if abs(m.imag) <= 1e-6 and 2 in self.bows and 3 in self.bows:
            self._check("alexander", T("Alexander's band between the bows (scattering angles by Descartes)"),
                        self.bows[2]["theta"] - self.bows[3]["theta"], None, "°", tol=None, info=True, group=G_BOW,
                        note=T("secondary {s:.3f}°, primary {p:.3f}°: between them the rays p = 2 and 3 do not come "
                               "out", s=self.bows[3]["theta"], p=self.bows[2]["theta"]))

    # --- the near field -----------------------------------------------------------------------------------------------
    def _volume(self):
        g = np.linspace(BOX[0][0], BOX[1][0], NV)
        Z, X, Y = np.meshgrid(g, g, g, indexing="ij")
        pts = np.stack([X, Y, Z], -1)
        f = mie.near_field(self.m, self.x, pts)
        I = np.sum(np.abs(f["E"]) ** 2, -1)
        peak = float(I.max())
        self.vol_peak = peak
        self._msg({"type": "volume", "t": self.t, "id": "field", "dims": [NV, NV, NV],
                   "quantity": {"label": "|E|²/|E₀|²", "unit": "", "peak": peak},
                   "note": T("|E|² of the incident plus the scattered (outside) and the internal field, a grid of "
                             "{n:d}³", n=NV)},
                  {"data": (I / peak).astype(np.float32).reshape(-1)})
        # the boundary conditions on the drop's surface (24 points)
        k = np.arange(24)
        th = np.arccos(1 - 2 * (k + 0.5) / 24)
        ph = k * math.pi * (3 - math.sqrt(5))
        nrm = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)], -1)
        d = 1e-10
        fo, fi = mie.near_field(self.m, self.x, nrm * (1 + d)), mie.near_field(self.m, self.x, nrm * (1 - d))
        tE = fo["E"] - fi["E"]
        tE = tE - np.sum(tE * nrm, -1)[:, None] * nrm
        tH = fo["H"] - fi["H"]
        tH = tH - np.sum(tH * nrm, -1)[:, None] * nrm
        s = float(np.abs(fo["E"]).max())
        err = max(float(np.abs(tE).max()), float(np.abs(tH).max()) / abs(self.m)) / s
        tol = 20 * self.x * abs(self.m) ** 2 * d + 1e-11
        self._check("boundary", T("Near field: the tangential E and H are continuous on the drop's surface"), err, 0.0,
                    tol=tol, ok=err <= tol, group=T("Near field"),
                    note=T("{n:d} points of the surface, the field {d} a outside and inside; tolerance: the change of "
                           "the field over this gap (20 x |m|² · {d}) plus round-off. It tests the assembly of the "
                           "fields (the spherical harmonics, the internal cₙ, dₙ, Z·H) against aₙ, bₙ; Dₙ, ψₙ, χₙ "
                           "themselves enter both sides consistently: their values are tested by “Debye series”",
                           n=24, d=d))

    def _plane_slice(self, pid, pl, s_rng, t_rng, coarse):
        n = 61 if coarse else NS
        s = np.linspace(s_rng[0], s_rng[1], n)
        t = np.linspace(t_rng[0], t_rng[1], n)
        P = G.plane_points(pl, s, t)
        f = mie.near_field(self.m, self.x, P)
        E = f["E"]
        ver = {"points": 0, "note": T("a coarse slice while auto-moving, not verified")}
        if not coarse:
            ver = self._verify_plane(pl)
        return {"s": s, "t": t, "E": E, "verify": ver, "plane": pl, "coarse": coarse}

    def _verify_plane(self, pl):
        """Points of the plane on the drop's surface (the circle where the plane cuts the sphere): the tangential E
        just inside and outside agree (the slice's field is the engine's total field there)."""
        o = np.asarray(pl.origin, float)
        n = np.asarray(pl.normal, float)
        dist = float(o @ n)
        if abs(dist) >= 0.999:
            return {"points": 0, "note": T("the plane does not cut the drop: there is nothing to verify on the "
                                           "surface")}
        c = dist * n
        rr = math.sqrt(1 - dist * dist)
        u, v = np.asarray(pl.u, float), np.asarray(pl.v, float)
        ang = np.linspace(0, 2 * math.pi, 12, endpoint=False)
        pts = c + rr * (np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v)
        nr = pts / np.linalg.norm(pts, axis=-1, keepdims=True)
        d = 1e-10
        fo, fi = mie.near_field(self.m, self.x, nr * (1 + d)), mie.near_field(self.m, self.x, nr * (1 - d))
        t = fo["E"] - fi["E"]
        t = t - np.sum(t * nr, -1)[:, None] * nr
        err = float(np.abs(t).max()) / float(np.abs(fo["E"]).max())
        tol = 20 * self.x * abs(self.m) ** 2 * d + 1e-11
        return {"points": 12, "max_err": err, "tol": tol, "ok": err <= tol}

    def _plane_emit(self, pid):
        sl = self.slices[pid]
        pd = self.planes[pid]
        E = sl["E"]
        I = np.sum(np.abs(E) ** 2, -1)
        peak = float(np.nanmax(I))
        meta = {"type": "slice", "t": self.t, "id": pid, "shape": list(I.shape), "coarse": bool(sl["coarse"]),
                "s": [float(sl["s"][0]), float(sl["s"][-1]), len(sl["s"])],
                "tt": [float(sl["t"][0]), float(sl["t"][-1]), len(sl["t"])],
                "origin": pd["origin"], "u": pd["u"], "v": pd["v"], "normal": pd["normal"], "label": pd["label"],
                "peak": peak, "route": "mie", "route_label": T("the Mie series: the incident wave + the scattered "
                                                               "field outside, the internal field inside the drop; "
                                                               "the phase is arg Eₓ"),
                "exact": True, "approximation": False, "reason": "", "verify": sl["verify"],
                "verify_title": T("continuity of the tangential E on the circle where the slice cuts the drop"),
                "units": "a", "depth": False,
                "quantity": {"label": "|E|²/|E₀|²", "unit": "", "peak": peak}}
        blobs = {"I": (I / peak).astype(np.float32)}
        if not sl["coarse"]:
            blobs["phase"] = np.angle(E[..., 0]).astype(np.float32)
        self._msg(meta, blobs)
        ver = sl["verify"]
        if ver.get("points"):
            self._check(f"plane_{pid}", T("Slice {id}: the tangential E on the drop's surface is continuous", id=pid),
                        ver["max_err"], 0.0, tol=ver["tol"], ok=ver["ok"], group=T("Near field"),
                        note=T("{n:d} points of the circle where the slice cuts the drop, {d} a outside and inside",
                               n=12, d=1e-10))

    def _plane_removed(self, pid, sl):
        if sl and sl["verify"].get("points"):
            self._check(f"plane_{pid}", T("Slice {id}: removed", id=pid), None, None, info=True, group=T("Near field"),
                        note=T("the last verification of this slice is in the run's record"))

    # --- the cloud in sunlight ----------------------------------------------------------------------------------------
    def _sky_lams(self):
        if self.live["light"] == "mono":
            return np.array([self.lam_nm]), np.array([1.0])
        return self.lams, self.lam_w

    def _start_sky(self):
        self.sky_seq += 1
        self.sky_t0 = self.t
        self.sky_k = 0
        self.XYZ = np.zeros((len(SKY_DEG), 3))
        self.Ysum = np.zeros(len(SKY_DEG))
        self.Ypol = np.zeros(len(SKY_DEG))
        self.sky_err = 0.0
        self.sky_tail = 0.0
        self.sky_coarse_dx = 0.0
        lam, _ = self._sky_lams()
        self.sky_n = len(lam)
        self._msg({"type": "sky_start", "t": self.t, "seq": self.sky_seq, "n": self.sky_n,
                   "lams": [float(v) for v in lam], "mode": self.live["light"], "t_lam": T_LAM,
                   "deg": [float(SKY_DEG[0]), float(SKY_DEG[-1]), len(SKY_DEG)]})

    def _angular(self, N):
        if self._ang is None or self._ang[0].shape[0] < N:
            self._ang = mie.angular(np.cos(SKY_TH), N)
        return self._ang

    def _sky_step(self):
        lams, ws = self._sky_lams()
        k = self.sky_k
        lam = float(lams[k])
        m = DR.index(self.params, lam)
        nodes = MP.size_nodes(self.r_um, self.width, lam * 1e-3, self.n_med, max_nodes=self._max_nodes(lam))
        N = mie.n_terms(float(nodes["x"].max()))
        av = MP.average(m, lam * 1e-3, nodes, SKY_TH, self.n_med, angular=self._angular(N))
        cm = DR.cmf(lam)
        if self.live["light"] == "mono":
            wgt = 1.0
            self.XYZ = av["dsdo"][:, None] * cm[None, :]
            self.Ysum = cm[1] * av["dsdo"]
            self.Ypol = cm[1] * av["dsdo_pol"]
        else:
            wgt = float(ws[k] * DR.sun(lam))
            self.XYZ += wgt * av["dsdo"][:, None] * cm[None, :]
            self.Ysum += wgt * cm[1] * av["dsdo"]
            self.Ypol += wgt * cm[1] * av["dsdo_pol"]
        rel = float(np.max(av["err"]) / np.max(av["dsdo"])) if np.max(av["dsdo"]) > 0 else 0.0
        self.sky_err = max(self.sky_err, rel)
        self.sky_tail = max(self.sky_tail, float(av["tail"]))
        if nodes["coarse"]:
            self.sky_coarse_dx = max(self.sky_coarse_dx, float(nodes["dx"]))
        rgb = DR.strip_rgb(self.XYZ)
        Y = self.Ysum / max(float(self.Ysum.max()), 1e-300)
        pol = np.where(self.Ysum > 0, -self.Ypol / np.where(self.Ysum > 0, self.Ysum, 1.0), 0.0)
        self.sky_k += 1
        self._msg({"type": "sky", "t": self.t, "seq": self.sky_seq, "k": k, "n": self.sky_n, "lam_nm": lam,
                   "m": [float(m.real), float(m.imag)], "n_nodes": int(nodes["w"].size), "dx": nodes["dx"],
                   "coarse": bool(nodes["coarse"]), "rel_err": rel, "C_sca": av["C_sca"], "C_ext": av["C_ext"],
                   "tail": float(av["tail"])},
                  {"dsdo": av["dsdo"].astype(np.float32), "rgb": rgb.reshape(-1), "Y": Y.astype(np.float32),
                   "pol": pol.astype(np.float32)})
        if self.sky_k == self.sky_n:
            self._sky_done()

    def _max_nodes(self, lam):
        """Size nodes at this wavelength within MAX_NODES and the step's time budget (review UX-params P16: drops of
        1 mm took ~19 s per wavelength, «⏭» computed all 24 at once, > 2 min): the cost of the size average is ~nodes x
        terms x angles; beyond the budget the nodes are coarser, and the sky's check says so (the ripple and the
        supernumerary bows of such drops are washed out anyway)."""
        hi = self.r_um * (1.0 + 4.0 * self.width) if self.width > 0 else self.r_um
        N = mie.n_terms(float(mie.size_parameter(hi, lam * 1e-3, self.n_med)))
        cap = int(STEP_BUDGET_S / (SKY_S_PER_UNIT * N * len(SKY_TH)))
        return max(9, min(MAX_NODES, cap))

    def _sky_done(self):
        lams, _ = self._sky_lams()
        G_CLOUD = T("Cloud of drops")
        head = T("the largest over the angles difference of two alternating half-sums over the sizes, as fractions of "
                 "the maximum of ⟨dσ/dΩ⟩: an estimate of the largest error by its order of magnitude (on the presets the "
                 "true largest error is {lo}–{hi} of this estimate), not a bound and not the error at every angle; the "
                 "step in size does not resolve the series' narrow resonances", lo=0.1, hi=3)
        if self.width > 0:
            head = T("{head}. Not included: the cut of the distribution at ±4σ, which removes {tail:.1e} of the "
                     "probability; its bias is ≲ 3 of this fraction of the maximum", head=head, tail=self.sky_tail)
        else:
            head = T("{head}; drops of one size", head=head)
        self._check("sky_sum", T("Sky: the error estimate of the sum over the sizes (the largest over the wavelengths)"),
                    self.sky_err, None, tol=None, info=True, group=G_CLOUD,
                    note=join([head, T("a coarse sampling of the sizes (a step in x up to {dx:.2g}): the ripple and the "
                                       "supernumerary bows are washed into noise here", dx=self.sky_coarse_dx)
                               if self.sky_coarse_dx else ""]))
        Y = self.Ysum
        lo = (SKY_DEG >= 132.0) & (SKY_DEG <= 145.0)
        if lo.any() and 2 in self.bows and self.live["light"] == "white" and self.params["index"] == "water":
            k = int(np.argmax(np.where(lo, Y, -np.inf)))
            d550 = RB.descartes(float(DR.index(self.params, 550.0).real), 2)
            th_d = math.degrees(d550["theta"])
            self._check("sky_bow", T("Sky: the brightest angle of the primary bow (white light) against Descartes at "
                                     "{lam} nm", lam=550),
                        float(SKY_DEG[k]), th_d, "°", tol=None, info=True, group=G_CLOUD,
                        note=T("the brightness Y over {n:d} wavelengths, the size {r} µm ± {w} %: the maximum is "
                               "{d:+.2f}° from Descartes' angle, shifted to the bright side by Airy's shift and blurred "
                               "over the wavelengths", n=len(lams), r=self.r_um, w=100 * self.width,
                               d=float(SKY_DEG[k]) - th_d))
        self._msg({"type": "event", "t": self.t, "kind": "sky",
                   "text": T("the sky is complete: {n:d} wavelengths, drops of {r} µm ± {w} %", n=len(lams), r=self.r_um,
                             w=100 * self.width)})

    # --- checks and messages ---------------------------------------------------------------------------------------
    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None, info=False, group=None):
        group = T("Drop") if group is None else group
        rel = None
        if ref is not None and value is not None and ref != 0:
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": self.t, "id": cid, "label": label, "value": value, "ref": ref, "unit": unit,
             "rel": rel, "group": group, "note": note, "tol": tol}
        if ok is not None:
            d["ok"] = bool(ok)
        if info:
            d["info"] = True
        self._msg(d)

    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, None
        self._msg({"type": "arrow", "t": self.t, "id": "incident", "from": [0.0, 0.0, -2.45], "vec": [0.0, 0.0, 1.0],
                   "label": T("incident light (along +z)"), "layer": T("Incident wave"), "color": "#ffe9a0"})
        self._msg({"type": "arrow", "t": self.t, "id": "polarisation", "from": [0.0, 0.0, -2.2], "vec": [0.6, 0.0, 0.0],
                   "label": T("polarisation E along x"), "layer": T("Polarisation of the incident wave"),
                   "color": "#7fb7ff"})
        for meta, blobs in buf:
            self.emit(meta, blobs)

    # --- time ------------------------------------------------------------------------------------------------------------
    def advance(self, t_target):
        dt = t_target - self.t
        self.t = t_target
        while self.sky_k < self.sky_n and self.t >= self.sky_t0 + (self.sky_k + 1) * T_LAM - 1e-12:
            self._sky_step()
        if self.near:
            self._advance_planes(t_target, dt)

    def max_step(self):
        return T_LAM

    def next_event_time(self):
        """The next wavelength of the sky (P16: «⏭» to the end of the scan computed every wavelength at once)."""
        if self.sky_k >= self.sky_n:
            return None
        return self.sky_t0 + (self.sky_k + 1) * T_LAM

    def frame(self):
        return {"seq": self.seq, "sky_seq": self.sky_seq, "k": self.sky_k, "n": self.sky_n}, {}

    # --- live set-up ---------------------------------------------------------------------------------------------------
    def live_values(self):
        return dict(self.live)

    def set_live(self, values):
        merged, errors = SCHEMA.coerce_live(self.live, values)
        if errors:
            raise ValueError(join(errors))
        old = self.live
        self.live = merged
        try:
            self._setup()
        except Exception:
            self.live = old
            raise
        lam = float(merged["lam_nm"])
        what = T("sunlight") if merged["light"] == "white" else T("one wavelength {lam} nm", lam=lam)
        return T("light: {what}; the drop at {lam} nm computed anew", what=what, lam=lam)

    def engine_modules(self):
        mods = ["core.optics.mie", "core.optics.mie_debye", "core.optics.mie_poly", "core.optics.radiation",
                "core.data", "theories.approx.rainbow", "tools.colour"]
        if self.near:
            mods.append("core.geometry")
        return mods

    def header(self):
        p = self.params
        mat = (T("water") if p["index"] == "water" else
               T("n = {n} + {k}i", n=float(p["n_re"]), k=float(p["n_im"])))
        approximations = [T("single scattering by a sparse cloud of drops: the drops' intensities add up"),
                          T("sunlight is a black body at {T} K (without absorption lines and the atmosphere); the "
                            "angular size of the Sun ({sun}°) is not taken into account: the bows in the sky are "
                            "blurred by another half a degree", T=5772, sun=0.5),
                          T("the drops are spheres (large rain drops are flattened)")]
        if p["index"] == "water":
            approximations.append(T("water without absorption: IAPWS gives only the real part of the index (so the "
                                    "series' narrow resonances are narrower here than in real water)"))
        if self.n_med == 1.0:
            approximations.append(T("the medium around the drop is vacuum (n = 1): in air the drop's index relative to "
                                    "the medium is n_air times smaller, and the angles of the bows shift by fractions "
                                    "of a degree (for water at {tc} °C and {lam} nm: p = 2 by {s2:+.2f}°, p = 3 by "
                                    "{s3:+.2f}° for an illustrative n_air − 1 = {na})", tc=10, lam=550,
                                    s2=AIR_SHIFT[0], s3=AIR_SHIFT[1], na=2.77e-4))
        else:
            approximations.append(T("the medium is homogeneous, transparent, without dispersion: n = {n}",
                                    n=self.n_med))
        if self.width > 0:
            approximations.append(T("the sizes have a gamma distribution cut at ±4σ (the fraction cut off is in the "
                                    "check “Sky: the error estimate”)"))
            nd = MP.size_nodes(self.r_um, self.width, DR.LAM_MIN * 1e-3, self.n_med, max_nodes=MAX_NODES)
            if nd["coarse"]:
                approximations.append(T("a coarse sampling of the sizes: at short wavelengths the step in x is up to "
                                        "{dx:.2g} (≤ {need} is needed, at most {nmax:d} nodes): the ripple of the "
                                        "intensity and the supernumerary bows in the sky are washed into noise, the "
                                        "computation is heavy", dx=float(nd["dx"]), need=0.25, nmax=MAX_NODES))
        objects = [{"id": "drop", "label": T("Drop ({mat}), radius a = {r} µm; in the scene the radius is 1", mat=mat,
                                             r=self.r_um),
                    "kind": "sphere", "center": [0.0, 0.0, 0.0], "radius": 1.0, "visible": True}]
        layers = []
        if self.near:
            layers.append({"id": "field", "label": T("Field |E|² in the volume (inside and around the drop)"),
                           "kind": "volume", "visible": True, "look": {"density": 0.6, "threshold": 0.05}})
        views = [["iso", T("Iso"), T("Isometric (F)"), [0.45, -0.75, -0.5]],
                 ["side", T("Side"), T("The plane xz: the light from left to right, the polarisation up"),
                  [0.0, -1.0, 0.0]],
                 ["back", T("Back to the Sun"), T("The view of a rainbow's observer: along the light, the Sun behind"),
                  [0.0, 0.0, -1.0]]]
        return {
            "title": T("Light scattered by a drop: {mat}, ⟨r⟩ = {r} µm", mat=mat, r=self.r_um),
            "text": T("The exact Mie series for one drop: the phase function, the polarisation, the scattered light as "
                      "a surface around the drop, the near field of small drops; the Debye series separates the "
                      "reflected light (p = 0), the transmitted (p = 1) and the light reflected inside (p = 2, the "
                      "primary rainbow; p = 3, the secondary). A cloud of drops in sunlight: the colour of the sky "
                      "against the scattering angle builds up wavelength after wavelength."),
            "actions": [],
            "approximations": approximations,
            "scene3d": {"box": [list(BOX[0]), list(BOX[1])], "units": "a", "objects": objects, "layers": layers,
                        "views": views, "up": [1.0, 0.0, 0.0],
                        "planes": {"max": MAX_PLANES if self.near else 0, "center": [0.0, 0.0, 0.0],
                                   "defaults": {str(i): list(v) for i, v in DEFAULT_NORMALS.items()}}},
            "drop": {"r_um": self.r_um, "width": self.width, "index": p["index"], "t_c": float(p["t_c"]),
                     "n_medium": self.n_med, "near": self.near, "x_max": self.x_max},
            "sky": {"deg": [float(SKY_DEG[0]), float(SKY_DEG[-1]), len(SKY_DEG)], "t_lam": T_LAM},
            "units": {"t": T("s (the world's time: one wavelength per {t} s)", t=T_LAM), "x": "a"},
        }, {}


VIZ = {
    "id": "v17_mie_scattering",
    "title": T("Mie scattering by a drop: the rainbow and the glory"),
    "summary": T("The exact Mie series for a water drop: the phase function and the polarisation, the Debye series "
                 "(reflection, passage, internal reflections) against Descartes' rays and Airy's theory, the near "
                 "field of a small drop; a cloud of drops in sunlight, the colour of the sky: the rainbow, the "
                 "supernumerary bows, Alexander's band, the glory."),
    "purpose": T("See where the rainbow and its supernumerary bows come from, how the wave theory differs from the ray "
                 "theory, why the bows blur for drops of different sizes, and where the glory around the antisolar "
                 "point comes from."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
