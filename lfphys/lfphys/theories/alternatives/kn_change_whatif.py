# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""What if a Kerr-Newman hole's spin or charge changed at an instant under moving test bodies: a declared rule that
carries the bodies over into the new metric (plan P16.1, the p01 playground's “what if”; review LB1-physics P5, P6).

Why outside the core. General relativity has no dynamics in which a stationary vacuum hole's spin or charge jumps
while test bodies move around it: a real hole changes them only through what falls in or is radiated, at finite rates,
and the bodies then move in a time-dependent metric, not in two stationary ones glued at one moment. So the change is
a model, and how the bodies are matched across it is a CHOICE, declared here.

The rule. At the coordinate time t of the change, every body (a timelike test body or a photon of
``core.gravity.kerr_newman.Geodesics``) keeps

* its Boyer-Lindquist coordinates (r, theta, phi) — the main caveat: BL coordinates of different (a, Q) do NOT label
  the same physical places (at fixed r the circumferential radius varpi = sqrt(A/Sigma) sin theta, the proper distance
  to the horizon and the area of the r-sphere all change), so the rule depends on the coordinates; keeping the
  circumferential radius instead, or keeping E, L and Carter's K, are equally defensible rules that give different
  worlds (``carry`` reports how much varpi changed at the bodies);
* its proper time (the clock it carries);
* the momentum the local zero-angular-momentum observer (ZAMO; Bardeen, Press & Teukolsky 1972, Eqs. 3.9-3.10) measures:
  the frame components p^(r), p^(theta), p^(phi) (gamma v per unit rest mass; a photon's in units of its ``nu``) are
  kept and the frame energy p^(t) is taken from the mass shell, sqrt(mu^2 + |p^(i)|^2). So the ZAMO-measured velocity
  is kept up to the body's own mass-shell drift and rounding, with no limit below c (a body falling through gamma ~ 10^2
  near the horizon keeps it), and a photon keeps its direction and its ZAMO-measured frequency.

Its covariant momentum in the new metric follows (``kerr_newman.momentum_from_frame``): new E, L, p_r, p_theta, and
with them Carter's K; the drift accounting of K and of the mass shell restarts (``Geodesics.add_state``). A body that
has been captured (stopped just outside the old horizon) stays captured, where it was or just outside the new capture
radius if that is larger; an escaped one stays escaped. Refused (``Refused``, the old world untouched): a² + Q² >= 1
(no horizon), an active body at or inside the new capture radius r+ + capture_eps.

Observers of a world (static, ZAMO, circular) keep their place; ``observer_refusal`` names a place the new metric
does not allow them (inside the new horizon; a static one inside the new ergosurface; a circular one inside the new
ISCO).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.i18n import T

from ...core.gravity import kerr_newman as KN

ABOUT = {
    "layer": "theories", "kind": "alternative",
    "title": T("What if the spin or charge of a Kerr–Newman hole changed instantly: the rule that carries test bodies "
               "over"),
    "statement": T("A declared rule (not a law): at the moment (a, Q) changes, every body keeps its Boyer–Lindquist "
                   "coordinates (r, θ, φ), its proper time and the momentum measured by the local "
                   "zero-angular-momentum observer (ZAMO; the energy from the mass shell), i.e. its velocity as well, "
                   "without capping it below c; a photon keeps the direction and the frequency measured by the ZAMO; "
                   "E, L, p_r, p_θ and the Carter constant are new; the drift accounting starts anew. Refused: a² + "
                   "Q² ≥ 1, an active body inside the new capture radius; observer positions the new metric does not "
                   "allow."),
    "validity": T("only as a declared “what if” model: it depends on the choice of coordinates, since the "
                  "Boyer–Lindquist coordinates of different (a, Q) do not label the same physical places (at the same "
                  "r the circumference √(A/Σ) sin θ, the proper distance to the horizon and the area of the sphere r "
                  "change); the rules “keep the circumference” or “keep E, L, K” are just as admissible and give "
                  "other worlds; test bodies, the hole is a background; captured bodies stay captured"),
    "basis": [T("Bardeen, Press & Teukolsky, ApJ 178, 347 (1972): ZAMO (LNRF), Eqs. (3.9)–(3.10)"),
              T("Adamo & Newman, Scholarpedia 9, 31791 (2014), arXiv:1410.6626: the Kerr–Newman metric, horizons "
                "(3.18)")],
    "conflicts": [T("lfphys.core.gravity.kerr_newman: the metric is stationary; in GR the hole's spin and charge "
                    "change only through what falls in or is radiated (at a finite speed), and the bodies move in a "
                    "time-dependent metric, not in two stationary ones glued together at one moment: an instant "
                    "change has no established dynamics; no experiment tests this rule: it is a declared "
                    "counterfactual scenario"),
                  T("the rule depends on the coordinates (Boyer–Lindquist): “the same place” in another metric is a "
                    "choice")],
}


class Refused(ValueError):
    """A change the rule cannot make: ``key`` the body concerned (None for the hole); the text and ``hint`` (what to
    change) are translatable texts (``lfphys.i18n.T``)."""

    def __init__(self, text: T, key=None, hint: T | None = None):
        super().__init__(text)
        self.key, self.hint = key, hint


def check_hole(chi: float, q: float):
    """Refuse a hole the rule cannot carry bodies into: a² + Q² >= 1 (no horizon), a < 0 (the engine's convention)."""
    chi, q = float(chi), float(q)
    if not (math.isfinite(chi) and math.isfinite(q)):
        raise Refused(T("spin and charge must be finite numbers"))
    if chi < 0.0:
        raise Refused(T("spin a = {a} < 0: the direction of rotation is set by the azimuth (a ≥ 0)", a=chi))
    if chi * chi + q * q >= 1.0:
        raise Refused(T("a² + Q² = {s:.4g} is not below 1: the hole would have no horizon (a naked singularity)",
                        s=chi * chi + q * q), hint=T("a smaller spin or charge"))


def observer_refusal(kind: str, r: float, theta: float, chi: float, q: float):
    """Why an observer of ``kind`` ("static", "zamo", "circular") cannot stay at (r, theta) in the metric (chi, q):
    (text, hint) as translatable texts (``lfphys.i18n.T``), or None. Inside the horizon (with a margin of 1e-6 r+); a static one inside the
    ergosurface (no static observer there); a circular one inside the ISCO (its orbit unstable)."""
    r_plus = KN.horizons(chi, q)[0]
    if not r > r_plus * (1.0 + 1e-6):
        return T("would end up under the new horizon"), T("spin or charge closer to the previous values")
    if kind == "static" and not np.isfinite(KN.static_clock_rate(r, theta, chi, q)):
        return (T("a static observer would end up inside the new ergosphere"),
                T("a smaller spin or the observer farther out"))
    if kind == "circular":
        risco = KN.isco(chi, q, True)
        if r < risco:
            return (T("an observer on a circular orbit would end up inside the new ISCO ({r:.4g} G M/c²)",
                      r=float(risco)),
                    T("a larger spin or the observer farther out"))
    return None


def carry(geo: KN.Geodesics, chi: float, q: float) -> dict:
    """The bodies of ``geo`` (at its time t) carried into the metric (chi, q) by the rule of the module's docstring.

    Returns {"geodesics": the new ``Geodesics`` (same keys in the same order, same t, rtol, capture_eps, r_escape),
    "r_plus": the new outer horizon, "bodies": [{key, status, photon, r, r_new, E, L, K (before), E_new, L_new, K_new,
    v (|v| the ZAMO measured), gamma (its frame energy per unit rest mass; a photon's frequency nu), varpi, varpi_new
    (the circumferential radius at the body's coordinates before and after)}], "max_dE": the largest |E_new - E| / |E|,
    "max_dvarpi": the largest |varpi_new / varpi - 1|}. ``geo`` is not changed. Raises ``Refused``."""
    check_hole(chi, q)
    chi, q = float(chi), float(q)
    r_plus = KN.horizons(chi, q)[0]
    eps = geo.capture_eps
    new = KN.Geodesics(chi, q, rtol=geo.rtol, t=geo.t, capture_eps=eps, r_escape=geo.r_escape)
    out = {"geodesics": new, "r_plus": r_plus, "bodies": [], "max_dE": 0.0, "max_dvarpi": 0.0}
    if geo.n == 0:
        return out
    bl, tau, st, photon, pm = geo.bl(), geo.proper_time(), geo.status(), geo.is_photon(), geo.momenta()
    c0 = geo.constants()
    for i, k in enumerate(geo.keys):
        r, th, ph = (float(c) for c in bl[i])
        if st[i] == "active" and not r > r_plus + eps:
            raise Refused(T("a body at r = {r:.6g} G M/c² would end up under the new horizon or at the capture "
                            "radius (r₊ = {r_plus:.6g}, capture at r₊ + {eps})", r=r, r_plus=float(r_plus),
                            eps=float(eps)), key=k,
                          hint=T("spin or charge closer to the previous values, or remove this body first"))
        r_new = max(r, r_plus + eps) if st[i] == "captured" else r
        mu2 = 0.0 if photon[i] else 1.0
        hat = KN.zamo_frame_momentum(r, th, geo.chi, geo.q, pm[i])
        sp = hat[1:]
        e = math.sqrt(mu2 + float(sp @ sp))
        p_new = KN.momentum_from_frame(r_new, th, chi, q, np.array([e, *sp]))
        new.add_state(r_new, th, ph, p_new, mu2, key=k, tau=float(tau[i]), status=st[i])
        w0 = float(KN.zamo(r, th, geo.chi, geo.q)["varpi"])
        w1 = float(KN.zamo(r_new, th, chi, q)["varpi"])
        out["bodies"].append({"key": k, "status": st[i], "photon": bool(photon[i]), "r": r, "r_new": r_new,
                              "E": float(c0["E"][i]), "L": float(c0["L"][i]), "K": float(c0["K"][i]),
                              "v": float(math.sqrt(float(sp @ sp)) / e), "gamma": e, "varpi": w0, "varpi_new": w1})
    c1 = new.constants()
    for i, b in enumerate(out["bodies"]):
        b.update(E_new=float(c1["E"][i]), L_new=float(c1["L"][i]), K_new=float(c1["K"][i]))
        out["max_dE"] = max(out["max_dE"], abs(b["E_new"] - b["E"]) / max(abs(b["E"]), 1e-300))
        out["max_dvarpi"] = max(out["max_dvarpi"], abs(b["varpi_new"] / b["varpi"] - 1.0))
    return out
