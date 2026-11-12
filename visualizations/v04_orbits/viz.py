# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v04: orbits and clocks - a test body around a central mass in general relativity and in Newton's gravity.

What the run computes (README.md of this folder has the model in full):
* the body's orbit from its initial data: in GR the exact Schwarzschild geodesic (lfphys.core.gravity.orbit_stream:
  the Binet equation with coordinate and proper time, events located by the integrator), in a Newton world the
  Newtonian orbit (lfphys.theories.approx.newton.integrate_body);
* the orbit is computed ahead in chunks and revealed as the world's coordinate time reaches it; a live change of the
  initial data or an action (a boost, a new launch) starts a new segment at the current moment and withdraws the
  computed future;
* the body's clock (proper time) next to the distant observer's coordinate time, and its rate dtau/dt;
* the run's own measurements: periapses and apoapses, the advance of the periapsis per orbit (the angle between
  successive periapses), periods, the conservation of e and l, the fall through the horizon;
* checks against closed forms: the exact elliptic integral of the advance, the weak-field formula 6 pi M/p (leading
  order), dtau/dt = sqrt(1 - 3M/r) and Kepler's period on circular orbits, the cycloid of a radial fall, the
  impact speed, an independent second integration scheme; in a Newton world energy, angular momentum, Kepler's
  period and the closed ellipse.
"""

from __future__ import annotations

import math

import numpy as np
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

from lfphys.core.constants import AU, C, DAY, GM_SUN, R_SUN
from lfphys.core.gravity import kerr, orbit_stream, orbits
from lfphys.i18n import T, text_of
from lfphys.theories.approx import ppn

from .engine.body import GRTrack, NewtonTrack

# Mercury: NASA NSSDCA Mercury Fact Sheet, J2000 mean elements (a = 0.38709893 AU, e = 0.20563069); the GR perihelion
# advance 42.98"/century: Will, Living Rev. Relativ. 17, 4 (2014), Eq. (65) with gamma = beta = 1 and no solar J2.
# Both checked against the source texts: lfphys/sources/verification_2026-10-23.md, items 1 and 2.
MERCURY_A_AU = 0.38709893
MERCURY_ECC = 0.20563069
MERCURY_GR_ARCSEC_PER_CENTURY = 42.98
M_SUN_LEN = GM_SUN / C**2
MERCURY_R0 = MERCURY_A_AU * (1.0 - MERCURY_ECC) * AU / M_SUN_LEN   # perihelion in units of GM_sun/c^2
MERCURY_K = math.sqrt(1.0 + MERCURY_ECC)  # perihelion speed / circular speed (vis-viva; GR differs by O(M/r) ~ 3e-8)
CENTURY_S = 36525.0 * DAY
GHOST_SLICE_S = 0.03  # wall seconds of ghost catch-up per world step (review V4-16)
# the apsis of an orbit with relative spread s = (r_apo - r_peri)/r_peri is located to ~APSIS_PHASE/s rad (du/dphi
# ~ s at its zero; the integration error of du/dphi ~1e-15); measured in tests, used in the tolerances
APSIS_PHASE = 1e-14
APSIS_PHASE_NEWTON = 2e-13  # Newton: the apsis direction ~ (integration error ~1e-12 relative)/eccentricity
ARCSEC = math.pi / 180.0 / 3600.0

LAWS = [("GR", T("GR (Schwarzschild)")), ("newton", T("Newton (approximation)"))]
LIVE_INIT = ("r0", "speed", "angle")
G_LAWS, G_BODY, G_LAUNCH, G_VIEW = T("Laws"), T("Central body"), T("Launch of the body"), T("Display")


def _p(*a, **k):
    return Param(*a, **k)


def _join(items, sep="; "):
    """Several texts as one (a nested T: each part stays translatable)."""
    items = [x for x in items if x]
    if not items:
        return None
    out = items[0]
    for x in items[1:]:
        out = T("{a}; {b}", a=out, b=x) if sep == "; " else T("{a}, {b}", a=out, b=x)
    return out


SCHEMA = Schema([
    _p("gravity", T("Law of gravitation"), "select", "GR", group=G_LAWS, options=LAWS, standard="GR",
       help=T("GR is the accepted theory. Newtonian gravity is the approximation of a weak field and low speeds; a "
              "world with it is flagged as modified physics.")),
    _p("mass_msun", T("Mass of the central body, M☉"), "float", 10.0, group=G_BODY, min=1.0, max=1e9,
       log=True, help=T("The length GM/c² (the unit M) and the time GM/c³ follow from this mass; GM☉ is the IAU 2015 "
                        "B3 nominal value.")),
    _p("radius_km", T("Radius of the body, km (0: a black hole)"), "float", 0.0, group=G_BODY, min=0.0, max=1e8,
       help=T("In GR the radius must be larger than 2M (otherwise the body is a black hole: set 0). The exterior "
              "field of any spherical body is the Schwarzschild solution (Birkhoff's theorem).")),
    _p("r0", T("Initial radius r₀, M (GM/c²)"), "float", 20.0, group=G_LAUNCH, min=2.1, max=1e8, log=True,
       live=True, help=T("The starting radius in units of M = GM/c². A change applies at once: the body is launched "
                         "again at the world's current moment, from its current direction to the centre.")),
    _p("speed", T("Speed, fraction of the circular speed"), "float", 1.2, group=G_LAUNCH, min=0.0, max=1.6,
       live=True,
       help=T("The speed measured by a static observer at the starting point, as a fraction of the circular-orbit "
              "speed there: √(M/(r−2M)) in GR, √(GM/r) for Newton. Below 3M there are no circular orbits: there it "
              "is a fraction of the speed of light.")),
    _p("angle", T("Direction of the velocity, ° from the tangent (+ outward)"), "float", 0.0, group=G_LAUNCH,
       min=-90.0, max=90.0, live=True, help=T("0: along the tangent (anticlockwise), +90: straight away from the "
                                              "centre, −90: straight towards the centre.")),
    _p("ghost", T("Ghost of the other theory"), "bool", False, group=G_VIEW, live=True,
       help=T("The orbit from the same initial data (the same r₀ and speed) under the other theory: Newton in a GR "
              "world, GR in a Newton world. Dashed; it does not affect the world.")),
    _p("time_units", T("Time on the panels"), "select", "si", group=G_VIEW, live=True,
       options=[("si", T("seconds (hours, days, years)")), ("geo", T("units of GM/c³"))]),
], presets={
    "default": {"label": T("Black hole {m} M☉: a rosette (periapsis {rp}M)", m=10, rp=20), "params": {}},
    "mercury": {"label": T("Mercury at the Sun (weak field, {adv}″ per century)", adv=43),
                "params": {"gravity": "GR", "mass_msun": 1.0, "radius_km": R_SUN / 1e3, "r0": MERCURY_R0,
                           "speed": MERCURY_K, "angle": 0.0},
                "note": T("a = {a:.8g} AU, e = {e:.8g} (NASA NSSDCA, J2000), the start at the perihelion; the GR "
                          "reference {adv}″ per century: Will 2014, Living Rev. Relativ. 17, 4, Eq. (65)",
                          a=MERCURY_A_AU, e=MERCURY_ECC, adv=MERCURY_GR_ARCSEC_PER_CENTURY)},
    "neutron_star": {"label": T("Neutron star: strong precession"),
                     "params": {"gravity": "GR", "mass_msun": 1.4, "radius_km": 12.0, "r0": 10.0, "speed": 1.12,
                                "angle": 0.0},
                     "note": T("illustrative: {m} M☉, R = {r} km ≈ {rm}M; periapsis {rp}M", m=1.4, r=12, rm=5.8,
                               rp=10)},
    "bh_isco": {"label": T("Black hole: a circular orbit near the ISCO ({r}M)", r=6.2),
                "params": {"gravity": "GR", "mass_msun": 10.0, "radius_km": 0.0, "r0": 6.2, "speed": 1.0,
                           "angle": 0.0}},
    "plunge": {"label": T("Plunge inside the ISCO ({r}M, speed −{dv} %)", r=5.5, dv=0.5),
               "params": {"gravity": "GR", "mass_msun": 10.0, "radius_km": 0.0, "r0": 5.5, "speed": 0.995,
                          "angle": 0.0}},
    "radial": {"label": T("Radial fall from rest at {r}M (cycloid)", r=20),
               "params": {"gravity": "GR", "mass_msun": 10.0, "radius_km": 0.0, "r0": 20.0, "speed": 0.0,
                          "angle": 0.0}},
    "newton_ellipse": {"label": T("Newton: a closed ellipse (ghost: GR)"),
                       "params": {"gravity": "newton", "mass_msun": 10.0, "radius_km": 0.0, "r0": 20.0,
                                  "speed": 1.2, "angle": 0.0, "ghost": True}},
})

KIND_TEXT = {"bound": T("bound (an ellipse with precession)"), "circular": T("circular"),
             "plunge": T("a plunge into the centre"), "escape": T("escape to infinity"),
             "radial_fall": T("radial: a fall"), "radial_escape": T("radial: escape")}
KIND_TEXT_NEWTON = {**KIND_TEXT, "bound": T("bound (a Kepler ellipse)")}
LAW_SHORT = {"GR": T("GR"), "newton": T("Newton")}


def _kind_text(kind, law):
    return (KIND_TEXT if law == "GR" else KIND_TEXT_NEWTON).get(kind, kind)


END_TEXT = {"horizon": T("a fall through the horizon"), "surface": T("an impact on the body's surface"),
            "center": T("a fall into the centre"), "escape": T("escape to infinity")}


def _due(n: int) -> bool:
    """Which periapsis / turn numbers refresh the checks (all early ones, then sparsely: the record stays small)."""
    return n <= 4 or n in (6, 11, 21, 51) or (n - 1) % 100 == 0


def _same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=0.0)
    return a == b


def _val(k, v):
    """A parameter's value as the change log shows it: yes/no, a select by its option's label, a number as a
    number (formatted by the viewer's language)."""
    if isinstance(v, bool):
        return T("yes") if v else T("no")
    p = SCHEMA.by_id[k]
    if p.type == "select":
        return dict((o[0], o[1]) for o in p.options).get(v, v)
    return v


def _angle_text(rad: float):
    a = abs(rad)
    if a < math.radians(1.0):
        return T("{v:.6g}″", v=rad / ARCSEC)
    return T("{v:.6g}°", v=math.degrees(rad))


class Simulation(BaseSimulation):
    speed_range = (1e-10, 1e18)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        p = self.params
        self.law = p["gravity"]
        self.msun = float(p["mass_msun"])
        self.gm = self.msun * GM_SUN
        self.M_m = self.gm / C**2   # metres per M
        self.T_s = self.M_m / C     # seconds per GM/c^3
        self.R = p["radius_km"] * 1e3 / self.M_m  # body radius in M; 0 = black hole (GR) / point mass (Newton)
        if self.law == "GR" and 0.0 < self.R <= 2.0:
            raise Refusal(T("radius {r:.6g} km is not larger than 2M = {rs:.6g} km: such a body is a black hole",
                            r=p["radius_km"], rs=2 * self.M_m / 1e3),
                          hint=T("set the radius to 0 (a black hole) or larger than {rs:.6g} km", rs=2 * self.M_m / 1e3))
        # special radii of the Schwarzschild geometry (the Kerr closed forms at zero spin)
        self.special = {"horizon": kerr.horizons(0.0)[0], "photon": kerr.photon_orbit(0.0),
                        "mb": kerr.marginally_bound(0.0), "isco": kerr.isco(0.0)}
        self._buf = []
        self.seg = -1
        self.track = self.ghost = None
        self.t_launch = 0.0
        init = self._launch_data(p, 0.0)
        self._start_segment(init, T("launch of the body"), launch=True, ghost_on=bool(p["ghost"]))
        dyn = self._period_estimate(self.track) or self.track.dyn
        self.default_speed = float(min(max(dyn * self.T_s / 8.0, self.speed_range[0]), self.speed_range[1]))

    # --- engine modules of this world ------------------------------------------------------------------------
    def engine_modules(self):
        gr = ["core.gravity.orbit_stream", "core.gravity.orbits", "core.gravity.kerr"]
        if self.law == "GR":
            mods = ["core.constants"] + gr + ["theories.approx.ppn"]
            if self.params["ghost"]:
                mods.append("theories.approx.newton")
        else:
            mods = ["core.constants", "theories.approx.newton"]
            if self.params["ghost"]:
                mods += gr
        return mods

    # --- initial data ------------------------------------------------------------------------------------------
    def _v_ref(self, r, law):
        """The reference speed of the 'speed' parameter: the local circular speed (GR: sqrt(M/(r - 2M)), measured by
        the static observer; below 3M, where there is no circular orbit, c) or Newton's sqrt(GM/r)."""
        if law == "GR":
            return min(math.sqrt(1.0 / (r - 2.0)), 1.0)
        return math.sqrt(1.0 / r)

    def _launch_data(self, p, phi0):
        r0 = float(p["r0"])
        if self.R > 0 and r0 <= self.R:
            raise Refusal(T("r₀ = {r0:.6g}M is inside the body (radius {R:.6g}M)", r0=r0, R=self.R),
                          hint=T("set r₀ larger than {R:.6g}M", R=self.R))
        if self.law == "GR" and r0 <= 2.0:
            raise Refusal(T("r₀ is inside the horizon"), hint=T("set r₀ larger than 2M"))
        k, alpha = float(p["speed"]), math.radians(float(p["angle"]))
        v = k * self._v_ref(r0, self.law)
        if self.law == "GR" and v >= 1.0:
            raise Refusal(T("the local speed {v:.6g} c is not below the speed of light", v=v),
                          hint=T("lower the speed"))
        v_r, v_phi = v * math.sin(alpha), v * math.cos(alpha)
        if abs(v_phi) <= 1e-12 * v:
            v_phi = 0.0  # radial launch (cos 90 deg is not exactly zero in floating point)
        return {"r0": r0, "phi0": float(phi0), "v_r": v_r, "v_phi": v_phi, "v": v, "k": k,
                "alpha": float(p["angle"]), "how": "launch"}

    def _make_track(self, law, init, t0, tau0):
        r_stop = self.R if self.R > 0 else (2.0 if law == "GR" else 0.0)
        args = (init["r0"], init["phi0"], init["v_r"], init["v_phi"])
        if law == "GR":
            if math.hypot(init["v_r"], init["v_phi"]) >= 1.0:
                raise Refusal(T("in GR the local speed must be below c"))
            if init["r0"] <= 2.0:
                raise Refusal(T("the start is inside the horizon"))
            return GRTrack(*args, t0=t0, tau0=tau0, r_stop=r_stop)
        return NewtonTrack(*args, t0=t0, tau0=tau0, r_stop=r_stop)

    def _other(self):
        return "newton" if self.law == "GR" else "GR"

    # --- segments -------------------------------------------------------------------------------------------------
    def _start_segment(self, init, reason, launch, ghost_on):
        """Build the tracks first (may raise: then nothing changes), then commit the new segment at the current t."""
        tg = self.t / self.T_s
        if launch:
            tau0 = 0.0
        else:
            tau0 = self.track.state(tg, exact=True)["tau"]
        track = self._make_track(self.law, init, tg, tau0)
        ghost, ghost_note = None, None
        if ghost_on:
            try:
                ghost = self._make_track(self._other(), init, tg, tau0)
            except ValueError as e:
                ghost_note = T("the ghost is not built: {why}", why=text_of(e))
        # commit
        self.seg += 1
        if launch:
            self.t_launch = self.t
        self.track, self.ghost, self.init = track, ghost, dict(init)
        self.seg_t0, self.seg_tau0 = self.t, tau0
        self.S = {"peri": [], "apo": [], "laps": [], "second": None, "notes": set(), "maxdev": 0.0,
                  "ghost_ends": set()}
        info = self._orbit_info(track, init)
        self.info = info
        p_est = self._period_estimate(track, init) or track.dyn
        self._msg({"type": "segment", "t": self.t, "seg": self.seg, "reason": reason, "launch": launch,
                   "law": self.law, "init": init, **info, "t_window": 4.0 * p_est * self.T_s,
                   "ghost": self._ghost_info(ghost) if ghost else None})
        self._msg({"type": "event", "t": self.t, "kind": "segment", "text": self._segment_text(reason, init, info)})
        if ghost_note:
            self._msg({"type": "notice", "t": self.t, "text": ghost_note})
        if info["kind"] == "circular" and self.law == "GR" and init["r0"] < self.special["isco"]:
            self._msg({"type": "notice", "t": self.t,
                       "text": T("The circular orbit at r₀ = {r0:.6g}M < ISCO = {isco:.6g}M is unstable: rounding "
                                 "errors (~10⁻¹⁶) grow, and the body will leave it.",
                                 r0=init["r0"], isco=self.special["isco"])})
        self.advance(self.t)  # what happens at the launch instant itself (e.g. a start at a turning point)

    def _orbit_info(self, track, init):
        """Kind of orbit and the closed-form references for this segment (the run's checks compare with them)."""
        kind = track.info["kind"]
        ti = track.info
        d = {"kind": kind, "kind_text": _kind_text(kind, self.law), "r_peri": ti.get("r_peri"),
             "r_apo": ti.get("r_apo"), "e": None, "l": None, "em1": None, "elements": None,
             "adv_exact": None, "adv_ppn": None, "adv_series2": None, "period_ref": None, "period_t_ref": None,
             "rate_circ": None, "spread": ti.get("spread"), "moving": ti.get("moving"),
             "start_turning": ti.get("start_turning"), "double_root": ti.get("double_root"),
             "nearest_root": ti.get("nearest_root"), "u_cond": None, "u_sens": None}
        if self.law == "GR":
            d.update(e=track.e, l=track.l, em1=track.em1)
            if kind == "bound":
                try:  # references from e^2 - 1 itself (no cancellation; review V4-7)
                    el = orbits.elements(track.e, abs(track.l), track.em1)
                    d["elements"] = {k: float(v) for k, v in el.items()}
                    d["elements"]["a"] = el["p"] / (1.0 - el["ecc"] ** 2)
                    d["adv_exact"] = orbits.periapsis_advance(track.e, abs(track.l), track.em1)
                    a_m = d["elements"]["a"] * self.M_m
                    d["adv_ppn"] = ppn.periapsis_advance(self.gm, a_m, el["ecc"])
                    d["adv_series2"] = orbits.advance_series(el["p"], el["ecc"], 2)
                    d["period_t_ref"] = orbits.radial_period(track.e, abs(track.l), track.em1)["t"] * self.T_s
                    cond = orbits.turning_conditioning(track.e, abs(track.l), track.em1)
                    d["u_cond"] = {"apo": float(cond[0]), "peri": float(cond[1])}
                    # how a relative change of e^2 - 1 moves each turning point: |e^2-1| / (l^2 |f'(u)| u)
                    u = orbits.turning_points(track.e, abs(track.l), track.em1)
                    l2 = track.l * track.l
                    fp = [2.0 * (u[i] - u[(i + 1) % 3]) * (u[i] - u[(i + 2) % 3]) for i in (0, 1)]
                    d["u_sens"] = {"apo": abs(track.em1) / (l2 * abs(fp[0]) * u[0]),
                                   "peri": abs(track.em1) / (l2 * abs(fp[1]) * u[1])}
                except ValueError:
                    pass
            if kind == "circular":
                r = init["r0"]
                d["rate_circ"] = math.sqrt(1.0 - 3.0 / r)
                d["period_ref"] = 2.0 * math.pi * r**1.5 * self.T_s
        else:
            ti = track.info
            if ti.get("a"):
                d["elements"] = {"a": ti["a"], "ecc": ti["ecc"], "r_peri": ti["r_peri"], "r_apo": ti["r_apo"],
                                 "p": ti["a"] * (1 - ti["ecc"] ** 2)}
                d["period_ref"] = ti["period"] * self.T_s
                d["adv_exact"] = 0.0
            d["E"] = track.E0  # specific energy in c^2 (v^2/2 - GM/r)
            d["h"] = track.h0  # specific angular momentum in M c
        return d

    def _ghost_info(self, g):
        i = dict(g.info)
        i["law"] = g.theory
        i["kind_text"] = _kind_text(i["kind"], g.theory)
        return {k: (float(v) if isinstance(v, (np.floating,)) else v) for k, v in i.items()}

    def _segment_text(self, reason, init, info):
        s = T("{reason:cap}: r = {r:.6g}M, speed {v:.6g} c ({k:.4g} of the circular speed), angle {a:.4g}°. {law}: "
              "the orbit is {kind}", reason=reason, r=init["r0"], v=init["v"], k=init["k"], a=init["alpha"],
              law=LAW_SHORT[self.law], kind=info["kind_text"])
        if info.get("r_peri") and (info["kind"] == "bound" or (info["kind"] == "escape" and (info.get("moving") or 0) <= 0)):
            s = T("{a}, periapsis {r:.6g}M", a=s, r=info["r_peri"])  # (an outward escape never passes the periapsis behind it)
        if info.get("r_apo") and info["kind"] in ("bound", "plunge", "radial_fall"):
            s = T("{a}, apoapsis {r:.6g}M", a=s, r=info["r_apo"])
        if info.get("adv_exact"):
            s = T("{a}; periapsis advance per orbit (exact formula) {adv}", a=s, adv=_angle_text(info["adv_exact"]))
        return s

    def _period_estimate(self, track, init=None):
        """A time scale of the orbit (M units) for the default speed and the plot window: 2 pi a^{3/2} (bound),
        2 pi r^{3/2} (circular); None otherwise. A display scale, not a measured or reference quantity."""
        i = track.info
        if i.get("kind") == "bound" and i.get("r_apo"):
            a = 0.5 * (i["r_peri"] + i["r_apo"])
            return 2 * math.pi * a**1.5
        if i.get("kind") == "circular":
            return 2 * math.pi * (init or self.init)["r0"] ** 1.5
        return None

    # --- live parameters ----------------------------------------------------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        new, errors = SCHEMA.coerce_live(self.params, values)
        if errors:
            raise Refusal(_join(errors))
        changed = [k for k in SCHEMA.live_ids() if not _same(new[k], self.params[k])]
        if not changed:
            return T("no change")
        desc = _join([T("{label}: {old} → {new}", label=SCHEMA.by_id[k].label, old=_val(k, self.params[k]),
                        new=_val(k, new[k])) for k in changed])
        if any(k in LIVE_INIT for k in changed):
            init = self._launch_data(new, self._phi_now())
            ghost_on = bool(new["ghost"])
            old = self.params
            self.params = new  # _start_segment reads only init and ghost_on; restored if it raises
            try:
                self._start_segment(init, T("new initial data ({what})", what=desc), launch=True, ghost_on=ghost_on)
            except ValueError:
                self.params = old
                raise
            return desc
        if "ghost" in changed:
            if new["ghost"]:
                st = self.init
                try:  # the other theory from this segment's initial data, from the segment's start
                    self.ghost = self._make_track(self._other(), st, self.seg_t0 / self.T_s, self.seg_tau0)
                except ValueError as e:
                    raise Refusal(T("the ghost is not built: {why}", why=text_of(e))) from e
                self._msg({"type": "ghost", "t": self.t, "seg": self.seg, "info": self._ghost_info(self.ghost)})
                # its past up to now (a computation about the other theory), in slices: a late switch must not block
                # the worker (review V4-16); what is not computed now follows in the next steps of the world
                self._reveal_ghost(self.t / self.T_s, budget=GHOST_SLICE_S)
            else:
                self.ghost = None
                self._msg({"type": "ghost", "t": self.t, "seg": self.seg, "info": None})
        self.params = new
        return desc

    def _phi_now(self):
        st = self.track.state(self.t / self.T_s) if self.track else None
        return float(st["phi"]) if st else 0.0

    # --- actions ------------------------------------------------------------------------------------------------
    def _actions(self):
        return [
            {"name": "boost", "label": T("Push"), "button": T("push"),
             "help": T("An instantaneous change of the speed along the motion (in the frame of the static observer "
                       "at this point): a fraction of the current speed, negative to brake. The body's clock goes on."),
             "args": [{"id": "dv", "label": T("Δv, fraction of the speed"), "type": "float", "default": 0.05,
                       "min": -1.0, "max": 1.0}]},
            {"name": "relaunch", "label": T("New launch of the body"),
             "help": T("The body is launched again from the initial data of the panel “Launch of the body” (r₀, "
                       "speed, angle) at the current moment, from its current direction to the centre; the body's "
                       "clock starts from zero."), "args": []},
        ]

    def action(self, name, args):
        tg = self.t / self.T_s
        if name == "relaunch":
            init = self._launch_data(self.params, self._phi_now())
            self._start_segment(init, T("a new launch of the body"), launch=True, ghost_on=bool(self.params["ghost"]))
            return T("the body is launched again")
        if name == "boost":
            dv = float(args.get("dv", 0.05))
            if not -1.0 <= dv <= 1.0:
                raise Refusal(T("Δv is a fraction of the speed from −1 to 1"))
            if self.track.ended(tg):
                raise Refusal(T("the body is no longer on its orbit ({end})",
                                end=END_TEXT.get(self.track.end_event["kind"], "")))
            st = self.track.state(tg, exact=True)
            vr, vp = st["v_r"], st["v_phi"]
            if vr is None:
                raise Refusal(T("the body's state at this moment was not found"))
            v = math.hypot(vr, vp)
            if v == 0.0:
                raise Refusal(T("the body is at rest relative to the static observer: the direction of motion is "
                                "undefined"))
            f = 1.0 + dv
            vr, vp = vr * f, vp * f
            if abs(vp) <= 1e-12 * abs(vr):
                vp = 0.0
            if abs(vr) <= 1e-12 * abs(vp):
                vr = 0.0  # the dense-output state of a circular orbit has v_r ~ 1e-17: rounding (review V4-1)
            if self.law == "GR" and math.hypot(vr, vp) >= 1.0:
                raise Refusal(T("after the push the speed would be {v:.6g} c, not below c", v=math.hypot(vr, vp)),
                              hint=T("take a smaller Δv"))
            r = st["r"]
            vref = self._v_ref(r, self.law)
            init = {"r0": r, "phi0": st["phi"], "v_r": vr, "v_phi": vp, "v": math.hypot(vr, vp),
                    "k": math.hypot(vr, vp) / vref, "alpha": math.degrees(math.atan2(vr, abs(vp))) if vp or vr else 0.0,
                    "how": "boost"}
            self._start_segment(init, T("a push Δv = {dv:+.4g} of the speed", dv=dv), launch=False,
                                ghost_on=bool(self.params["ghost"]))
            return T("push: speed {v0:.6g} c → {v1:.6g} c at r = {r:.6g}M", v0=v, v1=math.hypot(vr, vp), r=r)
        raise Refusal(T("unknown action {name}", name=str(name)))

    # --- messages and checks --------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)

    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None):
        rel = None
        if ref is not None and value is not None and ref != 0 and math.isfinite(value):
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": self.t, "id": f"s{self.seg}.{cid}", "label": label, "value": value, "ref": ref,
             "unit": unit, "rel": rel, "group": self._group(), "note": note, "tol": tol}
        if ok is not None:
            d["ok"] = bool(ok)
        self._msg(d)

    def _group(self):
        return T("Segment {seg:d} ({law}, {kind})", seg=self.seg, law=LAW_SHORT[self.law], kind=self.info["kind_text"])

    # --- time ---------------------------------------------------------------------------------------------------
    def max_step(self):
        return 0.5 * self.track.dyn * self.T_s

    def advance(self, t_target):
        tg = t_target / self.T_s
        self.t = max(self.t, t_target)  # checks and messages carry the time they are revealed at
        out, evs = self.track.take(tg)
        if out is not None:
            self._trail("trail", out, rate=True)
            if self.info["kind"] == "circular":  # the largest departure from r0 seen so far (circle checks)
                r0 = self.init["r0"]
                self.S["maxdev"] = max(self.S["maxdev"], float(np.max(np.abs(out["r"] - r0))) / r0)
        for e in evs:
            self._on_event(e)
        self._reveal_ghost(tg, budget=GHOST_SLICE_S)
        self.t = t_target

    def _reveal_ghost(self, tg, budget=None):
        if self.ghost is not None:
            gout, gevs = self.ghost.take(tg, budget=budget)
            if not self.ghost.caught_up and "ghost_lag" not in self.S["notes"]:
                self.S["notes"].add("ghost_lag")
                self._msg({"type": "notice", "t": self.t,
                           "text": T("The ghost is being computed from the start of the segment in parts while the "
                                     "world runs; until then its trace is shorter.")})
            if gout is not None:
                self._trail("gtrail", gout, rate=False)
            for e in gevs:
                if e["kind"] in END_TEXT:
                    key = (e["kind"], round(e["t"], 6))
                    if key in self.S["ghost_ends"]:
                        continue  # the ghost was rebuilt after a toggle: its end is not reported twice (V4-14)
                    self.S["ghost_ends"].add(key)
                    self._msg({"type": "event", "t": e["t"] * self.T_s, "kind": "ghost",
                               "text": T("Ghost ({law}): {end} at r = {r:.6g}M", law=LAW_SHORT[self.ghost.theory],
                                         end=END_TEXT[e["kind"]], r=e["r"])})
                elif e["kind"] == "peri":
                    self._msg({"type": "gapsis", "t": e["t"] * self.T_s, "seg": self.seg,
                               "x": e["x"], "y": e["y"], "r": e["r"]})

    def _trail(self, typ, out, rate):
        """Send revealed samples. A step that reveals more than ~3 turns (high speed) keeps the newest two turns at
        full resolution and every 4th sample (at most 1500) of the rest: drawing only, the record stays small."""
        n = len(out["t"])
        idx = np.arange(n)
        full = 480
        if n > 720:
            k = max(4, int(math.ceil((n - full) / 1500)))
            idx = np.concatenate([np.arange(0, n - full, k), np.arange(n - full, n)])
        blobs = {"t": out["t"][idx] * self.T_s, "x": out["x"][idx], "y": out["y"][idx], "r": out["r"][idx]}
        if rate:
            blobs["lag"] = out["lag"][idx]  # 1 - dtau/dt in double precision (Mercury: 6e-8)
        self._msg({"type": typ, "t": float(out["t"][-1]) * self.T_s, "seg": self.seg, "n": int(len(idx))}, blobs)

    def _on_event(self, e):
        k = e["kind"]
        te = e["t"] * self.T_s
        S = self.S
        if k in ("peri", "apo"):
            lst = S[k]
            lst.append(e)
            n = len(lst)
            adv = (lst[-1]["psi"] - lst[-2]["psi"] - 2 * math.pi) if n >= 2 else None
            shift = (lst[-1]["psi"] - lst[0]["psi"] - 2 * math.pi * (n - 1)) if n >= 2 else 0.0
            self._msg({"type": "apsis", "t": te, "seg": self.seg, "kind": k, "n": n, "x": e["x"], "y": e["y"],
                       "r": e["r"], "phi": e["phi"], "adv": adv, "shift": shift,
                       "dt": (lst[-1]["t"] - lst[-2]["t"]) * self.T_s if n >= 2 else None})
            if k == "peri" and (n <= 3 or n % 100 == 0):
                txt = T("Periapsis no. {k:d}: r = {r:.8g}M, φ = {phi:.6g}°", k=n, r=e["r"],
                        phi=math.degrees(e["phi"]) % 360)
                if adv is not None:
                    txt = T("{a}; advance per orbit {adv}", a=txt, adv=_angle_text(adv))
                self._msg({"type": "event", "t": te, "kind": "periapsis", "text": txt})
            if k == "peri" and n >= 2 and _due(n):
                self._checks_advance()
            if k == "apo" and _due(n):
                self._checks_turning(e, "apo")
            if k == "peri" and _due(n):
                self._checks_turning(e, "peri")
            if self._mercury() and S["peri"] and S["apo"] and "merc" not in S["notes"]:
                S["notes"].add("merc")
                rp, ra = S["peri"][0]["r"], S["apo"][0]["r"]
                self._check("merc_a", T("Semi-major axis (r_p + r_a)/2 from the orbit's events ↔ Mercury"),
                            0.5 * (rp + ra) * self.M_m / AU, MERCURY_A_AU, T("AU"), tol=1e-6,
                            note=T("measured: the first periapsis and apoapsis of this run; reference: NASA NSSDCA "
                                   "Mercury Fact Sheet (J2000); the difference O(M/r) ~ 3·10⁻⁸ is GR's contribution "
                                   "to the initial data"))
                self._check("merc_e", T("Eccentricity (r_a − r_p)/(r_a + r_p) from the orbit's events ↔ Mercury"),
                            (ra - rp) / (ra + rp), MERCURY_ECC, "", tol=1e-6,
                            note=T("measured: the first periapsis and apoapsis of this run; reference: NASA NSSDCA "
                                   "(J2000)"))
        elif k == "lap":
            S["laps"].append(e)
            if self.info["kind"] == "circular" and _due(len(S["laps"])):
                self._checks_circular()
        elif k in END_TEXT:
            v = math.hypot(e.get("v_r") or 0.0, e.get("v_phi") or 0.0)
            tau = e["tau"] * self.T_s  # the body's clock since its launch
            txt = T("{end:cap}: r = {r:.8g}M, the body's proper time τ = {tau:.6g} s", end=END_TEXT[k], r=e["r"],
                    tau=tau)
            if k == "horizon":
                txt = T("{a} (a distant observer sees the body only approach r = 2M asymptotically; here the "
                        "computation stops at r − 2M = 2·10⁻⁶ M)", a=txt)
            if k == "surface":
                txt = T("{a}, impact speed {v:.6g} c (a static observer at the surface)", a=txt, v=v)
            self._msg({"type": "event", "t": te, "kind": k, "text": txt})
            self._checks_end(e)
            self._check_outcome(k)

    # --- checks ---------------------------------------------------------------------------------------------------
    def _adv_unit(self, adv):
        return ("″", ARCSEC) if abs(adv) < math.radians(1.0) else ("°", math.pi / 180.0)

    def _apsis_tol(self, adv):
        """Relative tolerance of a measured advance: the integrator's phase floor (~1e-12 rad per orbit) and the
        location of apsides on a nearly circular orbit (APSIS_PHASE/spread)."""
        s = self.info.get("spread") or 1.0
        return max(1e-8, (2e-11 + APSIS_PHASE / s) / abs(adv)) if adv else None

    def _checks_advance(self):
        P = self.S["peri"]
        n = len(P)
        info = self.info
        mean = (P[-1]["psi"] - P[0]["psi"]) / (n - 1) - 2 * math.pi
        period = (P[-1]["t"] - P[0]["t"]) / (n - 1) * self.T_s
        orbits_n = n - 1
        spread = info.get("spread") or 1.0
        if self.law == "GR":
            ref = info["adv_exact"]
            if ref is None:
                return
            unit, sc = self._adv_unit(ref)
            tol = self._apsis_tol(ref)
            self._check("adv", T("Periapsis advance per orbit: measured on the orbit ↔ the exact elliptic integral"),
                        mean / sc, ref / sc, unit, tol=tol,
                        note=T("the angle between successive periapses (zeros of du/dφ in the integrator's output) "
                               "minus 360°, the mean over the orbits observed ({turns:d}); reference: "
                               "lfphys.core.gravity.orbits.periapsis_advance (4K(m)/√(2(u₃−u₁)) − 2π) from e² − 1 "
                               "without loss of precision", turns=orbits_n))
            el = info["elements"]
            mp = 1.0 / el["p"]
            ecc = el["ecc"]
            c2 = (18.0 + ecc * ecc) / 4.0 * mp
            c3 = 5.0 / 12.0 * (54.0 + 9.0 * ecc * ecc) * mp * mp
            if mp <= 0.02:
                self._check("ppn", T("The same ↔ 6πM/p·[1 + (18 + ε²)/4·M/p] (weak field: PPN and the next order)"),
                            mean / sc, info["adv_series2"] / sc, unit, tol=1.5 * c3 + tol,
                            note=T("M/p = {mp:.3g}; the first term 6πM/p = {first:.10g}{unit}: "
                                   "lfphys.theories.approx.ppn (γ = β = 1); the second-order correction {c2:.3g} "
                                   "relative and the third term (5/12)(54 + 9ε²)(M/p)² = {c3:.3g}: "
                                   "lfphys.core.gravity.orbits.advance_series, verified against the exact integral "
                                   "(lfphys/tests/test_relativity_gravity.py); tolerance 1.5× the third term + the "
                                   "numerical one", mp=mp, first=info["adv_ppn"] / sc, unit=unit, c2=c2, c3=c3))
            else:
                ratio = mean / info["adv_ppn"]
                self._check("ppn", T("6πM/p (PPN, first order): here M/p = {mp:.3g}, outside its domain of validity",
                                     mp=mp),
                            info["adv_ppn"] / sc, None, unit,
                            note=T("the measured advance is {ratio:.4g} times larger: the expansion in M/p does not "
                                   "work in a strong field (the next-order correction ≈ {c2:.3g})", ratio=ratio, c2=c2))
            cent = mean * CENTURY_S / period / ARCSEC
            if mp > 0.02:
                pass  # per century only means something in a weak field
            elif self._mercury():
                self._check("century", T("Mercury's perihelion advance per Julian century (measured)"), cent,
                            MERCURY_GR_ARCSEC_PER_CENTURY, T("″/century"), tol=2e-4,
                            note=T("measured: the advance per orbit × ({days} days / the run's radial period); "
                                   "reference {ref}″ per century: Will 2014, Living Rev. Relativ. 17, 4, Eq. (65), "
                                   "γ = β = 1, without the Sun's J2 (+{j2}″); tolerance: the precision of the reference "
                                   "as quoted ({prec}″)", days=36525, ref=MERCURY_GR_ARCSEC_PER_CENTURY, j2=0.03,
                                   prec=0.01))
            else:
                self._check("century", T("Periapsis advance per Julian century (measured)"), cent, None,
                            T("″/century"), note=T("the advance per orbit × ({days} days / the radial period)",
                                                   days=36525))
            ref_t = info.get("period_t_ref")
            self._check("period", T("Radial period (t), measured ↔ the quadrature 2∫e dr/((1 − 2M/r)√R)"), period,
                        ref_t, T("s"), tol=1e-9 + 2.0 * APSIS_PHASE / spread,
                        note=T("the time between periapses; a reference without differential equations: "
                               "lfphys.core.gravity.orbits.radial_period (a smooth χ quadrature over the turning "
                               "points)"))
            if self.S["second"] is None:
                self._second_scheme_bound()
        else:
            ref_p = info["period_ref"]
            tol_a = 1e-9 + APSIS_PHASE_NEWTON / spread
            self._check("adv", T("Periapsis advance per orbit (Newton) ↔ 0: the ellipse is closed"), mean / ARCSEC,
                        0.0, "″", tol=tol_a / ARCSEC, ok=abs(mean) <= tol_a,
                        note=T("the angle between periapses (zeros of r·v) minus 360°, the mean over the orbits "
                               "observed ({turns:d}); tolerance {tol:.2g} rad (the precision of locating the "
                               "periapses)", turns=orbits_n, tol=tol_a))
            if ref_p:
                dE = self.track.drift["E"]
                self._check("period", T("Period (the time between periapses) ↔ Kepler's law 2π√(a³/GM)"), period,
                            ref_p, T("s"), tol=1e-8 + 2.0 * dE + 2.0 * APSIS_PHASE_NEWTON / spread,
                            note=T("a = −GM/(2E) from the initial data; tolerance 10⁻⁸ + 2× the measured energy drift "
                                   "({dE:.2g}: the period of the integrated orbit changes by 1.5 δE/E)", dE=dE))
            self._checks_newton_conservation()

    def _checks_turning(self, e, which):
        info = self.info
        if self.law != "GR" or info["kind"] != "bound" or not info.get("elements"):
            return
        el = info["elements"]
        ref = el["r_peri"] if which == "peri" else el["r_apo"]
        lab = (T("Periapsis: r at the event du/dφ = 0 on the orbit ↔ the root of f(u) (a turning point)")
               if which == "peri" else
               T("Apoapsis: r at the event du/dφ = 0 on the orbit ↔ the root of f(u) (a turning point)"))
        # the reference is computed from e^2 - 1 itself (review V4-7), its roots at 30 digits; what remains is the
        # rounding of the cubic's coefficients, amplified where two turning points come together (near the ISCO)
        cond = (info.get("u_cond") or {}).get(which) or 1.0
        sens = (info.get("u_sens") or {}).get(which) or 0.0
        drift = abs(e["em1_state"] - info["em1"]) / abs(info["em1"])
        tol = 1e-11 + 4.0 * 2.2e-16 * cond + 2.0 * sens * drift
        self._check("r_" + which, lab, e["r"], ref, "M", tol=tol,
                    note=T("reference: lfphys.core.gravity.orbits.elements from e² − 1 (without loss of precision), "
                           "the cubic's roots to 30 digits; tolerance 10⁻¹¹ + 4ε·κ + 2·s·δ: κ = Σ|terms of "
                           "f|/(|f′(u)|·u) = {cond:.3g} (the root's conditioning), δ = {drift:.2g} the measured drift "
                           "of e² − 1 at this event (the row below), s = {sens:.3g} how much it moves the turning "
                           "point", cond=cond, drift=drift, sens=sens))
        self._check("em1", T("e² − 1 from the body's state at the turning point ↔ the initial one (the integration "
                             "drift)"),
                    e["em1_state"], info["em1"], "", tol=1e-9,
                    note=T("the first integral e² − 1 = l²(u'² + u² − 2u³) − 2u from the integrator's (u, du/dφ), "
                           "u = M/r"))

    def _second_scheme_bound(self):
        """The same initial data integrated by the independent scheme (geodesic equations in proper time)."""
        P = self.S["peri"]
        init = self.init
        tau_end = (P[1]["tau"] - self.seg_tau0) + 0.25 * (P[1]["tau"] - P[0]["tau"])
        g = orbit_stream.geodesic_tau(init["r0"], init["v_r"], init["v_phi"], tau_end,
                                      r_stop=self.R if self.R > 0 else 2.0)
        self.S["second"] = g
        main = P[1]["psi"] - P[0]["psi"] - 2 * math.pi
        ref = self.info["adv_exact"]
        if len(g["peri_phi"]) >= 2:
            sec = abs(g["peri_phi"][1] - g["peri_phi"][0]) - 2 * math.pi
            unit, sc = self._adv_unit(ref)
            self._check("adv2", T("Advance over the first orbit: the second scheme (geodesic equations in τ) ↔ the "
                                  "main one"),
                        sec / sc, main / sc, unit, tol=2.0 * self._apsis_tol(ref),
                        note=T("lfphys.core.gravity.orbit_stream.geodesic_tau: (t, r, φ) from the Christoffel symbols; "
                               "e, l and the normalisation are not imposed"))
        self._drift_checks(g)

    def _drift_checks(self, g):
        """Drifts of the second scheme. e and the norm are compared with the binding energy |e^2 - 1| (review V4-8:
        in a weak field |e - 1| ~ 1e-8, so a drift of e of 1e-9 relative to e would be 8 % of it); in these variables
        double precision resolves it only to ~eps/|e^2 - 1| per step (measured up to ~30 eps over an eccentric orbit
        from 1e8 M), hence the tolerance max(1e-9, 100 eps/|e^2 - 1|)."""
        floor = g["binding_floor"] or 0.0
        tol = max(1e-9, 100.0 * floor)
        eb, nb = g["e_drift_binding"], g["norm_drift_binding"]
        self._check("drift_e", T("Second scheme: the drift of e² relative to the binding energy |e² − 1|"), eb, None,
                    "", tol=tol, ok=eb is not None and eb <= tol,
                    note=T("the maximum of |e² − e₀²|/|e₀² − 1| over the orbit, |e² − 1| = {em1:.3g}; the precision "
                           "limit of the variables ~{floor:.1g}; tolerance {tol:.2g}", em1=abs(g["em1"]), floor=floor,
                           tol=tol))
        self._check("drift_l", T("Second scheme: the drift of l = r² dφ/dτ"), g["l_drift"], None, "", tol=1e-9,
                    ok=g["l_drift"] <= 1e-9,
                    note=T("relative, the maximum over the orbit; in the main scheme (Binet) l is a parameter of the "
                           "equation"))
        self._check("drift_n", T("Second scheme: the normalisation |u·u + 1| relative to |e² − 1|"), nb, None, "",
                    tol=tol, ok=nb is not None and nb <= tol,
                    note=T("the maximum over the orbit; tolerance {tol:.2g}", tol=tol))

    def _checks_circular(self):
        """Circle checks. «Circular» is granted up to a relative spread s = (r_apo - r_peri)/r_peri of 1e-6; the mean
        rate and the lap time of such an orbit differ from the exact circle by O(s), so the tolerance is 1e-10 + 3 s
        (GR; Newton 1e-8 + 3 s). On an unstable circle (r0 < 6M) rounding grows: laps are checked only while the
        largest departure from r0 seen so far stays below 1.5 s + 2e-11 (the rate moves by ~2M/(r - 2M) of it)
        (review V4-5)."""
        L = self.S["laps"]
        n = len(L)
        e = L[-1]
        r0 = self.init["r0"]
        s = self.info.get("spread") or 0.0
        guard = 1.5 * s + 2e-11
        if self.S["maxdev"] > guard:
            if "left" not in self.S["notes"]:
                self.S["notes"].add("left")
                self._msg({"type": "notice", "t": self.t,
                           "text": T("The body is leaving its circular orbit (r deviates by up to {dev:.2g} r₀, orbits "
                                     "completed: {turns:d}; the spread of the turning points {s:.2g}): an instability, "
                                     "the circle's checks stop here.", dev=self.S["maxdev"], turns=n, s=s)})
            return
        dt = e["t"] * self.T_s - self.seg_t0
        dtau = (e["tau"] - self.seg_tau0) * self.T_s

        def note_s(base):
            return T("{a}; the orbit is circular with a spread of the turning points s = {s:.2g}, the tolerance "
                     "includes 3s", a=base, s=s)

        if self.law == "GR":
            tol = 1e-10 + 3.0 * s
            self._check("rate", T("dτ/dt on a circular orbit: Δτ/Δt on the orbit ↔ √(1 − 3M/r)"), dtau / dt,
                        self.info["rate_circ"], "", tol=tol,
                        note=note_s(T("the body's proper time over the orbits observed ({turns:d}) to the coordinate "
                                      "time; reference: the closed form", turns=n)))
            self._check("period", T("Orbital period (t) ↔ 2π√(r³/GM) (exact for a circular geodesic)"), dt / n,
                        self.info["period_ref"], T("s"), tol=tol,
                        note=note_s(T("the time of one turn in φ, the mean")))
            if self.S["second"] is None:
                g = orbit_stream.geodesic_tau(r0, self.init["v_r"], self.init["v_phi"], dtau / self.T_s,
                                              r_stop=self.R if self.R > 0 else 2.0)
                self.S["second"] = g
                dr = float(np.max(np.abs(g["r"] - r0)) / r0)
                stable = r0 > self.special["isco"]
                lim = (1e-9 if stable else 1e-6) + 1.5 * s
                self._check("circ2", T("Second scheme: the departure of r from r₀ over an orbit"), dr, None, "",
                            tol=lim, ok=dr < lim, note=note_s(T("geodesic equations in τ from the same initial data")))
                self._drift_checks(g)
        else:
            tol = 1e-8 + 3.0 * s
            self._check("period", T("Orbital period ↔ 2π√(r³/GM) (Kepler)"), dt / n,
                        2 * math.pi * r0**1.5 * self.T_s, T("s"), tol=tol,
                        note=note_s(T("the time of one turn in φ, the mean")))
            self._checks_newton_conservation()

    def _checks_newton_conservation(self):
        """E and h along every integration sample. The integration keeps a relative tolerance 1e-12 of the local
        terms, so near a deep periapsis the error of E is ~1e-12 of the largest term v^2/2 + GM/r there, which can be
        10^6 |E|: the tolerance is 1e-9 of the largest term seen (review V4-4); the row shows it (V4-13)."""
        d = self.track.drift
        E0 = abs(self.track.E0)
        tol_E = 1e-9 * d["scale"] / E0
        self._check("energy", T("Energy E = v²/2 − GM/r: the drift over the orbit"), d["E"], None, "", tol=tol_E,
                    ok=d["E"] <= tol_E,
                    note=T("relative to |E|, the maximum over all integration points; tolerance 10⁻⁹ of the largest "
                           "term v²/2 + GM/r on the orbit ({ratio:.3g} times |E|)", ratio=d["scale"] / E0))
        self._check("angmom", T("Angular momentum h = x·v_y − y·v_x: the drift over the orbit"), d["h"], None, "",
                    tol=1e-9, ok=d["h"] <= 1e-9, note=T("relative, the maximum; tolerance 10⁻⁹"))

    def _checks_end(self, e):
        k = e["kind"]
        init = self.init
        tau = (e["tau"] - self.seg_tau0) * self.T_s
        if self.law != "GR":
            if k in ("center", "surface"):
                self._checks_newton_conservation()
            return
        if k in ("horizon", "surface"):
            if init["v"] == 0.0 and init["how"] == "launch":
                r0 = init["r0"]
                rs = e["r"]
                eta = math.acos(2.0 * rs / r0 - 1.0)
                ref = math.sqrt(r0**3 / 8.0) * (eta + math.sin(eta)) * self.T_s
                self._check("fall_tau", T("Proper time of the fall from rest to r = {r:.10g}M ↔ the cycloid", r=rs),
                            tau, ref, T("s"), tol=1e-9,
                            note=T("τ = √(r₀³/8M)(η + sin η), r = r₀(1 + cos η)/2: the exact solution of the radial "
                                   "fall"))
            else:
                ref = None
                nr = self.info.get("nearest_root")
                on_double = bool(self.info.get("double_root")) or (
                    bool(self.info.get("start_turning")) and nr is not None and nr < 1e-6)
                note = T("a reference without differential equations: R = e² − (1 − 2M/r)(1 + l²/r²), "
                         "lfphys.core.gravity.orbit_stream.plunge_proper_time")
                if on_double:
                    note = T("no reference: the start is at an (almost) double root of R(r), on an unstable circular "
                             "orbit; the time to the fall is set by the growth of rounding errors, and the integral "
                             "∫dr/√R diverges")
                else:
                    try:
                        ref = orbit_stream.plunge_proper_time(self.track.em1, self.track.l, init["r0"], init["v_r"],
                                                              e["r"], self.info.get("r_apo")) * self.T_s
                    except ValueError:
                        pass
                self._check("fall_tau", T("Proper time to r = {r:.10g}M ↔ the quadrature ∫dr/√R(r)", r=e["r"]), tau,
                            ref, T("s"), tol=1e-9, note=note)
            if k == "surface":
                v = math.hypot(e["v_r"], e["v_phi"])
                ref = orbit_stream.local_speed_from_e(self.R, self.track.e)
                self._check("impact", T("Impact speed (a static observer at the surface) ↔ √(1 − (1 − 2M/R)/e²)"),
                            v, ref, "c", tol=1e-9, note=T("from the integrator's state at r = R"))

    def _check_outcome(self, k):
        """The end the run observed against the kind predicted from the turning points at the start of the segment
        (review V4-12: a check that can fail). A circle at r0 < 6M (unstable) may end either way."""
        kind = self.info["kind"]
        r0 = self.init["r0"]
        fall = {"horizon", "surface", "center"}
        expect = {"plunge": fall, "radial_fall": fall, "escape": {"escape"}, "radial_escape": {"escape"}}.get(kind)
        unstable_circle = kind == "circular" and (self.law == "GR" and r0 < self.special["isco"])
        if unstable_circle:
            expect = fall | {"escape"}
        ok = expect is not None and k in expect
        pred = {"plunge": T("a fall"), "radial_fall": T("a fall"), "escape": T("escape"), "radial_escape": T("escape"),
                "bound": T("bound: no end"), "circular": T("circular")}.get(kind, kind)
        note = T("the prediction is from the turning points at the start of the segment (lfphys.core.gravity.orbit_stream)")
        if unstable_circle or (kind == "plunge" and self.law == "GR" and self.special["photon"] < r0 < self.special["isco"]):
            note = T("{a}; r₀ = {r0:.4g}M < ISCO = {isco:.6g}M (lfphys.core.gravity.kerr.isco(0)): outside the ISCO the "
                     "same perturbation gives a bound orbit (test v04)", a=note, r0=r0, isco=self.special["isco"])
        self._check("outcome", T("Outcome of the orbit: predicted “{pred}”, observed “{seen}”", pred=pred,
                                 seen=END_TEXT.get(k, k)), None, None, "", ok=ok, note=note)

    def _mercury(self):
        """The Mercury reference applies only to its own initial data (preset values, unchanged)."""
        p = self.params
        return (self.law == "GR" and math.isclose(self.msun, 1.0, rel_tol=1e-12) and self.init["how"] == "launch"
                and math.isclose(self.init["r0"], MERCURY_R0, rel_tol=1e-9)
                and math.isclose(self.init["k"], MERCURY_K, rel_tol=1e-9) and self.init["alpha"] == 0.0
                and p["r0"] == self.init["r0"])

    # --- frames ---------------------------------------------------------------------------------------------------
    def frame(self):
        tg = self.t / self.T_s
        st = self.track.state(tg)
        d = {"seg": self.seg, "x": st["x"], "y": st["y"], "r": st["r"], "phi": st["phi"], "alive": st["alive"],
             "status": (self.track.end_event["kind"] if not st["alive"] else "orbit"),
             "tau": st["tau"] * self.T_s, "t_launch": self.t_launch, "rate": st["rate"], "deficit": st["lag"],
             "n_peri": len(self.S["peri"]), "n_lap": len(self.S["laps"])}
        vr, vp = st.get("v_r"), st.get("v_phi")
        if self.law == "GR":
            r = st["r"]
            v = math.hypot(vr, vp) if vr is not None else orbit_stream.local_speed_from_e(r, self.track.e)
            d.update(v=v, grav=math.sqrt(max(1.0 - 2.0 / r, 0.0)), kin=math.sqrt(max(1.0 - v * v, 0.0)))
        else:
            v = math.hypot(vr, vp) if vr is not None else None
            d.update(v=v, grav=1.0, kin=1.0)
        if self.ghost is not None:
            g = self.ghost.state(tg)
            d["ghost"] = {"x": g["x"], "y": g["y"], "r": g["r"], "alive": g["alive"], "tau": g["tau"] * self.T_s,
                          "rate": g["rate"]}
        # (the frame key "lag" is the runner's flag "the computation cannot keep up"; 1 - dtau/dt is "deficit")
        else:
            d["ghost"] = None
        return d, {}

    def next_event_time(self):
        kinds = {"peri", "apo", "horizon", "surface", "center", "escape"}
        if self.info["kind"] == "circular":
            kinds.add("lap")
        te = self.track.next_event_after(self.t / self.T_s, kinds)
        return None if te is None else te * self.T_s

    def header(self):
        body = T("a black hole") if self.R == 0 and self.law == "GR" else (
            T("a point mass") if self.R == 0 else T("a body of radius {r:.6g} km", r=self.params["radius_km"]))
        return {
            "title": T("Orbits and clocks: {law}, {m:.6g} M☉, {body}", law=LAW_SHORT[self.law], m=self.msun, body=body),
            "text": T("A test body in the equatorial plane of the central body. The orbit is computed in this run from "
                      "the initial data: in GR the exact Schwarzschild geodesic (the orbit equation together with the "
                      "coordinate time t and the body's proper time τ), in a Newton world the Newtonian orbit. The run "
                      "shows the orbit as the world's time t (the clock of a distant static observer) reaches it; the "
                      "periapses, their advance and the body's clock are the run's measurements. GR's closed forms "
                      "are only references in “Checks”. A change of r₀, the speed or the angle launches the body "
                      "again at the current moment; “Push” changes the speed on the fly."),
            "modifications": SCHEMA.modifications(self.params),
            "law": self.law,
            "units": {"M_m": self.M_m, "T_s": self.T_s, "au_m": AU, "gm": self.gm},
            "body": {"mass_msun": self.msun, "R": self.R, "R_km": self.params["radius_km"]},
            "special": self.special,
            "actions": self._actions(),
        }, {}


VIZ = {
    "id": "v04_orbits",
    "title": T("Orbits and clocks: general relativity and Newton"),
    "summary": T("A body orbiting a star or a black hole: the periapsis precession (Mercury {adv}″ per century, a "
                 "neutron star, the ISCO), the fall through the horizon, the body's proper time against the time of a "
                 "distant observer; a comparison with the Newtonian orbit from the same initial data.", adv=43),
    "purpose": T("To see how GR's equations of motion give the precession, the instability of orbits near the ISCO and "
                 "the slowing of clocks, and how Newton differs; the laws can be deliberately replaced by Newton's."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
