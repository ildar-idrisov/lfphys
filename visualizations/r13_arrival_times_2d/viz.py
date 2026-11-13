# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""r13: when does the particle arrive? Arrival times in 2-D by the rules in use (a wrapper over lfphys; plan P14.6, on
P6 and r12).

A wave packet flies along z to a detecting plane, freely or through r12's double slit. The run solves the
Schroedinger equation on the plane (x, z) (r12's machinery: split operator on GPU 0 where it pays, absorbing layers,
the Bohm ensemble) and records at the plane, at every step, the current J(x, t), psi and d psi/dz. From them and
from the initial state the run computes the arrival-time distribution by each rule
(lfphys.theories.interpretations.arrival_times, lfphys.theories.models.detection):

* quantum flux: J integrated over the plane (and J(x, t) itself: the joint distribution of place and time);
* Bohm: the first crossing of each trajectory of the ensemble (and, in free flight, the exact first-arrival law from
  the running maximum of the flux's integral);
* Aharonov-Bohm-Kijowski, semiclassical and the absorbing boundary rule (free flight only: functionals of the initial
  state for free motion);
* the exponential rules of Wlodarz and Marchewka-Schuss, from psi and d psi/dz on the plane;
* the soft detector: a second run of the same experiment whose screen is an absorbing potential -i W0 (it reflects a
  part of the wave; its clicks are the probability it absorbs).

Initial states along the flight: one packet; a train of packets (Das & Struyve 2021: the exponential rules damp the later
peaks, the semiclassical rule shows one peak); a two-speed superposition whose current flows back through the plane
for a while (quantum backflow: the flux is negative, Bohm's first arrivals are not).

Checks (free flight, against closed forms): the flux and psi on the plane against the exact free evolution; Bohm
hit times against the first-arrival law (KS); the soft detector's reflection against stationary transfer matrices
of its profile; the ABR identity; the initial state's momentum distribution; r12's checks (norm, time step, flux,
equivariance, symmetry).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import cumulative_trapezoid

from lfphys.core.quantum import schrodinger_nd as S
from lfphys.core.quantum.schrodinger1d import FreeGaussians
from lfphys.core.quantum.transfer import transmission_profile
from lfphys.i18n import T, is_t, join
from lfphys.theories.interpretations import arrival_times as AT
from lfphys.theories.models import detection as DET
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from r12_double_slit_2d import viz as V11

from .engine import apparatus as AP

V11_FIXED = {"mark": "none", "mark_deg": 0.0, "flux": 0.0}  # r12's parameters this world does not offer
CURVE_N = 1501        # samples of the curves computed from the initial state (ABK, semiclassical, ABR)
K_N = 4001            # wave numbers for them
ROWS_PER_T0 = 120     # time bins of the joint distribution J(x, t) per classical flight time t0 (a set-up scale)
COLS_MAX = 240        # its x bins
SOFT_REL_TOL = 0.1    # the soft detector's reflection against the stationary one (measured 0.1-4 % at lambda/6-8)
EARLY = 1e-6          # a live detector change at t = 0, or before this much signal reached the detector, acts as if made
                      # at the start (below the tolerances of the comparisons that assume one value: >= 2e-4)


def _p(*a, **k):
    return Param(*a, **k)


LAM, E0_UNIT, K0_UNIT = V11.LAM, V11.E0_UNIT, T("k₀")
DETECTORS, ARRIVAL = T("Detectors"), T("Arrival time")
SCHEMA = Schema([
    _p("particle", V11.PARTICLE, "select", "electron", group=V11.PARTICLE, options=V11.PARTICLES),
    _p("lam_pm", T("de Broglie wavelength λ, pm"), "float", 100.0, unit=V11.PM, group=V11.PARTICLE, min=20.0,
       max=5000.0, log=True,
       help=T("sets the physical scale: every length of the experiment is in λ, every time in units of mλ²/ħ")),
    _p("scene", T("Flight"), "select", "free", group=T("Experiment"),
       options=[("free", T("freely to the detecting plane")), ("slits", T("through two slits (as in r12)"))]),
    _p("L", T("Distance to the detector L, λ"), "float", 30.0, unit=LAM, group=T("Experiment"), min=2.0, max=200.0,
       help=T("free flight: from the centre of the first packet to the plane; slits: from the plate to the screen")),
    _p("state", T("Initial state along the flight"), "select", "gauss", group=V11.PACKET,
       options=[("gauss", T("one packet")), ("train", T("a train of packets (Das & Struyve 2021)")),
                ("backflow", T("a slow and a fast packet meet at the plane: backflow"))]),
    _p("sigma_z", T("Packet width along z σz, λ"), "float", 5.0, unit=LAM, group=V11.PACKET, min=1.0, max=20.0,
       help=T("the momentum spread Δk/k = 1/(4π σz/λ): the narrower the packet, the more the rules diverge")),
    _p("sigma_x", T("Packet width along x σx, λ"), "float", 4.0, unit=LAM, group=V11.PACKET, min=1.0, max=40.0),
    _p("sigma_y", T("Packet width along y σy, λ"), "float", 3.0, unit=LAM, group=V11.PACKET, min=0.5, max=40.0,
       help=T("nothing depends on y, so the wave is the exact product ψ(x, z, t)·η(y, t): η is a free Gaussian packet, "
              "it only spreads; the arrival time does not depend on y")),
    _p("n_train", T("Number of packets in the train"), "int", 4, group=V11.PACKET, min=2, max=8,
       show_if={"state": ["train"]}),
    _p("sep", T("Distance between the packets, λ"), "float", 30.0, unit=LAM, group=V11.PACKET, min=6.0, max=120.0,
       show_if={"state": ["train"]}, help=T("at least 6σz: the packets do not overlap")),
    # the plate is live (review UX-ui U12; r12's rules: rebuilt at the current moment in the world's window)
    _p("a", T("Slit width a, λ"), "float", 2.0, unit=LAM, group=V11.PLATE, min=0.5, max=20.0,
       show_if={"scene": ["slits"]}, live=True, help=V11.LIVE_PLATE_HELP),
    _p("d", T("Distance between the slits d, λ"), "float", 8.0, unit=LAM, group=V11.PLATE, min=1.0, max=60.0,
       show_if={"scene": ["slits"]}, live=True, help=V11.LIVE_PLATE_HELP),
    _p("w", T("Plate thickness w, λ"), "float", 2.0, unit=LAM, group=V11.PLATE, min=0.5, max=10.0,
       show_if={"scene": ["slits"]}, live=True, help=V11.LIVE_PLATE_HELP),
    _p("V0", T("Wall height V₀, in E₀"), "float", 4.0, unit=E0_UNIT, group=V11.PLATE, min=1.5, max=8.0,
       show_if={"scene": ["slits"]}, live=True,
       help=T("the particle's potential energy in the plate's material, in units of its kinetic energy E₀. {live}",
              live=V11.LIVE_PLATE_HELP)),
    _p("edge", T("Width of the edges of the wall and of the soft detector, λ"), "float", 0.2, unit=LAM, group=DETECTORS,
       min=0.1, max=1.0, help=T("the potentials rise over this length (tanh); not less than the grid step")),
    _p("kappa", T("Absorbing boundary: κ, in k₀"), "float", 1.0, unit=K0_UNIT, group=DETECTORS, min=0.05, max=20.0,
       log=True, help=T("the boundary condition ∂ψ/∂z = iκψ (Werner, Tumulka): a wave with k = κ is absorbed entirely, "
                        "others are partly reflected; free flight only. k₀ is the packet's mean wave vector")),
    # the exponential rules' strengths and the soft detector's height are live (review UX-ui U12): a detector made
    # more or less sensitive at the current moment
    _p("mu_w", T("Wlodarz's rule: strength λ₀ (dimensionless)"), "float", 1.0, group=DETECTORS, min=0.01,
       max=20.0, log=True, live=True,
       help=T("λ(t) = λ₀ v₀ ∫|ψ(x, L, t)|² dx: λ₀ is the mean number of clicks if the particle did not vanish. "
              "Changes on the fly: the clicks up to that moment are computed with the old strength, after it with the "
              "new one")),
    _p("mu_ms", T("Marchewka–Schuss rule: strength λ₀ (dimensionless)"), "float", 1.0, group=DETECTORS,
       min=0.01, max=20.0, log=True, live=True,
       help=T("λ(t) = λ₀ (v₀/k₀²) ∫|∂ψ/∂z(x, L, t)|² dx, normalised in the same way. Changes on the fly: the clicks "
              "up to that moment are computed with the old strength, after it with the new one")),
    _p("soft", T("Soft detector (an absorbing potential)"), "bool", True, group=DETECTORS,
       help=T("a second run of the same experiment: behind the detecting plane the potential −iW₀; it reflects a part "
              "of the wave")),
    _p("W0", T("Soft detector: height W₀, in E₀"), "float", 1.0, unit=E0_UNIT, group=DETECTORS,
       min=0.01, max=6.0, log=True, show_if={"soft": [True]}, live=True,
       help=T("the height of the absorbing potential −iW₀ behind the detecting plane, in units of the packet's kinetic "
              "energy E₀: higher absorbs faster but reflects more. Changes on the fly: the absorber of the second run "
              "is rebuilt at the current moment")),
    _p("grid", T("Grid"), "select", "normal", group=V11.COMPUTATION, options=V11.GRIDS),
    _p("n_bohm", T("Number of Bohm particles in the ensemble"), "int", 2000, group=V11.BOHM_TRAJECTORIES,
       min=100, max=8000),
    _p("n_tracks", T("Trajectories to draw"), "int", 60, group=V11.BOHM_TRAJECTORIES, min=10, max=400),
    _p("slit_a", T("Slit A (x = −d/2) open"), "bool", True, group=V11.SETUP, live=True, show_if={"scene": ["slits"]}),
    _p("slit_b", T("Slit B (x = +d/2) open"), "bool", True, group=V11.SETUP, live=True, show_if={"scene": ["slits"]},
       help=T("close a slit while the packet is on its way: the experiment of Das, Deckert, Kellers, Krekels, Struyve "
              "(2024)")),
], presets={
    "gauss": {"label": T("One packet: far from the source all the rules almost agree"), "params": {}},
    "near": {"label": T("Close to the source (σz = {s}λ, L = {L}λ): the rules diverge", s=1, L=5),
             "params": {"sigma_z": 1.0, "L": 5.0}},
    "train": {"label": T("A train of {n:d} packets: the exponential rules damp the later peaks (Das & Struyve 2021)", n=4),
              "params": {"state": "train", "mu_w": 2.0, "mu_ms": 2.0}},
    "backflow": {"label": T("Backflow: the flux through the plane is negative in places, Bohm's first arrivals are not"),
                 "params": {"state": "backflow", "sigma_z": 3.0, "L": 16.5}},
    "slits": {"label": T("Through two slits: the joint distribution of the place and the time of arrival (Das et al. "
                         "2024)"),
              "params": {"scene": "slits", "sigma_x": 8.0, "L": 30.0, "soft": False}},
})


TITLE = T("Particle arrival time: the rules in 2-D")


class Simulation(V11.Simulation):
    SCHEMA = SCHEMA
    FIXED_LIVE = {"mark_deg": 0.0, "flux": 0.0}  # r12's path mark and flux: not in this world

    def __init__(self, params, seed, emit):
        p = {**V11_FIXED, **dict(params)}
        self.free = p["scene"] == "free"
        self.label_slits = not self.free
        self.BACK_LABEL = T("reflected by the plate") if not self.free else T("went back")
        # the flight from the leading packet's centre to the plane (behind the plate: from r12's source point)
        D = float(p["L"]) if self.free else float(p["L"]) - AP.SlitGeometry(
            p["a"], p["d"], p["w"], p["L"], p["sigma_x"], p["sigma_z"], V11.H_OF[p["grid"]], edge=float(p["edge"])).z_src
        self.pk = AP.packets(p["state"], p["sigma_z"], p["n_train"], p["sep"], D)
        self.fg = FreeGaussians(self.pk)  # the longitudinal state, z from the leading packet's centre, hbar = m = 1
        ov = AP.overlap(self.fg, D)
        if ov > AP.OVERLAP_MAX:
            raise Refusal(T("the detector is too close: {p:.1e} of the probability is already beyond its plane at the "
                            "start (at most {m} is allowed)", p=ov, m=AP.OVERLAP_MAX),
                          T("move the plane farther away or make the packet narrower"))
        self.soft = bool(p["soft"])
        # the detectors' strengths in force from each moment (review UX-ui U12: live): (tau from, value, early) — early:
        # set before any signal reached the plane, so the rule saw that value alone
        self.det_hist = {k: [(0.0, float(p[k]), True)] for k in ("mu_w", "mu_ms", "W0")}
        super().__init__(p, seed, emit)
        # the world's parameters are this world's own: r12's fixed path mark and flux are not among them (the header's
        # parameters seed the player's «new world» form; with them a new world without a scenario was refused, «there is
        # no parameter “mark”», found while processing review UX-ui U12)
        self.params = {k: v for k, v in self.params.items() if k in SCHEMA.by_id}
        g = self.g
        self.z_lead = 0.0 if self.free else self.geo.z_src
        self.D = float(self.zL - self.z_lead)          # the flight from the leading packet's centre to the plane
        self.t0 = self.D / AP.V0_SPEED                 # its classical time at the mean speed
        self.t_obs = self.t_end_est                    # the observation window ends here
        self.rec = {k: [] for k in ("tau", "J", "rho", "d2", "click")}
        self.sent = 0
        # the joint distribution: J(x, t) in time bins of tbin steps and x bins over the screen (the bins from the set-up's
        # t0, not from the window's end, which is a consequence of the run: review B4-5)
        self.tbin = max(1, int(math.ceil(self.t0 / (ROWS_PER_T0 * self.dt))))
        xs = g.axes[0]
        on = np.flatnonzero(self.on_screen)
        self.cols = max(1, int(math.ceil(len(on) / COLS_MAX)))
        self.col_lo = int(on[0])
        self.ncol = len(on) // self.cols
        self.col_x0 = float(xs[self.col_lo]) + 0.5 * (self.cols - 1) * g.d[0]
        self._jacc = np.zeros(g.shape[0])
        self._jn = 0
        self.rows = []
        self.rows_sent = 0
        self.curve_sent = 0
        # the soft detector: the same experiment with the absorbing potential as its screen
        self.det = None
        if self.soft:
            W0 = float(p["W0"]) * AP.E0
            self.W_d = self.W + AP.soft_detector(g, self.zL, W0, self.geo.edge)
            Hd = self._hamiltonian(self.live, g, self.W_d)
            self.det = S.SplitOperator(Hd, self.dt, track_absorbed=True, force_cpu=self.prop.device == "cpu",
                                       why=T("as the main run"))
            self.psi_d = self.det.put(self._packet(Hd, g))
            iz0 = int(np.searchsorted(g.axes[1], self.zL - 5 * self.geo.edge))
            self.det_region = (slice(None), slice(iz0, None))
        self._arrival_static_checks()
        self.curves = self._initial_state_rules() if self.free else None

    # --- r12's hooks ---------------------------------------------------------------------------------------------------
    def _geometry(self, p):
        h = V11.H_OF[p["grid"]]
        layer = AP.screen_layer(*AP.k_range(self.pk, 3.0))
        if self.free:
            t_end = AP.leave_time(self.fg, float(p["L"]))
            return AP.FreeGeometry(p["L"], p["sigma_x"], p["sigma_z"], h, AP.rear(self.pk), t_end, edge=float(p["edge"]),
                                   layer=layer)
        return AP.SlitGeometry(p["a"], p["d"], p["w"], p["L"], p["sigma_x"], p["sigma_z"], h, edge=float(p["edge"]),
                               back=-AP.rear(self.pk), layer=layer)

    def _layer_k(self) -> np.ndarray:
        """The state's whole spectrum (+-3 standard deviations of each packet)."""
        lo, hi = AP.k_range(self.pk, 3.0)
        return np.linspace(max(lo, 0.05 * AP.K0), hi, 7)

    def _t_end_estimate(self) -> float:
        if self.free:  # the free flight in closed form: until all but 1e-4 has crossed the plane
            return 1.02 * AP.leave_time(self.fg, self.geo.L)
        geo = self.geo
        v_slow = min(k - 2 / (2 * s) for _, _, k, s in self.pk)  # hbar = m = 1
        return (abs(geo.z_src) - AP.rear(self.pk) + geo.L + 4 * geo.sz + 2 * geo.screen_half) / v_slow

    def _starts(self, N: int) -> np.ndarray:
        """Starts drawn from |psi0|^2 = chi(x)^2 |phi(z)|^2: x normal, z by the inverse of phi's cumulative
        distribution (closed form on 40001 points: interpolation error ~1e-7 of the width)."""
        z_lead = 0.0 if self.free else self.geo.z_src
        zz = np.linspace(AP.rear(self.pk) - 9 * self.geo.sz, 9 * self.geo.sz, 40001)
        rho = np.abs(self.fg.psi(zz, 0.0)) ** 2
        cdf = np.concatenate([[0.0], np.cumsum(0.5 * (rho[1:] + rho[:-1]) * np.diff(zz))])
        cdf /= cdf[-1]
        return np.column_stack([self.rng.normal(0.0, self.geo.sx, N), np.interp(self.rng.random(N), cdf, zz) + z_lead])

    def _packet(self, H, g) -> np.ndarray:
        z_lead = 0.0 if self.free else self.geo.z_src
        chi = np.exp(-g.axes[0] ** 2 / (4 * self.geo.sx ** 2))
        phi = self.fg.psi(g.axes[1] - z_lead, 0.0)
        psi = chi[:, None] * phi[None, :]
        return psi / math.sqrt(float(np.sum(np.abs(psi) ** 2)) * g.dV)

    def _widest_angle(self) -> float:
        if self.free:  # three standard deviations of the transverse momentum
            return math.atan(3.0 / (2 * self.geo.sx * AP.K0))
        return super()._widest_angle()

    def cost_estimate(self) -> float:
        pairs = self.t_end_est / self.pair
        per_point, per_particle = V11.RATES[self.prop.device]
        steps = 2 + (self.geo.h / self._companion_step()) ** 2 + (2 if self.soft else 0)
        return pairs * (self.g.size * steps * per_point + int(self.params["n_bohm"]) * per_particle)

    def _references(self, xs):
        return {} if self.free else super()._references(xs)

    def _record(self, psi, J, tau):
        g = self.g
        dx = float(g.d[0])
        pc, d = self.prop.plane(psi, 1, self.iL, V11.FLUX_ORDER)
        r = self.rec
        r["tau"].append(tau)
        r["J"].append(float(J.sum()) * dx)
        r["rho"].append(float(np.sum(np.abs(pc) ** 2)) * dx)
        r["d2"].append(float(np.sum(np.abs(d) ** 2)) * dx)
        self._jacc += J
        self._jn += 1
        if self._jn == self.tbin:
            seg = self._jacc[self.col_lo:self.col_lo + self.ncol * self.cols] / self._jn
            self.rows.append(seg.reshape(self.ncol, self.cols).mean(axis=1))
            self._jacc[:] = 0.0
            self._jn = 0
        if self.det is not None:
            self.psi_d = self.det.step(self.psi_d, 1)
            r["click"].append(self.det.absorbed_in(self.det_region))

    def advance(self, t_target):
        self.t = t_target
        tau_t = t_target / self.tunit
        while not self.done and self.tau + self.pair <= tau_t + 1e-12:
            self._pair()
            if not self.done and self.tau >= self.t_obs:
                self._finish(T("the observation window is over"))

    def set_live(self, values):
        if self.det is None and "W0" in values and float(values["W0"]) != float(self.live["W0"]):
            raise Refusal(T("there is no soft detector in this world: there is no height W₀ to change"),
                          T("switch on “Soft detector” in the new-world form"))
        before = dict(self.live)
        signal = self._signal_so_far()
        out = super().set_live(values)
        if is_t(out) and out["$t"] == V11.NO_CHANGE["$t"]:
            return out
        notes = []
        for k in ("mu_w", "mu_ms", "W0"):
            if self.live[k] == before[k]:
                continue
            early = self.tau == 0.0 or signal[k] < EARLY
            self.det_hist[k].append((self.tau, float(self.live[k]), early))
            what = T("the soft detector") if k == "W0" else (T("Wlodarz's rule") if k == "mu_w" else
                                                              T("the Marchewka–Schuss rule"))
            notes.append(T("{what}: the wave has not reached the detector yet (< 10⁻⁶ of the probability): the "
                           "experiment is as with the new value from the very start", what=what) if early else
                         T("{what}: up to this moment computed with the old value, from now on with the new one; a "
                           "comparison that assumes one value for the whole experiment is switched off", what=what))
        if self.det is not None:
            if self.live["W0"] != before["W0"]:
                self.W_d = self.W + AP.soft_detector(self.g, self.zL, float(self.live["W0"]) * AP.E0, self.geo.edge)
                self._soft_grid_check()
            Hd = self._hamiltonian(self.live, self.g, self.W_d)
            self.det.rebuild(V=Hd.V, W=Hd.W, keep=())
        return join([out] + notes)

    def _signal_so_far(self) -> dict:
        """What has reached the detectors by now, per live detector parameter: the exponential rules' unit-strength
        intensities integrated so far (v0 ∫∫|ψ|² dx dt and (v0/k0²) ∫∫|∂ψ/∂z|² dx dt on the plane), and the probability
        the soft detector's run took or holds behind z = L − 5·edge."""
        r, dt = self.rec, self.dt
        out = {"mu_w": AP.V0_SPEED * float(np.sum(r["rho"])) * dt,
               "mu_ms": AP.V0_SPEED / AP.K0 ** 2 * float(np.sum(r["d2"])) * dt, "W0": 0.0}
        if self.det is not None:
            out["W0"] = float(self.det.absorbed_in(self.det_region)) + \
                float(self.det.density(self.psi_d)[self.det_region].sum()) * self.g.dV
        return out

    def _strength(self, key, tau) -> np.ndarray:
        """A detector parameter at the run's sample times: the value in force when each sample was recorded (a sample
        at the moment of a change belongs to the value before it)."""
        h = self.det_hist[key]
        vals = np.array([v for _, v, _ in h])
        if len(h) == 1:
            return np.full(len(tau), vals[0])
        return vals[np.searchsorted(np.array([t for t, _, _ in h[1:]]), np.asarray(tau), side="left")]

    def _one_value(self, key):
        """The value a detector parameter had for the whole signal (every change made before the signal reached it),
        or None when it changed while the signal arrived."""
        h = self.det_hist[key]
        return h[-1][1] if all(early for _, _, early in h) else None

    def _screen(self):
        super()._screen()
        self._send_arrival()

    # --- the rules -----------------------------------------------------------------------------------------------------
    def _series(self):
        """Every rule's density on the run's sample times (units of the computation), from what was recorded."""
        r = self.rec
        tau = np.asarray(r["tau"])
        dt = self.dt
        J = np.asarray(r["J"])
        out = {"tau": tau, "flux": J}
        C = self._cum_flux(tau, J)
        if self.free:  # Bohm's first-arrival law in free flight: the running maximum of the flux's integral
            A = np.maximum.accumulate(np.maximum(C, 0.0))
            out["bohm_law"] = np.diff(np.concatenate([[0.0], A])) / dt
        v0, k0 = AP.V0_SPEED, AP.K0
        for key, lam in (("wlodarz", DET.wlodarz_intensity(np.sqrt(np.asarray(r["rho"])), self._strength("mu_w", tau) * v0)),
                         ("ms", DET.marchewka_schuss_intensity(np.sqrt(np.asarray(r["d2"])),
                                                               self._ms_lambda0p(self._strength("mu_ms", tau))))):
            Lam = np.cumsum(lam) * dt  # the first click falls in step i with probability e^{-Lam_{i-1}} - e^{-Lam_i}
            surv = np.exp(-Lam)
            out[key] = np.diff(np.concatenate([[1.0], surv])) * -1 / dt
            out[key + "_none"] = float(surv[-1]) if len(surv) else 1.0
        if self.det is not None:
            clicks = np.asarray(r["click"])
            out["soft"] = np.diff(np.concatenate([[0.0], clicks])) / dt
        return out

    @staticmethod
    def _cum_flux(tau, J):
        """int_0^t J by the trapezoid rule from J(0) = 0 (review B4-7: the rectangle sum ran dt/2 ahead)."""
        if not len(J):
            return np.zeros(0)
        return cumulative_trapezoid(np.concatenate([[0.0], J]), np.concatenate([[0.0], tau]))

    def _send_arrival(self):
        n = len(self.rec["tau"])
        if n == self.sent and len(self.rows) == self.rows_sent:
            return
        s = self._series()
        sl = slice(self.sent, n)
        keys = [k for k in ("flux", "bohm_law", "wlodarz", "ms", "soft") if k in s]
        blobs = {k: np.asarray(s[k][sl], np.float32) for k in keys}
        blobs["tau"] = np.asarray(s["tau"][sl], np.float32)
        if len(self.rows) > self.rows_sent:
            blobs["rows"] = np.asarray(self.rows[self.rows_sent:], np.float32).ravel()
        meta = {"type": "arrival", "t": self.t, "from": self.sent, "n": n - self.sent, "keys": keys,
                "row_from": self.rows_sent, "row_n": len(self.rows) - self.rows_sent, "ref_n": 0}
        if self.curves is not None:  # the initial state's rules, revealed as the run's time reaches them (B4-5)
            c = self.curves
            upto = int(np.searchsorted(c["tau"], self.tau, side="right"))
            if upto > self.curve_sent:
                for k_ in ("tau", "abk", "sc", "abr"):
                    blobs["ref_" + k_] = np.asarray(c[k_][self.curve_sent:upto], np.float32)
                meta["ref_n"] = upto - self.curve_sent
                self.curve_sent = upto
        self.sent, self.rows_sent = n, len(self.rows)
        self._msg(meta, blobs)

    @staticmethod
    def _ms_lambda0p(mu):
        """Das & Struyve's lambda0' for the strength mu_ms: (4 lambda0' eps / pi) |d psi/dz|^2 = mu (v0 / k0^2)
        |d psi/dz|^2 with eps = hbar/m = 1, so lambda0' = pi mu v0 / (4 k0^2) = mu / 8 in these units."""
        return math.pi * np.asarray(mu, float) * AP.V0_SPEED / (4 * AP.K0 ** 2)

    def _initial_state_rules(self):
        """Free flight: the rules that are functionals of the initial state (ABK, semiclassical, absorbing boundary),
        computed from its momentum amplitude for the flight D from the leading packet to the plane."""
        lo, hi = AP.k_range(self.pk)
        k = np.linspace(lo, hi, K_N)
        phi = self.fg.phi(k)
        tau = np.linspace(0.0, self.t_obs, CURVE_N)
        kappa = float(self.params["kappa"]) * AP.K0
        abk = AT.kijowski(phi, k, self.D, tau)
        tn = np.linspace(-self.t_obs, 0.0, 801)
        abk_neg = float(np.trapezoid(AT.kijowski(phi, k, self.D, tn), tn))
        # the semiclassical rule in k, exact: bin averages of its cumulative distribution (review B4-2: samples of its
        # density alias on a train); k sampled well below 2 pi / the state's extent
        extent = max(z0 for _, z0, _, _ in self.pk) - AP.rear(self.pk) + 10 * self.geo.sz
        nk = max(20001, int(math.ceil(40 * (hi - lo) * extent / (2 * math.pi))))
        self.sc_rule = AT.Semiclassical(self.fg.phi, self.D, lo, hi, nk)
        h = tau[1] - tau[0]
        sc = self.sc_rule.bin_density(np.concatenate([[tau[0] - 0.5 * h], tau + 0.5 * h]))
        abr = DET.abr_density(phi, k, self.D, kappa, tau)
        return {"tau": tau, "abk": abk, "sc": sc, "abr": abr, "abk_neg": abk_neg,
                "abr_total": DET.abr_total(phi, k, kappa), "k_lo": lo}

    # --- checks --------------------------------------------------------------------------------------------------------
    def _arrival_static_checks(self):
        g = self.g
        # the run starts from the state the rules are computed for: its longitudinal momentum distribution
        psi0 = self.prop.get(self.psi)
        chi = np.exp(-g.axes[0] ** 2 / (4 * self.geo.sx ** 2))
        chi /= math.sqrt(float(np.sum(chi ** 2)) * g.d[0])
        phi_z = (chi[None, :] @ psi0)[0] * g.d[0]
        z = g.axes[1] - self.z_lead
        kz = 2 * math.pi * np.fft.fftfreq(len(z), g.d[1])
        ft = np.fft.fft(phi_z) * g.d[1] / math.sqrt(2 * math.pi) * np.exp(-1j * kz * z[0])
        P_run, P_cf = np.abs(ft) ** 2, np.abs(self.fg.phi(kz)) ** 2
        dev = float(np.max(np.abs(P_run - P_cf)) / P_cf.max())
        self._check("arr_state", T("Initial state: the momentum distribution along the flight against the exact one"), dev,
                    None, "", ok=dev < 1e-3, group=ARRIVAL,
                    note=T("|ψ̃(k_z)|² of the run's initial wave (the FFT in z of its projection on the transverse "
                           "packet) against the closed form of the superposition of Gaussian packets the rules are "
                           "computed from; as a fraction of the peak; the window cuts the amplitude's tails "
                           "(e^(−(z/2σz)²) ~ 10⁻⁴ at the edges), the target is < 10⁻³"))
        if self.det is not None:
            self._soft_grid_check()

    def _soft_grid_check(self):
        """The soft detector's absorber resolved by the grid, for the highest W₀ it has had (live since U12)."""
        g = self.g
        W0 = max(v for _, v, _ in self.det_hist["W0"]) * AP.E0
        kmax = math.pi / g.d[1]
        k_hi = AP.k_range(self.pk, 6.0)[1]
        q = (k_hi ** 4 + 4 * W0 ** 2) ** 0.25
        self._check("soft_grid", T("The soft detector is resolved by the grid: |q|/k_max"), q / kmax, None, "",
                    ok=q / kmax < 0.8 and self.geo.edge >= g.d[1] * (1 - 1e-9), group=V11.COMPUTATION,
                    note=T("the wave in the absorber: q = √(k² + 2imW₀/ħ²), |q| = {q:.3g} λ⁻¹ at k = {k:.3g} λ⁻¹ (the "
                           "top of the spectrum) and the largest height W₀ = {W} E₀ the experiment had, k_max = π/step "
                           "= {kmax:.3g} λ⁻¹; less than {lim} is needed", q=q, k=k_hi, W=W0 / AP.E0, kmax=kmax,
                           lim=0.8))

    def _finish(self, why):
        if self._jn:  # the last, partial time bin of J(x, t) (review B4-8)
            seg = self._jacc[self.col_lo:self.col_lo + self.ncol * self.cols] / self._jn
            self.rows.append(seg.reshape(self.ncol, self.cols).mean(axis=1))
            self._jacc[:] = 0.0
            self._jn = 0
        self._send_arrival()
        super()._finish(why)
        s = self._series()
        res = {"t0_units": self.t0, "D": self.D, "tau_obs": self.t_obs,
               "none": {"wlodarz": s["wlodarz_none"], "ms": s["ms_none"]}}
        J, tau, dt = s["flux"], s["tau"], self.dt
        res["flux_total"] = float(J.sum() * dt)
        res["backflow"] = float(np.clip(-J, 0, None).sum() * dt)
        if self.det is not None:
            clicks = self.rec["click"][-1] if self.rec["click"] else 0.0
            rem = float(self.det.density(self.psi_d)[self.det_region].sum()) * self.g.dV
            res["soft"] = {"clicks": clicks, "inside": rem, "reflected": 1.0 - clicks - rem}
        if self.curves is not None:
            res["abk_neg"] = self.curves["abk_neg"]
            res["abr_total"] = self.curves["abr_total"]
        res["rules"] = self._rule_stats(s)
        self.arrival_final = res
        self._msg({"type": "arrival_result", "t": self.t, **res})
        self._arrival_checks(s, res)

    def _rule_stats(self, s) -> dict:
        """Each rule's probability within the observation window, its mean arrival time and spread (units of the
        computation): sums over the run's steps, the trapezoid rule over the curves of the initial state, the
        ensemble's hit times."""
        def moments(tau, P, w):
            tot = float(np.sum(P * w))
            if tot <= 0:
                return {"total": tot, "mean": None, "sd": None}
            m = float(np.sum(tau * P * w) / tot)
            return {"total": tot, "mean": m, "sd": float(math.sqrt(max(np.sum((tau - m) ** 2 * P * w) / tot, 0.0)))}
        out = {}
        for k in ("flux", "bohm_law", "wlodarz", "ms", "soft"):
            if k in s and len(s[k]):
                out[k] = moments(s["tau"], s[k], self.dt)
        if self.curves is not None:
            c = self.curves
            w = np.gradient(c["tau"])  # trapezoid weights on the uniform grid, up to the half-weights at the ends
            w[0] *= 0.5
            w[-1] *= 0.5
            for k in ("abk", "abr"):
                out[k] = moments(c["tau"], c[k], w)
            tot, mean, sd = self.sc_rule.moments(float(c["tau"][-1]))  # exact in k (B4-2)
            out["sc"] = {"total": tot, "mean": mean, "sd": sd}
        hits = self.hit_t[self.fate == 1] / self.tunit
        out["bohm"] = {"total": len(hits) / len(self.fate), "mean": float(hits.mean()) if len(hits) else None,
                       "sd": float(hits.std()) if len(hits) > 1 else None}
        return out

    def _arrival_checks(self, s, res):
        tau, J, dt = s["tau"], s["flux"], self.dt
        grp = ARRIVAL
        n_tot = len(self.fate)
        if self.free:
            Jx = self.fg.current(self.D, tau)
            dev = float(np.max(np.abs(J - Jx)) / np.max(np.abs(Jx)))
            bx = float(np.clip(-Jx, 0, None).sum() * dt)
            self._check("arr_flux_exact", T("Flux through the plane against the exact free evolution"), dev, None, "",
                        ok=dev < 1e-2, group=grp,
                        note=T("J(t) = ∫ j_z(x, L, t) dx of the run against the current of the exact solution (a "
                               "superposition of Gaussian packets); the largest difference as a fraction of the peak; "
                               "backflow: {b:.3g} (exactly {bx:.3g}) of the probability; the target is < 1 % (as for the "
                               "check «Grid and time step»)", b=res["backflow"], bx=bx))
            rho_x = np.abs(self.fg.psi(self.D, tau)) ** 2
            rho = np.asarray(self.rec["rho"])
            dev = float(np.max(np.abs(rho - rho_x)) / rho_x.max())
            self._check("arr_plane_psi", T("ψ on the detecting plane against the exact one: ∫|ψ(x, L, t)|² dx"), dev, None,
                        "", ok=dev < 1e-2, group=grp,
                        note=T("the input of the exponential rules (Wlodarz, Marchewka–Schuss); the largest difference "
                               "as a fraction of the peak"))
            if self.curves is not None:
                c = self.curves
                got = float(np.trapezoid(c["abr"], c["tau"]))
                self._check("arr_abr_identity", T("Absorbing boundary: the curve's quadrature, ∫Π dt over the window "
                                                  "against ∫|ψ̃|²(1 − R_k) dk"), got, c["abr_total"], "", tol=2e-3,
                            group=grp,
                            note=T("both sides come from the formula of images (Parseval's identity), so the comparison "
                                   "checks the quadratures in t and k over the observation window, not the rule itself "
                                   "(R_k = (k − κ)²/(k + κ)², κ = {kappa} k₀; less than 1e-4 is left beyond the window). "
                                   "The rule itself is checked in the engine's tests against an independent "
                                   "Crank–Nicolson solution with a Robin condition (review B4-9)",
                                   kappa=float(self.params["kappa"])))
                tot = float(np.trapezoid(c["abk"], c["tau"]))
                self._check("arr_abk_norm", T("Aharonov–Bohm–Kijowski: ∫Π dt at t > 0 and the weight at t < 0"),
                            tot + c["abk_neg"], 1.0, "", tol=2e-3, info=True, group=grp,
                            note=T("at t > 0 (the window): {pos:.6f}, at t < 0: {neg:.2e} (after Das and Nöth, the "
                                   "probability «not detected»); the sum must be 1", pos=tot, neg=float(c["abk_neg"])))
        hits_t = self.hit_t[self.fate == 1] / self.tunit
        n = len(hits_t)
        if n >= 20:
            C = self._cum_flux(tau, J)
            law = np.maximum.accumulate(np.maximum(C, 0.0)) if self.free else self._cum_flux(tau, np.clip(J, 0, None))
            F = law / law[-1]
            emp = np.searchsorted(np.sort(hits_t), tau, side="right") / n
            Dks = float(np.max(np.abs(emp - F)))
            crit = 1.95 / math.sqrt(n)
            self._check("arr_bohm_times", T("First arrival times of the Bohm particles against the law "
                                            "(Kolmogorov–Smirnov)"), Dks, None, "", ok=Dks < crit, group=V11.BOHM,
                        note=T("{n:d} particles of {N:d}; {law}; the critical value at {p} %: {c}/√n = {crit:.3g}", n=n,
                               N=n_tot, p=99.9, c=1.95, crit=crit,
                               law=T("free flight: the law of first arrival is the running maximum of ∫J dt (the "
                                     "trajectories do not cross)") if self.free else
                               T("behind the slits: the flux into the screen (trajectories that came back through the "
                                 "plane are not counted)")))
        if self.det is not None and self.free and self._one_value("W0") is None:
            self._check("arr_soft_reflection", T("Soft detector: the reflected fraction against the stationary theory"),
                        None, None, "", info=True, group=grp,
                        note=T("the height W₀ changed while the wave was already at the detector: the stationary theory "
                               "for one height does not apply to this experiment (the changes are in the events)"))
        elif self.det is not None and self.free:
            Rref = self._soft_reflection_reference()
            Rrun = res["soft"]["reflected"]
            tol = SOFT_REL_TOL * Rref + 2e-4
            self._check("arr_soft_reflection", T("Soft detector: the reflected fraction against the stationary theory"),
                        Rrun, Rref, "", tol=tol / max(Rref, 1e-12), ok=abs(Rrun - Rref) <= tol, group=grp,
                        note=T("the run: 1 − absorbed by the detector − left in it; the theory: R(k) of transfer "
                               "matrices for the detector's profile −iW(z) (a step W₀ = {W} E₀ with an edge of {e} λ and "
                               "an absorbing layer behind it), averaged over |ψ̃(k)|²; a sharp step would give "
                               "{sharp:.3g}; tolerance 10 % + 2e-4 (what did not arrive within the window)",
                               W=float(self._one_value("W0")), e=self.geo.edge, sharp=self._sharp_reflection()))
        if self.det is not None:
            lost = abs(self.det.norm(self.psi_d) + float(self.det.absorbed().sum()) - 1.0)
            self._check("arr_det_norm", T("The run with the soft detector: norm + absorbed = 1"), lost, 0.0, "", tol=1e-9,
                        ok=lost < 1e-9, group=V11.COMPUTATION)
        if self.free and self.params["state"] == "train":
            self._train_check(s)

    def _soft_reflection_reference(self) -> float:
        lo, hi = AP.k_range(self.pk)
        k = np.linspace(max(lo, 1e-3), hi, 1201)
        W0, e = self._one_value("W0") * AP.E0, self.geo.edge
        Wl = self.geo.screen_W * AP.E0
        gap = AP.AP11.SCREEN_GAP
        width = float(self.g.axes[1][-1] - self.zL) - gap

        def prof(z):  # the step at the plane, the screen's layer from SCREEN_GAP behind it
            z = np.asarray(z, float)
            return AP.soft_profile(W0, e)(z) - 1j * Wl * np.clip((z - gap) / width, 0.0, 1.0) ** 2
        R = []
        for nsl in (1500, 3000):
            _, Rk = transmission_profile(0.5 * k * k, prof, -10 * e, gap + width, nsl, return_r=True)
            R.append(Rk)
        Rk = R[1] + (R[1] - R[0]) / 3  # Richardson: the staircase's error falls as 1/n^2
        w = np.abs(self.fg.phi(k)) ** 2
        return float(np.trapezoid(w * Rk, k) / np.trapezoid(w, k))

    def _sharp_reflection(self) -> float:
        lo, hi = AP.k_range(self.pk)
        k = np.linspace(max(lo, 1e-3), hi, 1201)
        w = np.abs(self.fg.phi(k)) ** 2
        return float(np.trapezoid(w * DET.step_reflection(k, self._one_value("W0") * AP.E0), k) / np.trapezoid(w, k))

    def _train_check(self, s):
        """Das & Struyve 2021: with the train, the flux shows N equal peaks; Wlodarz's rule damps them by exp(-mu / N) each."""
        N, sep = int(self.params["n_train"]), float(self.params["sep"])
        tau = s["tau"]
        t_j = (self.D + sep * np.arange(N)) / AP.V0_SPEED
        half = 0.5 * sep / AP.V0_SPEED
        peaks = {k: np.array([s[k][(tau > tj - half) & (tau < tj + half)].max() for tj in t_j]) for k in ("flux", "wlodarz")}
        r_flux = peaks["flux"][1:] / peaks["flux"][:-1]
        r_w = peaks["wlodarz"][1:] / peaks["wlodarz"][:-1]
        mu = self._one_value("mu_w")
        if mu is None:
            self._check("arr_train", T("Train of packets: the peaks of Wlodarz's rule fade as e^(−λ₀/N)"), None, None, "",
                        info=True, group=ARRIVAL,
                        note=T("the strength λ₀ changed while the train was already arriving: the comparison with "
                               "e^(−λ₀/N) for one strength does not apply to this experiment (the changes are in the "
                               "events)"))
            return
        expect = math.exp(-mu / N)
        dev = float(np.max(np.abs(r_w / expect - 1)))
        self._check("arr_train", T("Train of packets: the peaks of Wlodarz's rule fade as e^(−λ₀/N)"), dev, None, "",
                    info=True, group=ARRIVAL,
                    note=T("ratios of neighbouring peaks: flux {flux} (≈ 1 expected, corrected for the spreading), "
                           "Wlodarz {w} against e^(−λ₀/N) = {e:.3f} (Das & Struyve 2021, eqs. 24–25); the largest "
                           "difference {dev:.2f} %", flux=join([round(float(v), 3) for v in r_flux], "; "),
                           w=join([round(float(v), 3) for v in r_w], "; "), e=expect, dev=100 * dev))

    # --- the scene -------------------------------------------------------------------------------------------------------
    def engine_modules(self):
        mods = ["core.quantum.schrodinger_nd", "core.quantum.schrodinger1d", "core.quantum.transfer",
                "core.quantum.particles", "core.backend", "theories.interpretations.bohm",
                "theories.interpretations.arrival_times", "theories.models.detection"]
        if not self.free:
            mods += ["theories.approx.paraxial", "theories.approx.kirchhoff"]
        return mods

    def _plate_obj(self):
        o = super()._plate_obj()
        if self.free:
            o["visible"] = False
            o["label"] = T("No plate: free flight")
        return o

    def header(self):
        hd, extra = super().header()
        hd["title"] = TITLE
        hd["text"] = T("A particle's packet flies to a detecting plane, freely or through two slits. The run solves the "
                       "Schrödinger equation on the plane (x, z) and records on the detecting plane the current, the "
                       "wave and its derivative at every moment. From them and from the initial state the run computes "
                       "the distribution of the arrival time by each rule: the quantum flux, the first arrivals of the "
                       "Bohm particles, Aharonov–Bohm–Kijowski, the semiclassical rule, the absorbing boundary, the "
                       "exponential rules of Wlodarz and of Marchewka–Schuss, and the soft detector (a second run with "
                       "an absorbing potential). Quantum mechanics does not fix one rule: where they diverge, an "
                       "experiment could tell them apart.")
        for o in hd["scene3d"]["objects"]:
            if o["id"] == "screen":
                o["label"] = T("Detecting plane (z = {L} λ): the flux accumulated over the experiment", L=self.geo.L)
        approx = list(hd["approximations"])
        if self.free:
            replaced = (V11.APPROX_SLITS["$t"], V11.APPROX_WALL["$t"])
            approx = [a for a in approx if not (is_t(a) and a["$t"] in replaced)]
            approx.insert(0, T("nothing depends on y: the Schrödinger equation is solved on the plane (x, z); the 3-D "
                               "wave is the exact product ψ(x, z, t)·η(y, t) with a free Gaussian η (closed form)"))
            approx.append(T("ABK, the semiclassical rule and the absorbing boundary: for free flight and a separable state "
                            "(the transverse packet is a spectator); the exponential rules are generalised to the plane "
                            "as a Poisson flow with the density λ(x, t), their time is an integral over x"))
        approx.append(T("the plane's detector in the main run is an absorbing layer without reflection (an ideal plane "
                        "of arrival); the rules of «detectors» are computed separately"))
        hd["approximations"] = approx
        rules = ["flux", "bohm"] + (["bohm_law", "abk", "sc", "abr"] if self.free else []) + ["wlodarz", "ms"] + \
                (["soft"] if self.soft else [])
        hd["arrival"] = {"scene": "free" if self.free else "slits", "state": self.params["state"], "t0_units": self.t0,
                         "D": self.D, "dt": self.dt, "rules": rules,
                         "rows": {"tbin_units": self.tbin * self.dt, "x0": self.col_x0, "dx": float(self.g.d[0]) * self.cols,
                                  "n": self.ncol},
                         "params": {k: self.params[k] for k in ("kappa", "mu_w", "mu_ms", "W0", "n_train", "sep")}}
        hd["geometry"]["scene"] = hd["arrival"]["scene"]
        return hd, extra


VIZ = {
    "id": "r13_arrival_times_2d",
    "title": TITLE,
    "summary": T("When does the particle arrive at the detector? A packet flies to a plane freely or through two slits; "
                 "the run solves the Schrödinger equation and, from the record on the plane and the initial state, "
                 "computes the distribution of the arrival time by the quantum flux, the Bohm trajectories, "
                 "Aharonov–Bohm–Kijowski, the semiclassical rule, the absorbing boundary, the rules of Wlodarz and of "
                 "Marchewka–Schuss, and the soft detector."),
    "purpose": T("Quantum mechanics does not fix the arrival time uniquely; the world shows where the rules agree (far "
                 "from the source) and where they diverge: near the source, for a train of packets, under backflow, "
                 "behind two slits."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
    "audience": "research",
    "section": "quantum",
    "ui": "full",
    "teaser": T("Several rules of the arrival time on one run: they agree far from the source and diverge near it."),
    "question": T("When does a particle arrive at a detector? Where do the rules of the arrival time agree, and "
                  "where do they diverge: near the source, for a train of packets, under backflow, behind two "
                  "slits?"),
    # the prior art found in the checks of plan §3 (lfphys/sources/priorart_2026-11-12_*.md): two or three
    # targeted searches per item, not a survey; every novelty a hypothesis (AGENTS.md rule 11)
    "prior_art": [
        {"ref": "Ayatollah Rafsanjani et al., Commun. Phys. 6, 195 (2023)", "url": "https://arxiv.org/abs/2301.02641"},
        {"ref": "Das & Struyve, Phys. Rev. A 104, 042214 (2021)", "url": "https://arxiv.org/abs/2105.14744"},
        {"ref": "Das, Deckert, Kellers, Krekels & Struyve, Ann. Phys. 479, 170054 (2025)",
         "url": "https://arxiv.org/abs/2211.13362"},
        {"ref": "Cavendish & Das, Phys. Rev. A 112, 062217 (2025)",
         "url": "https://journals.aps.org/pra/abstract/10.1103/332p-4nl1"},
        {"ref": "Jozani & Tumulka, Phys. Rev. Research 8, 033072 (2026)", "url": "https://arxiv.org/abs/2603.22044"},
        {"ref": "Paterek & Goussev, Phys. Rev. Lett. 136, 090202 (2026)", "url": "https://arxiv.org/abs/2511.10155"},
    ],
    "status": "hypothesis",
    "related": [],
    # what the public site plays (DESIGN §4.1): ~8-9 kB of gzip per frame measured
    "recordings": [
        {"id": "gauss", "preset": "gauss", "seconds": 20, "fps": 10,
         "speed": None, "seed": 1, "script": [], "poster": 18},
        {"id": "near", "preset": "near", "seconds": 20, "fps": 10,
         "speed": None, "seed": 1, "script": [], "poster": 18},
    ],
}
