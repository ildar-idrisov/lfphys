# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The double-slit experiment as a stream of single particles, in causal order.

1. **Emission** (t_e, Poisson stream of the source rate): the particle's own wavelength (log-normal spectrum), group
   velocity, source point and internal state (drawn from the source's density matrix).
2. **Slit plane** (t_e + L1/v): the apparatus present at THAT moment acts - elements at the slits (absorption with
   the probability their projectors give), the which-path qubit is coupled, a probe photon of the microscope may
   scatter (a transverse kick), the Aharonov-Bohm phase; GRW hits during the flight to the screen are drawn here as
   random kicks q ~ N(0, 1/(2 r_C^2)) at uniform distances z' and enter as the equivalent slit-plane kick
   q (1 - z'/L2) (exact for the screen pattern in the paraxial engine; review 2026-10-22 R1).
3. **Screen** (t_e + (L1 + L2)/v): the apparatus present at THAT moment decides the rest - the analyzer in front of
   the screen and the basis in which the which-path detector is read (review R4: a change while the particle flies
   acts on it). Born rule P(x, r) = sum_jl A_j A_l^* G^(r)_jl with the Gram matrix of the particle's marks; then the
   analyzer's absorption, missing the finite screen (Parseval), the hit position (exact within the grid cell for the
   piecewise-linear density), detector efficiency.
No rule "observed -> no interference" exists: interference between slits j and l survives only through G_jl.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field

import numpy as np

from lfphys.core.quantum import marks
from lfphys.i18n import T
from lfphys.core.quantum.particles import C, E_CHARGE, H, U, Particle
from lfphys.core.quantum.scattering import dipole_directions
from lfphys.theories.alternatives import born_rule, collapse
from lfphys.theories.approx import paraxial

FLAG_DARK, FLAG_R1, FLAG_READ, FLAG_SCAT, FLAG_REC, FLAG_MIX = 1, 2, 4, 8, 16, 32

def setup_key(params: dict) -> int:
    """The set-up's key: its parameters as sorted JSON, hashed to 64 bits (as u35's ``engine/bench.py rng_for``). Every
    generator of a run is seeded by the world's seed and this key together, so that every set-up of an atlas, all of
    which share one seed, draws its own independent sample (RULES §10). With the seed alone the 48 points of Explore
    drew the same random numbers (common random numbers): at d = 100 and 200 µm all 4732 photons were detected at the
    same instants, their positions drawn from the same uniforms through each point's distribution (Spearman 0.999998;
    integrator I-P, 2026-11-19)."""
    text = json.dumps({k: params[k] for k in sorted(params)}, sort_keys=True, default=repr)
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "little")


#: the elements at the slits by their short names (the parameter forms add which particle they act on)
ELEMENT_NAMES = {"none": T("none"), "polarizer": T("polariser"), "hwp": T("λ/2 plate"), "qwp": T("λ/4 plate"),
                 "rot_y": T("spin rotation about y"), "filter": T("spin filter"), "phase": T("phase shift"),
                 "block": T("shutter")}


def _join(items, sep="; "):
    """Texts joined into one text (nested pairs, so that every language joins them its own way)."""
    items = [x for x in items if x]
    if not items:
        return None
    out = items[0]
    for x in items[1:]:
        out = T("{a}; {b}", a=out, b=x) if sep == "; " else T("{a}, {b}", a=out, b=x)
    return out


@dataclass
class Geometry:
    n: int
    a: float
    d: float
    L1: float  # inf = plane wave
    L2: float
    src_width: float
    x: np.ndarray  # screen grid
    pixel: float

    @property
    def slits(self) -> np.ndarray:
        return (np.arange(self.n) - 0.5 * (self.n - 1)) * self.d

    @property
    def dx(self) -> float:
        return float(self.x[1] - self.x[0])


@dataclass
class Apparatus:
    """What the experimenter can change during a run. Slit-plane parts act at slit passage, the analyzer and the
    readout basis at the screen."""
    elements: list  # [(kind, angle)] per slit
    analyzer: tuple = ("none", 0.0)
    wp_mode: str = "none"  # none | qubit | microscope
    wp_slit: int = 0
    wp_theta: float = 90.0
    wp_read: str = "none"  # none | path | angle
    wp_read_angle: float = 45.0
    mic_lambda: float = 500e-9
    mic_prob: float = 1.0
    mic_dir: str = "y"
    mic_pol: str = "z"
    mic_record: str = "all"  # none | all | cone
    mic_cone_deg: float = 30.0
    ab_flux: float = 0.0  # in h/e
    rate: float = 1000.0
    seg: int = 0

    def describe(self, internal) -> T:
        parts = []
        for j, (kind, ang) in enumerate(self.elements):
            if kind == "block":  # a shutter has no angle (review R-W F14)
                parts.append(T("slit {j:d}: {elem}", j=j + 1, elem=ELEMENT_NAMES.get(kind, kind)))
            elif kind != "none":
                parts.append(T("slit {j:d}: {elem} {a:g}°", j=j + 1, elem=ELEMENT_NAMES.get(kind, kind), a=float(ang)))
        if self.analyzer[0] != "none":
            parts.append(T("analyser {a:g}°", a=float(self.analyzer[1])))
        if self.wp_mode == "qubit":
            rd = {"none": T("not read"), "path": T("read in the path basis"),
                  "angle": T("read in the {a:g}° basis", a=float(self.wp_read_angle))}[self.wp_read]
            parts.append(T("which-path detector at slit {j:d}, θ = {th:g}°, {read}", j=self.wp_slit + 1,
                           th=float(self.wp_theta), read=rd))
        if self.wp_mode == "microscope":
            parts.append(T("microscope: λ = {lam:g} nm, p = {p:g}", lam=float(self.mic_lambda * 1e9),
                           p=float(self.mic_prob)))
        if self.ab_flux:
            parts.append(T("Aharonov–Bohm flux {f:g} h/e", f=float(self.ab_flux)))
        return _join(parts) or T("no observer and no elements")


@dataclass
class Laws:
    born_p: float = 2.0
    collapse: str = "none"  # none | grw | slit
    grw_lambda: float = 1e-16  # per nucleon mass (atomic mass unit), 1/s
    grw_rc: float = 1e-7  # m


@dataclass
class Source:
    pol_state: str = "H"
    pol_degree: float = 1.0
    pol_custom: tuple = (0.0, 0.0)
    dlam_rel: float = 0.0  # sigma of ln(lambda)


@dataclass
class Batch:
    """Particles of one emission batch, column-wise."""
    t_e: np.ndarray
    pid: np.ndarray
    lam: np.ndarray
    v: np.ndarray
    xs: np.ndarray
    chi: np.ndarray  # (B, d_int)
    t_slit: np.ndarray
    t_det: np.ndarray
    stage: np.ndarray  # 0 flying to the slits, 1 behind the slits, 2 done
    kappa: np.ndarray = None
    scat: np.ndarray = None
    rec: np.ndarray = None
    nf: np.ndarray = None
    hits: np.ndarray = None
    absorbed: np.ndarray = None
    app: list = None  # apparatus at slit passage (per particle)


@dataclass
class Outcome:
    t_det: np.ndarray
    x: np.ndarray
    y: np.ndarray
    flags: np.ndarray
    kick: np.ndarray
    seg: np.ndarray
    pid: np.ndarray
    counts: dict = field(default_factory=dict)
    stories: list = field(default_factory=list)


def axis(name):
    return {"x": np.array([1.0, 0, 0]), "y": np.array([0, 1.0, 0]), "z": np.array([0, 0, 1.0])}[name]


class Experiment:
    def __init__(self, particle: Particle, geom: Geometry, laws: Laws, source: Source, rng):
        self.p = particle
        self.g = geom
        self.laws = laws
        self.src = source
        self.rng = rng
        self.internal = particle.internal
        self.d_int = 1 if particle.internal is None else 2
        self.eff = 1.0
        self._base = None
        # vector mode (a perfectly conducting screen; lfphys.core.em.slit): the energy flux of the TE and TM solutions
        # through the screen plane, set by the visualization; None in the scalar mode
        self.vec = None

    # --- per-particle physics ----------------------------------------------------------------------------
    def v_of_lam(self, lam):
        """Group velocity for a wavelength (relativistic)."""
        if self.p.mass == 0:
            return np.full_like(np.asarray(lam, float), C)
        pc = H * C / np.asarray(lam, float)
        mc2 = self.p.mass * C * C
        return pc * C / np.hypot(pc, mc2)

    def grw_rate(self) -> float:
        """GRW hit rate of the particle: lambda per atomic mass unit times the mass in u (review R22: mass-proportional,
        so electrons are included; massless particles have none)."""
        if self.laws.collapse != "grw" or self.p.mass == 0:
            return 0.0
        return self.laws.grw_lambda * self.p.mass / U

    def emit(self, t_e: np.ndarray, pid0: int, rng) -> Batch:
        B = len(t_e)
        g = self.g
        lam = np.full(B, self.p.lam)
        if self.src.dlam_rel > 0:
            lam = self.p.lam * np.exp(self.src.dlam_rel * rng.normal(size=B))  # log-normal (review R21)
        v = self.v_of_lam(lam)
        xs = (rng.random(B) - 0.5) * g.src_width if (g.src_width > 0 and math.isfinite(g.L1)) else np.zeros(B)
        chi = np.array([marks.sample_internal(rng, self.internal, self.src.pol_state, self.src.pol_degree,
                                              self.src.pol_custom) for _ in range(B)]).reshape(B, self.d_int)
        L1 = g.L1 if math.isfinite(g.L1) else 0.0
        return Batch(t_e, pid0 + np.arange(B, dtype=np.int64), lam, v, xs, chi, t_e + L1 / v,
                     t_e + (L1 + g.L2) / v, np.zeros(B, np.int8))

    def at_slits(self, b: Batch, idx: np.ndarray, app: Apparatus, rng):
        """Slit-plane stage for the particles idx of batch b with the apparatus present now."""
        n = len(idx)
        if b.kappa is None:
            B = len(b.t_e)
            b.kappa, b.scat, b.rec = np.zeros(B), np.zeros(B, bool), np.zeros(B, bool)
            b.nf, b.hits, b.absorbed = np.zeros((B, 3)), np.zeros(B, int), np.zeros(B, bool)
            b.app = [None] * B
        k = 2 * math.pi / b.lam[idx]
        kap = np.zeros(n)
        if app.wp_mode == "microscope":
            sc = rng.random(n) < app.mic_prob
            ns = int(sc.sum())
            if ns:
                nf = dipole_directions(rng, axis(app.mic_pol), ns)
                kp = 2 * math.pi / app.mic_lambda
                kap[sc] = kp * (axis(app.mic_dir)[0] - nf[:, 0])
                b.nf[idx[sc]] = nf
                if app.mic_record == "all":
                    b.rec[idx[sc]] = True
                elif app.mic_record == "cone":
                    rc = np.zeros(ns, bool)
                    rc[:] = nf[:, 2] > math.cos(math.radians(app.mic_cone_deg))
                    b.rec[idx[sc]] = rc
            b.scat[idx] = sc
        rate = self.grw_rate()
        if rate > 0:
            hits = rng.poisson(rate * self.g.L2 / b.v[idx])
            b.hits[idx] = hits
            for i in np.nonzero(hits)[0]:
                q = collapse.grw_kicks(rng, hits[i], self.laws.grw_rc)
                zf = rng.random(hits[i])  # z'/L2
                kap[i] += float(np.sum(q * (1.0 - zf)))
        b.kappa[idx] = kap
        # absorption by the elements at the slits (equal illumination of the slits)
        J = self.element_mats(app)
        surv = np.einsum("jab,pb->pja", np.array(J), b.chi[idx])
        surv = np.sum(np.abs(surv) ** 2, axis=(1, 2)) / self.g.n
        b.absorbed[idx] = rng.random(n) >= surv
        for i in idx:
            b.app[i] = app
        b.stage[idx] = 1

    def element_mats(self, app: Apparatus):
        return [marks.element_matrix(kd, ang, self.internal) for kd, ang in app.elements]

    def ab_phases(self, app: Apparatus):
        """q Phi / hbar = 2 pi (q/e) (Phi / (h/e)) on slits 2..N (solenoid between slits 1 and 2); review R6."""
        if not app.ab_flux or self.p.charge == 0:
            return np.zeros(self.g.n)
        ph = 2 * math.pi * app.ab_flux * self.p.charge / E_CHARGE
        return np.array([0.0] + [ph] * (self.g.n - 1))

    def gram(self, chi: np.ndarray, app_slit: Apparatus, app_screen: Apparatus):
        """Gram matrices of the marks: G[p, r, j, l] for each readout r (one r if the detector is absent or not read)
        and the unread G_full[p, j, l]; chi (P, d_int). Elements and the qubit coupling come from app_slit, the
        analyzer and the readout basis from app_screen."""
        J = np.array(self.element_mats(app_slit))  # (n, d, d)
        Pa = marks.analyzer_matrix(app_screen.analyzer[0], app_screen.analyzer[1], self.internal)
        V = np.einsum("ab,jbc,pc->pja", Pa, J, chi)  # (P, n, d): internal part after the analyzer
        S = np.einsum("pja,pla->pjl", V, V.conj())
        ph = np.exp(1j * self.ab_phases(app_slit))
        Ph = np.outer(ph, ph.conj())
        coupled = app_slit.wp_mode == "qubit"
        dets = marks.detector_states(self.g.n, app_slit.wp_slit, app_slit.wp_theta, coupled)
        Dm = np.array(dets)  # (n, d_det)
        Dfull = Dm @ Dm.conj().T  # <d_l|d_j> ... (j, l): sum_c d_j[c] conj(d_l[c])
        G_full = S * (Dfull * Ph)[None]
        if coupled and app_screen.wp_read != "none":
            basis = marks.readout_basis(0.0 if app_screen.wp_read == "path" else app_screen.wp_read_angle)
            Gs = []
            for bvec in basis:
                cr = Dm @ bvec.conj()  # <b_r|d_j>
                Gs.append(S * (np.outer(cr, cr.conj()) * Ph)[None])
            G = np.stack(Gs, axis=1)
        else:
            G = G_full[:, None]
        if self.laws.collapse == "slit":  # modified physics: forced which-slit collapse, no cross terms
            G = collapse.which_slit_gram(G)
            G_full = collapse.which_slit_gram(G_full)
        return G, G_full

    def base_A(self):
        if self._base is None:
            self._base = paraxial.slit_amplitudes(self.g.x, self.g.L2, self.p.k, self.g.slits, self.g.a, self.g.L1)
        return self._base

    def intensities(self, lam, xs, kappa, G):
        """I[p, r, x] for the particles (own wavelength, source point, kick) and their Gram matrices."""
        g = self.g
        if np.all(lam == self.p.lam) and not np.any(xs) and not np.any(kappa):
            A0 = self.base_A()
            out = np.zeros((G.shape[0], G.shape[1], len(g.x)))
            for j in range(g.n):
                for l in range(g.n):
                    out += (G[:, :, j, l, None] * (A0[j] * A0[l].conj())[None, None]).real
            return np.maximum(out, 0.0)
        k = 2 * math.pi / lam
        A = paraxial.slit_amplitudes(g.x[None, :], g.L2, k[:, None], g.slits, g.a, g.L1, xs[:, None], kappa[:, None])
        out = np.einsum("pjx,plx,prjl->prx", A, A.conj(), G, optimize=True).real
        return np.maximum(out, 0.0)

    def born(self, I):
        return born_rule.weight(I, self.laws.born_p)

    def vec_plain(self, app: Apparatus) -> bool:
        """True when the vector screen decides this particle's hit: vector mode with standard laws, and an apparatus
        without elements at the slits, observer or analyzer (which-path marks have no vector counterpart here)."""
        return (self.vec is not None and bool(self.vec.get("hits")) and app.analyzer[0] == "none"
                and app.wp_mode == "none" and all(kd == "none" for kd, _ in app.elements))

    def at_screen(self, b: Batch, idx: np.ndarray, app: Apparatus, seg: int, rng, story_n: int = 0) -> Outcome:
        """Screen stage for the particles idx (not absorbed at the slits) with the apparatus present now: the vector
        screen (energy flux of the conductor's solution) for plain set-ups in vector mode, the scalar Born rule with
        the marks otherwise."""
        if self.vec is not None and self.vec.get("hits"):
            vm = np.array([self.vec_plain(b.app[i]) for i in idx], bool) & self.vec_plain(app)
            if vm.all():
                return self._at_screen_vec(b, idx, seg, rng, story_n)
            if vm.any():
                return _merge(self._at_screen_vec(b, idx[vm], seg, rng, story_n),
                              self._at_screen_scalar(b, idx[~vm], app, seg, rng, story_n))
        return self._at_screen_scalar(b, idx, app, seg, rng, story_n)

    def _at_screen_vec(self, b: Batch, idx: np.ndarray, seg: int, rng, story_n: int = 0) -> Outcome:
        """Vector screen: a photon of the incident plane wave falling on the strip of width W = n d is transmitted
        with probability P_t / W and lands with the density of the energy flux j_z(x) / W through the screen plane,
        j_z = |chi_H|^2 j_TM + |chi_V|^2 j_TE (H across the slits = TM, V along them = TE; the flux has no TE-TM cross
        term); the rest is reflected or scattered back by the screen."""
        g, v = self.g, self.vec
        n = len(idx)
        chi = b.chi[idx]
        wH, wV = np.abs(chi[:, 0]) ** 2, np.abs(chi[:, 1]) ** 2
        s = wH + wV
        wH, wV = wH / s, wV / s
        I = np.maximum(wH[:, None] * v["J_TM"][None, :] + wV[:, None] * v["J_TE"][None, :], 0.0) / v["W"]
        p_scr = np.minimum(np.sum(0.5 * (I[:, 1:] + I[:, :-1]), axis=1) * g.dx, 1.0)
        p_tr = np.minimum((wH * v["Pt_TM"] + wV * v["Pt_TE"]) / v["W"], 1.0)  # <= 1: checked when the set-up is built
        u = rng.random(n)
        hit = u < p_scr
        missed = ~hit & (u < np.maximum(p_tr, p_scr))
        reflected = ~hit & ~missed
        xpos = np.zeros(n)
        if hit.any():
            xpos[hit], _ = self._sample(I[hit], 1, rng)
        detected = hit & (rng.random(n) < self.eff)
        flags = np.zeros(n, np.uint8)
        mixed = np.array([b.app[i].seg != seg for i in idx], bool)
        flags[mixed] |= FLAG_MIX
        sel = detected
        out = Outcome(b.t_det[idx][sel], xpos[sel], (rng.random(int(sel.sum())) - 0.5).astype(np.float32), flags[sel],
                      np.zeros(int(sel.sum()), np.float32), np.full(int(sel.sum()), seg, np.uint16),
                      b.pid[idx][sel].astype(np.uint32))
        out.counts = {"absorbed_an": 0, "missed": int(missed.sum()), "reflected": int(reflected.sum()),
                      "undetected": int((hit & ~detected).sum()), "detected": int(detected.sum()),
                      "mixed": int((mixed & detected).sum())}
        for q in range(min(story_n, n)):
            i = idx[q]
            fate = (T("reflected or scattered back by the conducting screen") if reflected[q] else
                    T("passed the slits but missed the screen") if missed[q] else
                    T("arrived but was not registered (detector efficiency)") if (hit[q] and not detected[q]) else
                    T("registered at x = {x:.4g} µm (vector screen: TE/TM energy flux)", x=float(xpos[q] * 1e6)))
            out.stories.append(self.story(b, i, fate, None))
        return out

    def _at_screen_scalar(self, b: Batch, idx: np.ndarray, app: Apparatus, seg: int, rng, story_n: int = 0) -> Outcome:
        """Scalar screen stage (the Born rule with the marks) for the particles idx."""
        g = self.g
        n = len(idx)
        G, G_full = self._gram_per_app(b, idx, app)
        I = self.intensities(b.lam[idx], b.xs[idx], b.kappa[idx], G)
        nR = I.shape[1]
        # analyzer absorption given the slits were passed: sum_j |Pa J_j chi|^2 / sum_j |J_j chi|^2
        trace_full = np.real(np.einsum("pjj->p", G_full))
        slit_pass = np.array([self._slit_norm(b, i) for i in idx])
        pass_an = np.where(slit_pass > 0, trace_full / np.maximum(slit_pass, 1e-300), 0.0)
        absorbed_an = rng.random(n) >= np.minimum(pass_an, 1.0)
        total = b.lam[idx] * g.L2 * g.a * trace_full  # Parseval flux of these marks
        on_screen = np.clip(I.sum(axis=(1, 2)) * g.dx / np.maximum(total, 1e-300), 0.0, 1.0)
        missed = (~absorbed_an) & (rng.random(n) >= on_screen)
        Pw = self.born(I).reshape(n, -1)
        hit = ~absorbed_an & ~missed & (Pw.sum(axis=1) > 0)
        xpos = np.zeros(n)
        r_out = np.zeros(n, int)
        if hit.any():
            xpos[hit], r_out[hit] = self._sample(Pw[hit], nR, rng)
        detected = hit & (rng.random(n) < self.eff)
        flags = np.zeros(n, np.uint8)
        if nR > 1:
            flags |= FLAG_READ
            flags[r_out == 1] |= FLAG_R1
        flags[b.scat[idx]] |= FLAG_SCAT
        flags[b.rec[idx]] |= FLAG_REC
        mixed = np.array([b.app[i].seg != seg for i in idx])
        flags[mixed] |= FLAG_MIX
        sel = detected
        out = Outcome(b.t_det[idx][sel], xpos[sel], (rng.random(int(sel.sum())) - 0.5).astype(np.float32), flags[sel],
                      (b.kappa[idx][sel] * g.d).astype(np.float32), np.full(int(sel.sum()), seg, np.uint16),
                      b.pid[idx][sel].astype(np.uint32))
        out.counts = {"absorbed_an": int(absorbed_an.sum()), "missed": int(missed.sum()),
                      "undetected": int((hit & ~detected).sum()), "detected": int(detected.sum()),
                      "mixed": int((mixed & detected).sum())}
        for q in range(min(story_n, n)):
            i = idx[q]
            fate = (T("absorbed by the analyser in front of the screen") if absorbed_an[q] else
                    T("missed the screen") if missed[q] else
                    T("arrived but was not registered (detector efficiency)") if (hit[q] and not detected[q]) else
                    T("registered at x = {x:.4g} µm, which-path detector reading: {r:d}", x=float(xpos[q] * 1e6),
                      r=int(r_out[q])) if nR > 1 else
                    T("registered at x = {x:.4g} µm", x=float(xpos[q] * 1e6)))
            out.stories.append(self.story(b, i, fate, G_full[q]))
        return out

    def _gram_per_app(self, b, idx, app_screen):
        """Group the particles by their slit-time apparatus (usually one) and build their Gram matrices."""
        groups = {}
        for q, i in enumerate(idx):
            groups.setdefault(id(b.app[i]), []).append(q)
        res_G = res_Gf = None
        for key, qs in groups.items():
            qs = np.array(qs)
            app_slit = b.app[idx[qs[0]]]
            G, Gf = self.gram(b.chi[idx[qs]], app_slit, app_screen)
            if res_G is None:
                res_G = np.zeros((len(idx),) + G.shape[1:], complex)
                res_Gf = np.zeros((len(idx),) + Gf.shape[1:], complex)
            if G.shape[1] != res_G.shape[1]:  # detector coupled for some, not for others: pad readouts
                if G.shape[1] == 1:
                    G = np.concatenate([G, np.zeros_like(G)], axis=1)
                else:
                    res_G = np.concatenate([res_G, np.zeros_like(res_G)], axis=1)
            res_G[qs] = G
            res_Gf[qs] = Gf
        return res_G, res_Gf

    def _slit_norm(self, b, i):
        J = np.array(self.element_mats(b.app[i]))
        v = np.einsum("jab,b->ja", J, b.chi[i])
        return float(np.sum(np.abs(v) ** 2))

    def _sample(self, Pw, nR, rng):
        """Position and reading drawn from the piecewise-linear density on the grid (exact within each cell, the
        same density the trapezoid rebinning integrates; review R26)."""
        g = self.g
        Ns = len(g.x)
        P = Pw.reshape(len(Pw), nR, Ns)
        cell = 0.5 * (P[:, :, :-1] + P[:, :, 1:])  # (m, nR, Ns-1)
        flat = cell.reshape(len(Pw), -1)
        cdf = np.cumsum(flat, axis=1)
        cdf /= cdf[:, -1:]
        u = rng.random(len(Pw))
        k = np.minimum((cdf < u[:, None]).sum(axis=1), flat.shape[1] - 1)
        r = k // (Ns - 1)
        i = k % (Ns - 1)
        p0 = P[np.arange(len(Pw)), r, i]
        p1 = P[np.arange(len(Pw)), r, i + 1]
        w = rng.random(len(Pw))
        # inverse CDF of the linear density p0 + (p1 - p0) t on [0, 1]
        dp = p1 - p0
        tot = 0.5 * (p0 + p1)
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(np.abs(dp) > 1e-12 * np.maximum(tot, 1e-300),
                         (-p0 + np.sqrt(np.maximum(p0 * p0 + 2 * dp * w * tot, 0.0))) / dp, w)
        t = np.clip(np.nan_to_num(t, nan=0.5), 0.0, 1.0)
        return g.x[i] + t * g.dx, r

    def story(self, b, i, fate, Gf):
        ov = None
        if Gf is not None and self.g.n >= 2:
            n0, n1 = Gf[0, 0].real, Gf[1, 1].real
            ov = abs(Gf[0, 1]) / math.sqrt(n0 * n1) if n0 > 0 and n1 > 0 else None
        return {"id": int(b.pid[i]), "t_emit": float(b.t_e[i]), "t_det": float(b.t_det[i]), "lambda": float(b.lam[i]),
                "x_src": float(b.xs[i]), "state": state_label(b.chi[i], self.internal), "scattered": bool(b.scat[i]),
                "recorded": bool(b.rec[i]), "kick_phase": float(b.kappa[i] * self.g.d), "grw_hits": int(b.hits[i]),
                "overlap12": ov, "fate": fate}


def _merge(a: Outcome, b: Outcome) -> Outcome:
    out = Outcome(*(np.concatenate([getattr(a, f), getattr(b, f)]) for f in ("t_det", "x", "y", "flags", "kick", "seg",
                                                                              "pid")))
    out.counts = {k: a.counts.get(k, 0) + b.counts.get(k, 0) for k in set(a.counts) | set(b.counts)}
    out.stories = a.stories + b.stories
    return out


def state_label(chi, internal):
    if internal is None:
        return "—"
    a, b = chi
    if internal == "pol":
        # Stokes parameters; S3 = I_R - I_L with R = (1, -i)/sqrt2 (time convention exp(i(kz - wt)); review R19)
        s0 = abs(a) ** 2 + abs(b) ** 2
        s1 = (abs(a) ** 2 - abs(b) ** 2) / s0
        s2 = 2 * (a * np.conj(b)).real / s0
        s3 = 2 * (a * np.conj(b)).imag / s0
        return T("Stokes parameters ({s1:+.2f}, {s2:+.2f}, {s3:+.2f})", s1=float(s1), s2=float(s2), s3=float(s3))
    s0 = abs(a) ** 2 + abs(b) ** 2
    sx = 2 * (np.conj(a) * b).real / s0
    sy = 2 * (np.conj(a) * b).imag / s0
    sz = (abs(a) ** 2 - abs(b) ** 2) / s0
    return T("spin ({sx:+.2f}, {sy:+.2f}, {sz:+.2f})", sx=float(sx), sy=float(sy), sz=float(sz))
