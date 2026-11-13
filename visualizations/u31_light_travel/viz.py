# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v01: light over large distances - finite speed, light cones, gravity, moving observers.

What the run computes (README.md of this folder has the model in full):
* light from an emission event is traced under the run's laws (flat: Lorentz-aberrated straight rays; GR: null
  geodesics of Schwarzschild; modifications: ether, ballistic light, Newtonian corpuscles);
* exact arrival events at every receiver (quadratic solve in flat space, quadrature + root finding in GR);
* clocks along every worldline from the metric of the laws; observers' frames from the laws' transformations;
* measurements by apparatus (a rod with clocks at both ends, synchronised by a simulated light exchange);
* checks: each computed quantity next to the closed-form value of accepted physics (or of the declared
  modification).
"""

from __future__ import annotations

import math

import numpy as np
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

from lfphys.core.constants import AU, DAY, GM_SUN, LIGHT_YEAR, R_EARTH, R_SUN
from lfphys.core.constants import C as C_SI
from lfphys.core.worldlines import Orbit, Piecewise
from lfphys.i18n import T, join
from lfphys.laws.light import GRAVITY, KINEMATICS, Laws

from .engine import checks
from .engine.apparatus import Apparatus, fmt_s
from .engine.world import Obj, World, _check

SCN = [("sun_earth", T("Sun → Earth: light travels for 8 minutes")),
       ("measure_c", T("Measuring the speed of light by moving observers")),
       ("lensing", T("Gravitational deflection of light (black hole / star)")),
       ("andromeda", T("The Andromeda paradox: the relativity of simultaneity"))]

G_SCN, G_LAWS, G_LIGHT = T("Scenario"), T("Laws of physics"), T("Light")
G_SE, G_MC, G_LN, G_AN = T("Sun and Earth"), T("Measuring c"), T("Lens"), T("Andromeda")


def _p(*a, **k):
    return Param(*a, **k)


SE = {"scenario": ["sun_earth"]}
MC = {"scenario": ["measure_c"]}
LN = {"scenario": ["lensing"]}
AN = {"scenario": ["andromeda"]}

SCHEMA = Schema([
    _p("scenario", T("Scenario"), "select", "sun_earth", group=G_SCN, options=SCN),
    _p("kinematics", T("Kinematics"), "select", "SR", group=G_LAWS, options=KINEMATICS, standard="SR",
       help=T("SR is the accepted theory. The ether and the emission theory are historical alternatives refuted by "
              "experiment; choosing one marks the run as modified physics.")),
    _p("gravity", T("Gravity"), "select", "GR", group=G_LAWS, options=GRAVITY, standard="GR",
       help=T("GR is the accepted theory (for the scenarios with a mass). “No gravity” in a scenario with a mass is a "
              "modification.")),
    _p("c_factor", T("Speed of light, × c"), "float", 1.0, group=G_LAWS, min=1e-3, max=1e3, log=True,
       standard=1.0, help=T("A multiplier on c = {c:d} m/s; any value other than 1 is a modification.", c=299792458)),
    _p("n_rays", T("Rays per flash"), "int", 360, group=G_LIGHT, min=36, max=1440,
       help=T("How many rays draw the front of one flash. It does not affect the accuracy of the events: they are "
              "computed separately.")),
    # sun-earth
    _p("se_mass", T("Mass of the Sun, M☉"), "float", 1.0, group=G_SE, min=1e-3, max=1e6, log=True, show_if=SE),
    _p("se_radius_km", T("Radius of the Sun, km"), "float", R_SUN / 1e3, group=G_SE, min=1.0, max=1e8, log=True,
       show_if=SE),
    _p("se_distance_au", T("Distance to the Earth, au"), "float", 1.0, group=G_SE, min=0.01, max=100, log=True,
       show_if=SE),
    _p("se_orbit", T("The Earth moves along its orbit"), "bool", True, group=G_SE, show_if=SE),
    # measure c
    _p("mc_v1", T("Observer 1: speed, × c"), "float", 0.0, group=G_MC, min=-0.99, max=0.99, show_if=MC),
    _p("mc_v2", T("Observer 2: speed, × c"), "float", 0.5, group=G_MC, min=-0.99, max=0.99, show_if=MC,
       help=T("Positive: away from the source (along the light); negative: towards the light.")),
    _p("mc_v3", T("Observer 3: speed, × c"), "float", -0.5, group=G_MC, min=-0.99, max=0.99, show_if=MC),
    _p("mc_L0_km", T("Rod length L₀ (at rest), km"), "float", 300.0, group=G_MC, min=1e-3, max=1e6, log=True,
       show_if=MC),
    _p("mc_src_km", T("Distance to the sources, km"), "float", 3000.0, group=G_MC, min=1.0, max=1e8, log=True,
       show_if=MC),
    _p("mc_src_u", T("Speed of the sources, × c"), "float", 0.0, group=G_MC, min=-0.9, max=0.9, show_if=MC,
       help=T("Matters in the emission theory (light travels at c relative to its source); in SR it does not "
              "change c.")),
    _p("mc_sync", T("Synchronisation of clock B"), "select", "einstein", group=G_MC, show_if=MC,
       options=[("einstein", T("Einstein's (light exchange)")),
                ("lab", T("by laboratory simultaneity (not available to the observer)"))]),
    _p("mc_orient", T("Rod"), "select", "x", group=G_MC, show_if=MC,
       options=[("x", T("along the motion (x axis)")), ("y", T("across the motion (y axis)"))]),
    _p("mc_t_flash_ms", T("Time of the flash of the sources, ms"), "float", 3.0, group=G_MC, min=0.0, max=1e6,
       show_if=MC),
    # lensing
    _p("ln_mass", T("Mass of the body, M☉"), "float", 10.0, group=G_LN, min=1e-3, max=1e10, log=True, show_if=LN),
    _p("ln_radius_km", T("Radius of the body, km (0 = a black hole)"), "float", 0.0, group=G_LN, min=0.0, max=1e8,
       show_if=LN),
    _p("ln_src_rs", T("Source: distance, rs"), "float", 60.0, group=G_LN, min=5.0, max=1e5, log=True, show_if=LN),
    _p("ln_src_y_rs", T("Source: sideways offset, rs"), "float", 0.5, group=G_LN, min=-1e4, max=1e4, show_if=LN),
    _p("ln_obs_rs", T("Observer: distance, rs"), "float", 60.0, group=G_LN, min=5.0, max=1e5, log=True,
       show_if=LN),
    _p("ln_plane", T("Parallel beam from the left"), "bool", True, group=G_LN, show_if=LN),
    _p("ln_plane_hw_rs", T("Half-width of the beam, rs"), "float", 10.0, group=G_LN, min=0.5, max=1e4, log=True,
       show_if=LN),
    # andromeda
    _p("an_dist_mly", T("Distance to Andromeda, million ly"), "float", 2.5, group=G_AN, min=1e-9, max=1e4,
       log=True, show_if=AN),
    _p("an_walk", T("Speed of the pedestrians, m/s"), "float", 1.4, group=G_AN, min=0.0, max=2.9e8, show_if=AN),
    _p("an_event_days", T("Time of the event on Andromeda (lab), days"), "float", 0.0, group=G_AN,
       min=-1e12, max=1e12, show_if=AN),
], presets={
    "sun_earth": {"label": T("Sun → Earth (standard physics)"), "params": {"scenario": "sun_earth"}},
    "measure_c": {"label": T("Measuring c: at rest, moving along the light, against it (SR)"),
                  "params": {"scenario": "measure_c", "gravity": "none"}},
    "measure_c_lab": {"label": T("Measuring c: clocks synchronised in the lab frame (SR)"),
                      "params": {"scenario": "measure_c", "gravity": "none", "mc_sync": "lab"}},
    "measure_c_ether": {"label": T("Measuring c in a world with an ether (modification)"),
                        "params": {"scenario": "measure_c", "gravity": "none", "kinematics": "ether"}},
    "measure_c_emission": {"label": T("Measuring c with ballistic light (modification)"),
                           "params": {"scenario": "measure_c", "gravity": "none", "kinematics": "emission",
                                      "mc_src_u": 0.3}},
    "michelson": {"label": T("An arm across the motion (Michelson–Morley), ether (modification)"),
                  "params": {"scenario": "measure_c", "gravity": "none", "kinematics": "ether", "mc_orient": "y"}},
    "lensing": {"label": T("Black hole of {m:d} M☉: deflection, shadow, two images", m=10),
                "params": {"scenario": "lensing"}},
    "lensing_newton": {"label": T("Newtonian corpuscles at a black hole (modification)"),
                       "params": {"scenario": "lensing", "kinematics": "emission", "gravity": "newton",
                                  "ln_radius_km": 29.5}},
    "andromeda": {"label": T("The Andromeda paradox: pedestrians at {v:.2g} m/s", v=1.4),
                  "params": {"scenario": "andromeda", "gravity": "none"}},
    "andromeda_fast": {"label": T("The Andromeda paradox: observers at ±{v:.4g} m/s ({b:.2g} c at the standard c)",
                                  v=0.5 * 299792458.0, b=0.5),
                       "params": {"scenario": "andromeda", "gravity": "none", "an_walk": 0.5 * 299792458.0}},
})


MASSIVE = ("sun_earth", "lensing")  # scenarios with a gravitating body: there the gravity law matters
# the laws' short names (the option labels without their explanation in brackets)
_KIN = {"SR": T("SR"), "ether": T("Galileo + ether"), "emission": T("Emission theory")}
_GRAV = {"GR": T("GR"), "newton": T("Newton: light as corpuscles"), "none": T("No gravity")}


def _adjust_laws(p) -> list:
    """Review UX-params P12 (owner, 2026-11-04: a choice the form offers must work): the law sets of the engine allow
    GR only with SR and Newtonian light only with the emission kinematics (``Laws.validate``). When one law is changed
    and the other is left at its standard value, the world takes the other one as the nearest law that goes with it
    and says so (the returned lines; ``p`` is changed in place, so that the header's parameters and the "modified
    physics" list are the ones in force); two changed laws that do not go together are refused, saying what to
    change. In a scene without a gravitating body (measuring c, Andromeda) the gravity law has nothing to act on and
    is set to "No gravity". A lens of radius 0 (a black hole) is GR's object: without GR the world gives the body
    the horizon's radius 2GM/c² of the same mass, so that it is a body that stops light (the preset
    "lensing_newton"'s choice)."""
    out = []
    k, g = p["kinematics"], p["gravity"]
    massive = p["scenario"] in MASSIVE
    if g == "GR" and k != "SR":
        if massive and k == "emission":
            g = "newton"
            why = T("GR is incompatible with ballistic light (the Schwarzschild metric is locally Lorentzian), so "
                    "gravity is “{g}”: light consists of corpuscles at speed c relative to the source, and the body's "
                    "attraction deflects them half as much as GR does and without the Shapiro delay.", g=_GRAV[g])
        else:
            g = "none"
            why = (T("GR is incompatible with the ether (the Schwarzschild metric is locally Lorentzian), so gravity "
                     "is “No gravity”: the body neither deflects nor delays light, it only absorbs it; the motion of "
                     "the bodies (the Earth's orbit) stays as prescribed.") if massive and k == "ether" else
                   T("there is no gravitating body in this scene, so gravity is “No gravity” (GR and “{k}” do not go "
                     "together, but here that changes nothing).", k=_KIN[k]))
        out.append(T("Kinematics “{k}” with the default gravity (GR): {why} To get GR back, choose the SR "
                     "kinematics.", k=_KIN[k], why=why))
    elif g == "newton" and k == "SR":
        if massive:
            k = "emission"
            out.append(T("The gravity “Newton: light as corpuscles” is defined for corpuscles flying at speed c "
                         "relative to the source, so the kinematics is the emission theory (Ritz), not SR: the speed "
                         "of light depends on the speed of the source. To get SR back, set the gravity to GR or “No "
                         "gravity”."))
        else:
            g = "none"
            out.append(T("There is no gravitating body in this scene, so Newtonian attraction of light has nothing to "
                         "act on: gravity is “No gravity”, the kinematics stays SR."))
    elif g == "newton" and k == "ether":
        if massive:
            raise Refusal(T("Newtonian attraction of light is defined for corpuscles (the emission kinematics), while "
                            "in a world with an ether light is a wave in the ether"),
                          hint=T("choose “Kinematics” = emission theory (Ritz) or “Gravity” = “No gravity”"))
        g = "none"
        out.append(T("There is no gravitating body in this scene: gravity is “No gravity” (Newtonian attraction of "
                     "light does not go with the ether, but here that changes nothing)."))
    p["kinematics"], p["gravity"] = k, g
    if p["scenario"] == "lensing" and g != "GR" and p["ln_radius_km"] == 0.0:
        rs_km = 2 * GM_SUN * p["ln_mass"] / (C_SI * p["c_factor"]) ** 2 / 1e3
        r_max = SCHEMA.by_id["ln_radius_km"].max  # the header's parameters must stay inside the form's range
        p["ln_radius_km"] = min(rs_km, r_max)
        if rs_km > r_max:
            out.append(T("A body of radius 0 (a black hole) makes sense only in GR; without GR the body is given the "
                         "horizon radius of a black hole of the same mass, 2GM/c² = {r:.4g} km (capped at the form's "
                         "maximum {rmax:.4g} km): it absorbs the light that falls on it.", r=rs_km, rmax=r_max))
        else:
            out.append(T("A body of radius 0 (a black hole) makes sense only in GR; without GR the body is given the "
                         "horizon radius of a black hole of the same mass, 2GM/c² = {r:.4g} km: it absorbs the light "
                         "that falls on it.", r=rs_km))
    return out


COLORS = {"star": "#f5b700", "planet": "#3d8bfd", "observer": "#e8590c", "beacon": "#c2255c",
          "galaxy": "#7048e8", "station": "#2b8a3e"}
OBS_COLORS = ["#e8590c", "#2b8a3e", "#1971c2", "#9c36b5", "#c92a2a"]


class Simulation(BaseSimulation):
    speed_range = (1e-12, 1e18)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = p = dict(params)
        self._buf = []
        self.adjusted = _adjust_laws(p)  # P12: the dependent law and the lens's size chosen by the world, stated
        self.laws = Laws(p["kinematics"], p["gravity"], float(p["c_factor"]))
        errs = self.laws.validate()
        if errs:
            raise Refusal(join(errs))
        self.planned = []
        self.scn = getattr(self, "_scn_" + p["scenario"])(p)
        self.default_speed = self.scn["speed"]
        if self.adjusted:
            note = T("The world changed dependent parameters: {what}", what=join(self.adjusted, " "))
            self.scn["text"] = T("{note}\n\n{text}", note=note, text=self.scn["text"])
            self._msg({"type": "notice", "t": 0.0, "text": note})

    def _laws_text(self):
        L = self.laws
        parts = [_KIN[L.kinematics], _GRAV[L.gravity]]
        if L.c_factor != 1.0:
            parts.append(T("c × {f}", f=L.c_factor))
        return join(parts, ", ")

    def _plan(self, t, obj_id, text):
        """A scripted world event from the initial data: shown to the view in advance as planned (review R14)."""
        p = self.world.objects[obj_id].wl.pos(t)
        self.planned.append({"t": t, "obj": obj_id, "x": float(p[0]), "y": float(p[1]), "text": text})

    # message buffering until the header is out
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)

    # --- scenarios ------------------------------------------------------------------------------------
    def _new_world(self, body, center, radius):
        self.world = World(self.laws, body, center, radius, self.params["n_rays"], self._msg)
        return self.world

    def _obs(self, oid, name, x0, v, color, movable=True, kind="observer"):
        wl = Piecewise.start(self.laws, self.world.rs, 0.0, x0, v)
        o = Obj(oid, name, kind, color, wl, movable=movable)
        self.world.add(o)
        return o

    def _scn_sun_earth(self, p):
        gm = GM_SUN * p["se_mass"]
        R = p["se_radius_km"] * 1e3
        d = p["se_distance_au"] * AU
        body = {"gm": gm, "radius": R, "name": T("Sun")}
        w = self._new_world(body, [0.5 * d, 0.0], 1.6 * d)
        rs = w.rs
        if R <= rs * 1.5:
            raise Refusal(T("the radius of the Sun is less than {k:.2g} rs", k=1.5),
                          hint=T("choose the scenario “Gravitational deflection of light (black hole / star)”"))
        # the central body's own clock is not used (its worldline is the centre r = 0)
        w.add(Obj("sun", T("Sun"), "star", COLORS["star"], Piecewise.start(self.laws, 0.0, 0.0, [0.0, 0.0], [0, 0]),
                  radius=R, receiver=False))
        flare = Obj("flare", T("Flare on the Sun"), "beacon", "#ff922b",
                    Piecewise.start(self.laws, rs, 0.0, [R * (1 + 1e-9), 0.0], [0, 0]), receiver=False)
        w.add(flare)
        if p["se_orbit"]:
            # Kepler's third law (exact for circular orbits in Schwarzschild coordinates); the orbit is the
            # scenario's prescribed worldline also when the light's gravity is switched off
            earth_wl = Orbit(self.laws, rs, d, math.sqrt(gm / d**3))
        else:
            earth_wl = Piecewise.start(self.laws, rs, 0.0, [d, 0.0], [0.0, 0.0])
        w.add(Obj("earth", T("Earth"), "planet", COLORS["planet"], earth_wl, radius=R_EARTH))
        w.add(Obj("station", T("Station (at rest at the Earth's starting point)"), "station", COLORS["station"],
                  Piecewise.start(self.laws, rs, 0.0, [d, 0.0], [0.0, 0.0])))
        self._obs("rocket", T("Rocket"), [0.5 * d, 0.0], [0.0, 0.0], OBS_COLORS[2])
        w.schedule({"t": 0.0, "kind": "scripted", "silent": True, "deps": set(),
                    "do": lambda: w.flash("flare", 0.0, label=T("flash on the surface of the Sun"))})
        self._plan(0.0, "flare", T("flash on the Sun"))
        self._initial_checks_sun_earth(p, d, R)
        actions = [self._act_flash(), self._act_boost(), self._act_train()]
        if w.gr:
            actions.append(self._act_measure(T("Measure c locally (a static observer, GR)")))
        return {"speed": 20.0, "actions": actions,
                "view": {"center": [0.5 * d, 0.0], "half": 0.62 * d, "unit": "au"},
                "diagram": {"axis": "x", "x0": -0.05 * d, "x1": 1.05 * d, "t0": -20.0, "t1": 1.3 * d / self.laws.c},
                "text": T("At t = 0 a flash goes off on the surface of the Sun. The front leaves the place of the "
                          "flash by the laws of this run ({laws}); when it reaches the rocket, the station and the "
                          "Earth, an event with the computed time of flight and the receiver's clock reading appears "
                          "in the log. The station is at rest where the Earth was at the time of the flash; the "
                          "Earth moves along a prescribed circular orbit (Kepler's law for the mass of the Sun; with "
                          "gravity switched off this stays a prescribed motion). “1:1” is real time.",
                          laws=self._laws_text())}

    def _initial_checks_sun_earth(self, p, d, R):
        w = self.world
        if not w.gr:
            return
        rs = w.rs
        st = w.objects["station"]
        self._msg({"type": "check", "t": 0.0, **_check(
            "rate_station", T("Rate of the station's clock dτ/dt (metric): self-consistency"),
            st.wl.tau(1.0) - st.wl.tau(0.0), checks.static_clock_rate(d, rs), "", group=T("Self-consistency"),
            note=T("for clocks at rest the general formula of the metric coincides with √(1 − rs/r) identically; the "
                   "independent check is a pulse train from the station (the redshift)"))})
        e = w.objects["earth"]
        if isinstance(e.wl, Orbit):
            self._msg({"type": "check", "t": 0.0, **_check(
                "rate_earth", T("Rate of the Earth's clock on its orbit dτ/dt (metric)"), e.wl.rate(),
                checks.circular_orbit_clock_rate(d, rs), "", group=T("GR"),
                note=T("a circular geodesic: √(1 − {k:.2g} rs/r)", k=1.5))})

    def _scn_measure_c(self, p):
        c = self.laws.c
        D = p["mc_src_km"] * 1e3
        L0 = p["mc_L0_km"] * 1e3
        betas = [p["mc_v1"], p["mc_v2"], p["mc_v3"]]
        w = self._new_world(None, [0.0, 0.0], 3.0 * D + 6 * L0)
        u = p["mc_src_u"] * c
        # one source on the axis; the three observers meet at the origin at t = 0 with different velocities,
        # so every one of them measures light that runs along its rod (collinear)
        w.add(Obj("src", T("Source"), "beacon", COLORS["beacon"],
                  Piecewise.start(self.laws, 0.0, 0.0, [-D, 0.0], [u, 0.0]), receiver=False))
        for i, beta in enumerate(betas):
            # the name carries no velocity: it changes with every boost (the table shows the current one)
            o = self._obs(f"obs{i + 1}", T("Observer {k:d}", k=i + 1), [0.0, 0.0], [beta * c, 0.0], OBS_COLORS[i])
            o.apparatus = Apparatus(self.laws, o.name, o.wl, L0, p["mc_orient"], p["mc_sync"])
            w.build_apparatus(o, 0.0)
        tf = p["mc_t_flash_ms"] * 1e-3
        w.schedule({"t": tf, "kind": "scripted", "silent": True, "deps": set(),
                    "do": lambda: w.flash("src", tf, label=T("flash of the source"))})
        self._plan(tf, "src", T("flash of the source"))
        return {"speed": 1e-3, "actions": [self._act_flash(), self._act_boost(),
                                           self._act_measure(T("Measure c with the apparatus (round trip)")),
                                           self._act_train()],
                "view": {"center": [-0.3 * D, 0.0], "half": 0.9 * D, "unit": "km"},
                "diagram": {"axis": "x", "x0": -1.1 * D, "x1": 0.8 * D, "t0": -0.1 * D / c, "t1": 2.5 * D / c},
                "text": T("Laws of the run: {laws}. Three observers meet at the origin at t = 0 with different "
                          "speeds and carry rods of length L₀ (in their own rest frames) with clocks at the ends A "
                          "and B (B is the far end). First each one synchronises clock B by an exchange of light "
                          "(seen on the diagram), then at time {tf} the source flashes. The speed of light is "
                          "computed from the clock readings at the events where the light passes the ends of the "
                          "rod; the result reaches the observer when the signal with B's reading arrives at A. "
                          "“Measure” is a round trip with one's own light. “Speed” accelerates an observer: the "
                          "apparatus is dismantled, assembled again and synchronised again.", laws=self._laws_text(),
                          tf=fmt_s(tf))}

    def _scn_lensing(self, p):
        gm = GM_SUN * p["ln_mass"]
        rs0 = 2 * gm / self.laws.c**2  # scale unit even when gravity is switched off
        R = p["ln_radius_km"] * 1e3
        body = {"gm": gm, "radius": R, "name": T("Lens")}
        xs = -p["ln_src_rs"] * rs0
        xo = p["ln_obs_rs"] * rs0
        span = max(-xs, xo)
        w = self._new_world(body, [0.0, 0.0], 1.35 * span)
        rs = w.rs
        w.add(Obj("lens", T("Black hole") if R <= rs else T("Lensing body"), "star", "#212529",
                  Piecewise.start(self.laws, 0.0, 0.0, [0.0, 0.0], [0, 0]), radius=max(R, rs), receiver=False))
        w.add(Obj("src", T("Source"), "beacon", COLORS["beacon"],
                  Piecewise.start(self.laws, rs, 0.0, [xs, p["ln_src_y_rs"] * rs0], [0, 0]), receiver=False))
        self._obs("obs", T("Observer"), [xo, 0.0], [0.0, 0.0], OBS_COLORS[0])

        def at_zero():
            w.flash("src", 0.0, label=T("flash of the source"))
            if p["ln_plane"]:
                rays, ys = w.plane_wave(0.0, -0.5 * span, p["ln_plane_hw_rs"] * rs0, 121)
                self._deflection_checks(rays, ys)

        w.schedule({"t": 0.0, "kind": "scripted", "silent": True, "deps": set(), "do": at_zero})
        self._plan(0.0, "src", T("flash of the source"))
        if w.gr:
            self._msg({"type": "check", "t": 0.0, **_check(
                "bc", T("Critical impact parameter b_c / rs (photon sphere)"), None,
                checks.b_crit(rs) / rs, "", group=T("GR"),
                note=T("rays with b < b_c are captured; the boundary from the beam appears once it is computed"))})
        actions = [self._act_flash(), self._act_train(), self._act_boost()]
        if w.gr:
            actions.append(self._act_measure(T("Measure c locally (a static observer, GR)")))
        return {"speed": 2.5 * span / self.laws.c / 20.0, "actions": actions,
                "view": {"center": [0.0, 0.0], "half": 0.45 * span, "unit": "rs", "rs": rs0},
                "diagram": {"axis": "x", "x0": 1.25 * xs, "x1": 1.25 * xo, "t0": -0.05 * span / self.laws.c,
                            "t1": 3.0 * span / self.laws.c},
                "text": T("On the left, a parallel beam; at the source, a flash. Every ray is computed by the laws "
                          "of the run ({laws}). What the front does near the body (is delayed, bends round, is "
                          "captured or goes straight) is seen from the computed rays; the observer receives the "
                          "images the run found, at the moments it found them (events in the log). The checks appear "
                          "when the rays have actually reached the horizon or left the scene.", laws=self._laws_text())}

    def _deflection_checks(self, rays, ys):
        """Compare the RK fan with exact quadrature on the same finite path; the capture boundary vs b_c."""
        w = self.world
        if not w.gr:
            return
        from lfphys.core.gravity import schwarzschild as S
        rs = w.rs
        f = lambda r: 1.0 - rs / r
        esc_b, cap_b = [], []
        t_end = {}
        picks = []
        for i in range(rays.n):
            TT, X, Y = rays.ray(i)
            r0 = math.hypot(X[0], Y[0])
            b = abs(ys[i]) / math.sqrt(f(r0))  # L of a ray launched along +x in the static frame
            t_end[b] = TT[-1]
            if rays.status[i] == 0:
                esc_b.append(b)
                if b > 3.0 * rs and len(picks) < 3 and ys[i] > 0:
                    picks.append((i, b, r0, math.hypot(X[-1], Y[-1]), X, Y, TT[-1]))
            elif rays.status[i] == 2:
                cap_b.append(b)

        def later(t, chk):  # revealed when the run's time reaches the rays' fate (review R6)
            w.schedule({"t": t, "kind": "check", "silent": True, "deps": set(), "checks": [chk]})

        if esc_b and cap_b:
            lo, hi = max(cap_b), min(b for b in esc_b if b > max(cap_b))
            mid = 0.5 * (lo + hi)
            later(max(t_end[lo], t_end[hi]), _check(
                "bc", T("Critical impact parameter b_c / rs: the capture boundary of the beam"), mid / rs,
                checks.b_crit(rs) / rs, "", group=T("GR"), tol=0.5 * (hi - lo) / mid,
                note=T("the boundary between the captured and the escaping rays of the beam: [{lo:.4f}, {hi:.4f}] rs; "
                       "the accuracy is limited by the spacing of the rays; reference 3√3/2 rs", lo=lo / rs,
                       hi=hi / rs)))
        for i, b, r0, r1, X, Y, te in picks[-2:]:
            phi_rk = abs(np.unwrap(np.arctan2(Y, X))[-1] - np.unwrap(np.arctan2(Y, X))[0])
            rtp = S.turning_point(b, rs)
            p1, _ = S.integrals(b, rtp, r0, rs, self.laws.c, rtp)
            p2, _ = S.integrals(b, rtp, r1, rs, self.laws.c, rtp)
            later(te, _check(
                f"swept_{i}", T("Angle swept by the ray b = {b:.3f} rs (RK against quadrature)", b=b / rs), phi_rk,
                p1 + p2, T("rad"), group=T("GR"),
                note=T("one and the same finite path: a check of the geodesic integrator")))
            later(te, _check(
                f"defl_{i}", T("Deflection of the same ray at infinity (quadrature, a reference computation)"),
                S.deflection_from_quadrature(b, rs), checks.darwin_deflection(rtp, rs), T("rad"), group=T("GR"),
                note=T("not an event of the run: the path from −∞ to +∞; reference: Darwin's formula (elliptic "
                       "integrals); weak-field limit 2rs/b = {w:.6g}", w=2 * rs / b)))

    def _scn_andromeda(self, p):
        c = self.laws.c
        D = p["an_dist_mly"] * 1e6 * LIGHT_YEAR
        v = p["an_walk"]
        if self.laws.relativistic and v >= c:  # P7: the walkers' worldlines would not be timelike in this world
            raise Refusal(T("pedestrians cannot be faster than the light of this world: the pedestrians' speed "
                            "{v:.4g} m/s ≥ c × {f} = {c:.4g} m/s (in SR a body cannot reach the speed of light)", v=v,
                            f=self.laws.c_factor, c=c),
                          hint=T("make the pedestrians' speed less than {c:.4g} m/s or raise the multiplier “Speed "
                                 "of light, × c” above {f:.4g}", c=c, f=v / C_SI))
        w = self._new_world(None, [0.5 * D, 0.0], 1.2 * D)
        w.add(Obj("earth", T("Earth"), "planet", COLORS["planet"], Piecewise.start(self.laws, 0.0, 0.0, [0, 0], [0, 0]),
                  radius=R_EARTH, receiver=True))
        w.add(Obj("andromeda", T("Andromeda"), "galaxy", COLORS["galaxy"],
                  Piecewise.start(self.laws, 0.0, 0.0, [D, 0.0], [0, 0]), radius=5e20, receiver=True))
        self._obs("walk_to", T("Walks towards Andromeda"), [0.0, 0.0], [v, 0.0], OBS_COLORS[0])
        self._obs("stay", T("At rest"), [0.0, 0.0], [0.0, 0.0], OBS_COLORS[1])
        self._obs("walk_from", T("Walks away from Andromeda"), [0.0, 0.0], [-v, 0.0], OBS_COLORS[2])
        tA = p["an_event_days"] * DAY
        w.schedule({"t": tA, "kind": "scripted", "silent": True, "deps": set(),
                    "do": lambda: w.flash("andromeda", tA, label=T("event on Andromeda (the fleet takes off)"))})
        self._plan(tA, "andromeda", T("event on Andromeda (the fleet takes off)"))
        # simultaneity at t = 0 from the observers' frames (computed) vs the closed form
        for oid in ("walk_to", "walk_from"):
            o = w.objects[oid]
            M = self.laws.frame_matrix(o.wl.vel(0.0))
            # event on Andromeda's worldline with ct' = 0: M00 c t + M01 D = 0
            t_sim = -M[0, 1] * D / (M[0, 0] * c)
            self._msg({"type": "check", "t": 0.0, **_check(
                f"simul_{oid}", T("“{obj}”: “now” on Andromeda at t = 0 (lab time, days)", obj=o.name),
                t_sim / DAY, checks.simultaneity_offset(o.wl.vel(0.0)[0], D, c, self.laws.kinematics) / DAY,
                T("d"), group=T("Simultaneity"), note=T("reference: v·D/c² (SR), 0 with absolute time"))})
        return {"speed": 1e12, "actions": [self._act_flash(), self._act_boost()],
                "view": {"center": [0.5 * D, 0.0], "half": 0.65 * D, "unit": "ly"},
                "diagram": {"axis": "x", "x0": -0.05 * D, "x1": 1.05 * D, "t0": -0.3 * D / c, "t1": 1.3 * D / c,
                            "zooms": [{"label": T("at Andromeda ±{d:d} d", d=10), "x0": D - c * 12 * DAY, "x1": D + c * 12 * DAY,
                                       "t0": tA - 10 * DAY, "t1": tA + 10 * DAY},
                                      {"label": T("at the Earth ±{d:d} d", d=10), "x0": -c * 12 * DAY, "x1": c * 12 * DAY,
                                       "t0": -10 * DAY, "t1": 10 * DAY}]},
                "text": T("Three observers pass each other on the Earth at t = 0 with different speeds. The diagram "
                          "shows their lines of simultaneity (“now”) computed by the laws of the run ({laws}); the "
                          "buttons “at Andromeda ±{d:d} d” and “at the Earth ±{d:d} d” zoom the diagram. The table "
                          "“Objects and clocks” shows which moment on Andromeda each observer calls “now” and "
                          "whether the planned event has already happened there. The parts of the slice that lie in "
                          "the lab future are not computed yet and are shown pale. The light from the event reaches "
                          "the observers at the moments the run computes.", laws=self._laws_text(),
                          d=10)}

    # --- actions --------------------------------------------------------------------------------------
    def _objs(self, pred):
        return [{"value": o.id, "label": o.name} for o in self.world.objects.values() if pred(o)]

    def _act_flash(self):
        return {"name": "flash", "label": T("Flash"), "args": [
            {"id": "obj", "label": T("Who"), "type": "select", "options": self._objs(lambda o: o.kind != "star")}]}

    def _act_flash_all(self):
        return {"name": "flash_all", "label": T("Flash of all sources"), "args": []}

    def _act_boost(self):
        """A live action (owner, 2026-10-23: changes apply at once): choose who, then move the speed or direction;
        each committed value is a boost at the current moment. ``current`` gives each object's present velocity."""
        c = self.laws.c
        cur = {}
        for o in self.world.objects.values():
            if o.movable:
                v = o.wl.vel(self.t)
                cur[o.id] = {"v": float(math.hypot(v[0], v[1]) / c), "angle": float(math.degrees(math.atan2(v[1], v[0])))}
        return {"name": "boost", "label": T("Speed (changes at once)"), "mode": "live", "key": "obj",
                "help": T("Release the slider or press Enter: the object instantly gets the new speed at the current "
                          "moment. Enter small speeds as a number ({v:.2g} m/s ≈ {b:.3g} c).", v=1.4, b=1.4 / C_SI),
                "current": cur, "args": [
                    {"id": "obj", "label": T("Who"), "type": "select", "options": self._objs(lambda o: o.movable)},
                    {"id": "v", "label": T("speed, fractions of c"), "type": "float", "default": 0.0, "min": 0.0,
                     "max": 0.99},
                    {"id": "angle", "label": T("direction, °"), "type": "float", "default": 0.0, "min": -180.0,
                     "max": 180.0}]}

    def _actions_now(self):
        """The scenario's actions with the current velocities in the live speed control."""
        return [self._act_boost() if a.get("name") == "boost" else a for a in self.scn["actions"]]

    def _act_measure(self, label):
        pred = (lambda o: o.apparatus is not None) if self.world.flat else (lambda o: o.kind in ("observer", "station"))
        return {"name": "measure", "label": label, "args": [
            {"id": "obj", "label": T("Who"), "type": "select", "options": self._objs(pred)}]}

    def _act_train(self):
        return {"name": "train", "label": T("Pulse train (frequency)"), "args": [
            {"id": "obj", "label": T("Source"), "type": "select", "options": self._objs(lambda o: o.kind != "star")},
            {"id": "period", "label": T("Period by the source's clock, s"), "type": "float", "default": 1.0},
            {"id": "count", "label": T("How many"), "type": "int", "default": 5}]}

    def action(self, name, args):
        w = self.world
        t = self.t
        if name == "flash":
            w.flash(args["obj"], t)
            return T("{obj}: flash", obj=w.objects[args["obj"]].name)
        if name == "flash_all":
            n = 0
            for o in list(w.objects.values()):
                if o.kind == "beacon":
                    w.flash(o.id, t, label=T("flash of the source"))
                    n += 1
            return T("flash of all sources: {n:d}", n=n)
        if name == "boost":
            unit = {"c": self.laws.c, "kms": 1e3, "ms": 1.0}[args.get("unit", "c")]
            sp = float(args["v"]) * unit
            a = math.radians(float(args.get("angle", 0.0)))
            try:
                w.boost(args["obj"], [sp * math.cos(a), sp * math.sin(a)], t)
            finally:  # the speed control shows the velocity in force (also after a refused boost)
                self._msg({"type": "actions", "t": t, "actions": self._actions_now()})
            return T("{obj}: speed {v:.6g} m/s ({b:.6g} c), {a:.4g}°", obj=w.objects[args["obj"]].name, v=sp,
                     b=sp / self.laws.c, a=math.degrees(a))
        if name == "measure":
            return w.measure(args["obj"], t)
        if name == "train":
            period = float(args["period"])
            count = int(args["count"])
            if not (period > 0 and 1 <= count <= 200):
                raise Refusal(T("a pulse train needs a period > 0 and from {lo:d} to {hi:d} pulses", lo=1, hi=200),
                              hint=T("set a positive period and a count from {lo:d} to {hi:d}", lo=1, hi=200))
            w.start_train(args["obj"], t, period, count)
            return T("{obj}: a pulse train, pulses: {n:d}, period {period}", obj=w.objects[args["obj"]].name,
                     n=count, period=fmt_s(period))
        raise Refusal(T("unknown action “{name}”", name=str(name)))

    def engine_modules(self):
        L = self.laws
        mods = ["core.constants", "core.worldlines", "core.gravity.rays", "core.gravity.arrivals", "laws.light"]
        mods.append("core.relativity" if L.relativistic else "theories.alternatives.kinematics")
        if L.gravity == "GR":
            mods.append("core.gravity.schwarzschild")
        elif L.gravity == "newton":  # light as Newtonian corpuscles: a refuted alternative (review 2026-10-23, E9)
            mods.append("theories.alternatives.newton_light")
        return mods

    # --- contract -------------------------------------------------------------------------------------
    def header(self):
        w = self.world
        objs = []
        for o in w.objects.values():
            objs.append({"id": o.id, "name": o.name, "kind": o.kind, "color": o.color, "radius": o.radius,
                         "movable": o.movable, "apparatus": o.apparatus is not None, "wl": o.wl.to_json(),
                         "L0": o.apparatus.L0 if o.apparatus else None})
        body = None
        if w.body:
            body = {"gm": w.gm, "radius": w.body.get("radius", 0.0), "rs": w.rs, "r_abs": w.r_abs,
                    "name": w.body.get("name", "")}
        mods = SCHEMA.modifications(self.params)
        if self.params["scenario"] != "lensing" and self.params["scenario"] != "sun_earth":
            mods = [m for m in mods if m["id"] != "gravity"]  # no mass in the scene: gravity is irrelevant
        return {
            "title": dict(SCN)[self.params["scenario"]],
            "scenario": self.params["scenario"],
            "text": self.scn["text"],
            "laws": {"kinematics": self.laws.kinematics, "gravity": self.laws.gravity, "c": self.laws.c,
                     "c_factor": self.laws.c_factor,
                     "kinematics_label": dict(KINEMATICS)[self.laws.kinematics],
                     "gravity_label": dict(GRAVITY)[self.laws.gravity]},
            "modifications": mods,
            "objects": objs, "body": body,
            "flat": w.flat, "gr": w.gr,
            "scene": {"center": w.scene_center.tolist(), "radius": w.scene_radius},
            "view": self.scn["view"], "diagram": self.scn["diagram"], "planned": self.planned,
            "actions": self._actions_now(),
            "units": {"au": AU, "ly": LIGHT_YEAR, "rs": self.scn["view"].get("rs", w.rs)},
        }, {}

    def advance(self, t_target):
        self.world.advance(t_target)
        self.t = t_target

    def frame(self):
        return self.world.frame_state(self.t), {}

    def next_event_time(self):
        return self.world.next_event_time()


VIZ = {
    "id": "v01_light_travel",
    "title": T("Light over large distances"),
    "summary": T("The finite speed of light from the Sun to the Earth, light cones, gravitational deflection, the "
                 "speed of light measured by moving observers, the relativity of simultaneity (the Andromeda "
                 "paradox)."),
    "purpose": T("A study of the light cone, the invariance of the speed of light and the Andromeda paradox; the laws "
                 "can be changed on purpose (an ether, ballistic light, Newtonian corpuscles, another c)."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
