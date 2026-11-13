# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""What if the black hole is not Kerr: the shadow of the Johannsen (2013) Kerr-like metric (the "JP metric" of the
EHT papers) against the EHT measurements of M87* and Sgr A* (plan P7, the what-if of P14.3).

Why this metric. It is a published parametrized deviation from Kerr that (i) keeps a Carter-like constant, so the
edge of its shadow follows from closed conditions R(r) = R'(r) = 0 exactly like Bardeen's (Johannsen 2013b,
ApJ 777, 170, Eqs. 26-30 and Appendix Eq. 1 for xi(r)); (ii) is regular outside its horizon where the conditions of
Johannsen 2013a (PRD 88, 044002) Eqs. (72) and (76)-(78) hold (``check_regular``); and (iii) is the one the EHT used to turn its
shadow sizes into bounds (Psaltis et al. 2020, PRL 125, 141104: M87*; EHT 2022, ApJL 930, L17, Sgr A* Paper VI,
Sec. 5.1 and Table 3), so the comparison can be checked against their published numbers.

The metric (Johannsen 2013a Eqs. 51-56; M = 1): Kerr with the deviation functions A1(r) = 1 + alpha13/r^3 + ...
(Johannsen's series starts at n = 3, his Eq. 52), A2(r) = 1 + alpha22/r^2, A5(r), f(r). The term alpha12/r^2 of A1
is not Johannsen's: it is the 1PN term of the EHT's non-spinning form, Sgr A* Paper VI Eq. (17),
g_tt = -(1 - 2/r)(1 + sum_{i=2} alpha_1i/r^i)^-2, kept here for its Table 3 bound; with alpha12 the regularity
conditions are applied as the same inequalities (Eqs. 72, 76), not as Johannsen derived them. For photons (E = 1) the radial potential is (Johannsen 2013a
Eq. 23 with mu = 0; 2013b Eq. 29)

    R(r) = [(r^2 + a^2) A1(r) - a A2(r) lambda]^2 - Delta [(lambda - a)^2 + eta],

and the polar potential is Kerr's, so the screen coordinates are Bardeen's: alpha = -lambda/sin(i),
beta = +-sqrt(eta + a^2 cos^2 i - lambda^2 cot^2 i) (2013b Eqs. 26-27). A5 and f(r) do not change where R and R'
vanish, so the shadow depends only on (a, alpha12, alpha13, alpha22). The double root gives, with
P = (r^2 + a^2) A1 - a A2 lambda (derived here; equal to 2013b App. Eq. 1, tested):

    lambda(r) = [Delta' (r^2 + a^2) A1 - 2 Delta ((r^2 + a^2) A1)'] / (a [Delta' A2 - 2 Delta A2']),
    eta(r) = P^2/Delta - (lambda - a)^2.

Non-spinning (a = 0): the shadow is the circle of radius b_c = min_r r A1(r)/sqrt(1 - 2/r) (EHT 2022 Paper VI
Eqs. 15-17: r_sh = r_ph/sqrt(-g_tt(r_ph)) with g_tt = -(1 - 2/r) A1^-2).

Shadow size as the EHT defines it (Sgr A* Paper VI Eq. 14): delta = d/(6 sqrt 3) - 1, d the median diameter of
the critical curve (twice the median distance from a centre at equally spaced angles). The centre is a convention
(``shadow_size``): by default half-way between the extreme alpha (it reproduces Paper VI's Kerr range
[-0.075, 0]); CHARM's variance-minimising centre is also reported, and differs by up to 0.053 in delta for
high-spin, edge-on Kerr shadows. The deviating metric's own photon orbits and ISCO: ``circular_orbits``. Checks of the published bounds (reproduced,
tests): |delta| <= 0.17 for M87* gives -3.56 < alpha13 < 5.89 at a = 0 (Psaltis et al. 2020: "-3.6 < alpha13 <
5.9"); the Keck bound of Sgr A* (Paper VI Eq. 12: 3 sqrt 3 (1 - 0.14) <= r_sh <= 3 sqrt 3 (1 + 0.05)) gives
-3.06 < alpha13 < 1.45 and -1.14 < alpha12 < 0.47 (Table 3: "-3.1 <~ alpha13 <~ 1.5", "-1.1 <~ alpha12 <~ 0.5").
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.i18n import T
from lfphys.codes import coded

from ...core import data as D
from ...core.gravity import kerr_null as KN

ABOUT = {
    "layer": "theories", "kind": "alternative",
    "title": T("What if the hole is not Kerr: the shadow of the Johannsen metric against the EHT data"),
    "statement": T("A parametrised deviation from Kerr (the Johannsen metric of 2013, “JP” in the EHT papers) with "
                   "the parameters α₁₂, α₁₃, α₂₂: the edge of the shadow from the conditions R = R′ = 0 (as for "
                   "Bardeen), its size (the median diameter, δ as defined by the EHT) and shape (offset, spread of "
                   "diameters) as functions of the deviation; the allowed regions of the parameters from the EHT "
                   "measurements of M87* and Sgr A*."),
    "validity": T("geometric optics; regular metrics only: outside the horizon (r ≥ r₊) the determinant factor "
                  "A₁(r²+a²) − a²A₂ sin²θ (Johannsen 2013a, eq. 72), the condition of no closed timelike curves (eq. "
                  "76) and A₁, A₂ (eqs. 77–78) are positive, which is checked; one band of photon orbits; the size of "
                  "the shadow is the median diameter about the midpoint between the extreme α (the CHARM centre is a "
                  "second measure); at α = 0 it is Kerr"),
    "basis": ["Johannsen, Phys. Rev. D 88, 044002 (2013)", "Johannsen, ApJ 777, 170 (2013)",
              "Psaltis et al. (EHT), Phys. Rev. Lett. 125, 141104 (2020)",
              "EHT Collaboration, ApJL 930, L17 (2022): Sgr A* Paper VI",
              T("EHT Collaboration, ApJL 875, L1 and L6 (2019): M87* Papers I, VI")],
    "conflicts": [T("lfphys.core.gravity.kerr_null: the Kerr metric (the no-hair theorem); at α ≠ 0 the shadow has "
                    "another size and shape; bounded by the EHT: M87* |δ| ≤ 0.17 (−3.6 < α₁₃ < 5.9 at a = 0, Psaltis "
                    "et al. 2020), Sgr A* (Keck) −3.1 ≲ α₁₃ ≲ 1.5 (EHT 2022, Table 3)")],
}

SCHWARZSCHILD_DIAMETER = 6.0 * math.sqrt(3.0)


class Deviation:
    """Deviation parameters (alpha12, alpha13, alpha22) of A1 = 1 + alpha12/r^2 + alpha13/r^3, A2 = 1 + alpha22/r^2."""

    def __init__(self, alpha12=0.0, alpha13=0.0, alpha22=0.0):
        self.a12, self.a13, self.a22 = float(alpha12), float(alpha13), float(alpha22)

    def A1(self, r):
        return 1.0 + self.a12 / r ** 2 + self.a13 / r ** 3

    def dA1(self, r):
        return -2.0 * self.a12 / r ** 3 - 3.0 * self.a13 / r ** 4

    def A2(self, r):
        return 1.0 + self.a22 / r ** 2

    def dA2(self, r):
        return -2.0 * self.a22 / r ** 3

    @property
    def is_kerr(self):
        return self.a12 == 0.0 and self.a13 == 0.0 and self.a22 == 0.0


def regularity_margins(chi, dev: Deviation, r=None) -> dict:
    """The quantities that must stay positive on and outside the horizon (r >= r+), at the worst latitude:
    * Johannsen 2013a Eq. (72), the determinant's factor A1 (r^2 + a^2) - a^2 A2 sin^2 theta != 0 (Eq. 71: its
      vanishing makes det g = 0); positive at infinity and linear in sin^2 theta, so positive everywhere iff it is
      positive at sin^2 theta = 0 (A1 (r^2 + a^2)) and at sin^2 theta = 1;
    * Eq. (76), no closed timelike curves: A1^2 (r^2 + a^2)^2 - a^2 Delta sin^2 theta > 0, worst at sin^2 theta = 1;
    * Eqs. (77)-(78) as Johannsen states them at lowest order, A1 > 0 and A2 > 0 (alpha13 > -r+^3, alpha22 > -r+^2;
      for alpha12, A1 > 0 is the analogue).
    Returns the minima over r in [r+, 1e4 r+] (a geometric grid of 20001 points, denser at the horizon)."""
    a = chi
    rp = KN.horizon(chi)
    r = rp * np.exp(np.linspace(0.0, math.log(1e4), 20001)) if r is None else np.asarray(r, float)
    A1, A2 = dev.A1(r), dev.A2(r)
    dl = r * r - 2.0 * r + a * a
    return {"A1": float(np.min(A1)), "A2": float(np.min(A2)),
            "det_eq72": float(np.min(A1 * (r * r + a * a) - a * a * A2)),
            "ctc_eq76": float(np.min(A1 * A1 * (r * r + a * a) ** 2 - a * a * dl))}


def check_regular(chi, dev: Deviation):
    """Raise unless the metric is regular on and outside its horizon r+ (the Kerr horizon, Johannsen 2013a Sec. III
    A): the determinant's factor of Eq. (72) and the (phi, phi) condition of Eq. (76) positive at every latitude, and
    A1, A2 > 0 (Eqs. 77-78 as stated there). Review B5-K6: A1, A2 > 0 alone admitted metrics with det g = 0 outside
    the horizon (a = 0.998: every alpha22 > r+^4/a^2 = 1.283; alpha13 = -0.95 r+^3 at a = 0.6-0.998)."""
    m = regularity_margins(chi, dev)
    bad = [k for k, v in m.items() if not v > 0.0]
    if bad:
        raise coded(ValueError(T("the metric is not regular outside the horizon (Johannsen 2013a, eqs. 72, 76–78): "
                                 "{where}", where=[T("{k} reaches {v:.3g}", k=k, v=float(m[k])) for k in bad])),
                    "jp.irregular")


def radial_potential(r, lam, eta, chi, dev: Deviation):
    a = chi
    dl = r * r - 2.0 * r + a * a
    P = (r * r + a * a) * dev.A1(r) - a * dev.A2(r) * lam
    return P * P - dl * ((lam - a) ** 2 + eta)


def photon_orbit_constants(r, chi, dev: Deviation):
    """(lambda, eta) of the spherical photon orbit at radius r (a > 0)."""
    a = chi
    r = np.asarray(r, float)
    dl = r * r - 2.0 * r + a * a
    dlp = 2.0 * r - 2.0
    w = (r * r + a * a) * dev.A1(r)
    wp = 2.0 * r * dev.A1(r) + (r * r + a * a) * dev.dA1(r)
    lam = (dlp * w - 2.0 * dl * wp) / (a * (dlp * dev.A2(r) - 2.0 * dl * dev.dA2(r)))
    P = w - a * dev.A2(r) * lam
    return lam, P * P / dl - (lam - a) ** 2


def nonspinning_shadow(dev: Deviation):
    """(b_c, r_ph): shadow radius and photon-sphere radius of the non-spinning metric: b(r) = r A1/sqrt(1 - 2/r) is
    minimal at r_ph (Psaltis et al. 2020 Eqs. 3-4; EHT 2022 Paper VI Eqs. 15-17)."""
    from scipy.optimize import brentq

    def db(r):  # d/dr ln b = 1/r + A1'/A1 - 1/(r^2 (1 - 2/r))
        return 1.0 / r + dev.dA1(r) / dev.A1(r) - 1.0 / (r * r - 2.0 * r)

    # the outermost sign change of db from - to + outside r = 2
    rs = np.linspace(2.0 + 1e-9, 40.0, 40001)
    v = db(rs)
    idx = np.nonzero((v[:-1] < 0) & (v[1:] >= 0))[0]
    if idx.size != 1:
        raise coded(ValueError(T("not a single photon sphere outside the horizon for these parameters")),
                    "jp.photon_sphere")
    i = idx[0]
    r_ph = brentq(db, rs[i], rs[i + 1], xtol=1e-15, rtol=8.9e-16, maxiter=200)
    return float(r_ph * dev.A1(r_ph) / math.sqrt(1.0 - 2.0 / r_ph)), float(r_ph)


def photon_shell(chi, dev: Deviation):
    """(r_pro, r_retro): radii of the circular equatorial photon orbits (eta(r) = 0) bounding the shell where
    eta > 0 (a > 0); the Kerr shell when dev is zero."""
    from scipy.optimize import brentq
    rp = KN.horizon(chi)
    rs = np.linspace(rp * (1.0 + 1e-6), 12.0, 40001)
    _, eta = photon_orbit_constants(rs, chi, dev)
    pos = eta > 0
    edges = np.nonzero(pos[:-1] != pos[1:])[0]
    if edges.size != 2 or not pos[edges[0] + 1]:
        raise coded(ValueError(T("the photon shell is not a single band between r+ and 12 M for these parameters")),
                    "jp.photon_sphere")

    def f(r):
        return float(photon_orbit_constants(np.array(r), chi, dev)[1])

    lo = brentq(f, rs[edges[0]], rs[edges[0] + 1], xtol=1e-15, rtol=8.9e-16, maxiter=200)
    hi = brentq(f, rs[edges[1]], rs[edges[1] + 1], xtol=1e-15, rtol=8.9e-16, maxiter=200)
    return lo, hi


def _equatorial_metric(r, chi, dev: Deviation):
    """g_tt, g_tphi, g_phiphi in the equatorial plane and their r-derivatives (Johannsen 2013a Eq. 51 at
    sin theta = 1, f = 0): with W = (r^2 + a^2) A1 - a^2 A2, g_tt = -r^2 (Delta - a^2 A2^2)/W^2,
    g_tphi = -a r^2 [(r^2 + a^2) A1 A2 - Delta]/W^2, g_phiphi = r^2 [(r^2 + a^2)^2 A1^2 - a^2 Delta]/W^2. Plain
    arithmetic, so complex r is accepted (complex-step derivatives)."""
    a = chi
    A1, A2, dA1, dA2 = dev.A1(r), dev.A2(r), dev.dA1(r), dev.dA2(r)
    dl, ddl = r * r - 2.0 * r + a * a, 2.0 * r - 2.0
    s2 = r * r + a * a
    W = s2 * A1 - a * a * A2
    dW = 2.0 * r * A1 + s2 * dA1 - a * a * dA2
    D, dD = W * W, 2.0 * W * dW
    ntt = -r * r * (dl - a * a * A2 * A2)
    dntt = -2.0 * r * (dl - a * a * A2 * A2) - r * r * (ddl - 2.0 * a * a * A2 * dA2)
    ntp = -a * r * r * (s2 * A1 * A2 - dl)
    dntp = -a * (2.0 * r * (s2 * A1 * A2 - dl) + r * r * (2.0 * r * A1 * A2 + s2 * (dA1 * A2 + A1 * dA2) - ddl))
    npp = r * r * (s2 * s2 * A1 * A1 - a * a * dl)
    dnpp = 2.0 * r * (s2 * s2 * A1 * A1 - a * a * dl) + r * r * (4.0 * r * s2 * A1 * A1 + 2.0 * s2 * s2 * A1 * dA1
                                                                   - a * a * ddl)
    g = (ntt / D, ntp / D, npp / D)
    dg = ((dntt * D - ntt * dD) / (D * D), (dntp * D - ntp * dD) / (D * D), (dnpp * D - npp * dD) / (D * D))
    return g, dg


def _circular(r, chi, dev, prograde):
    """(Omega, -(g_tt + 2 g_tphi Omega + g_phiphi Omega^2), E, L) of the circular equatorial geodesic at r:
    Omega by Johannsen 2013a Eq. (83) (upper sign prograde), E = -u_t, L = u_phi."""
    (gtt, gtp, gpp), (dtt, dtp, dpp) = _equatorial_metric(r, chi, dev)
    s = 1.0 if prograde else -1.0
    disc = dtp * dtp - dtt * dpp
    if disc.real < 0.0:
        # Omega^2 < 0: no circular geodesic at this radius. A deviating metric can have such a band, where the
        # effective gravity is repulsive (e.g. a = 0, alpha12 = -3, alpha13 = -1.4: between 2.1 M and 4.6 M); a
        # real r gave a complex Omega there, and float() of its E crashed (review UX-params P6)
        return math.nan, math.nan, math.nan, math.nan
    om = (-dtp + s * disc ** 0.5) / dpp
    norm = -(gtt + 2.0 * gtp * om + gpp * om * om)
    if not isinstance(norm, complex) and not norm > 0.0:  # at or inside the circular photon orbit: no timelike orbit
        return om, norm, math.nan, math.nan
    ut = norm ** -0.5
    return om, norm, -(gtt + gtp * om) * ut, (gtp + gpp * om) * ut


def circular_orbits(chi, dev: Deviation | None = None) -> dict:
    """The deviating metric's own equatorial circular orbits (review B5-K7): ``photon_pro``, ``photon_retro`` (the
    circular photon orbits, where u^t of the circular geodesic diverges: g_tt + 2 g_tphi Omega + g_phiphi Omega^2 = 0)
    and ``isco_pro``, ``isco_retro`` (the innermost stable circular orbits, where E(r) of the circular orbits is
    minimal: dE/dr = 0), with ``E_isco_*``, ``L_isco_*``. Omega from Johannsen 2013a Eq. (83); the metric functions
    and their r-derivatives in closed form; dE/dr by the complex-step derivative of E(r) (exact to round-off); the
    roots by Brent's method to 1e-14 relative. Not closed forms (Johannsen 2013a Sec. IV computes them the same way,
    numerically); the Kerr values (``kerr.photon_orbit``, ``kerr.isco``) are reproduced at zero deviation (tests).
    At a = 0 both senses coincide (the photon sphere of ``nonspinning_shadow``). The ISCO is the inner edge of the
    stable circular orbits connected to infinity: where dE/dr = 0 (``isco_kind_*`` = "stability"), or, where a
    deviation makes a band without circular geodesics (Omega^2 < 0, the effective gravity repulsive), that band's
    outer edge (Omega^2 = 0, a static orbit; "existence"). Raises ValueError (a translatable text with a machine
    code, ``lfphys.codes``) when a photon orbit or the ISCO is not found."""
    from scipy.optimize import brentq
    dev = dev or Deviation()
    check_regular(chi, dev)
    rp = KN.horizon(chi)
    out = {}
    for pro, name in ((True, "pro"), (False, "retro")):
        def norm(r):
            return float(_circular(r, chi, dev, pro)[1].real)
        rs = rp * np.exp(np.linspace(1e-7, math.log(60.0 / rp), 6001))
        vals = np.array([norm(r) for r in rs])
        pos = np.nonzero((vals[:-1] <= 0) & (vals[1:] > 0))[0]
        if pos.size == 0:
            raise coded(ValueError(T("no prograde circular photon orbit between r+ and 60 M") if pro else
                                   T("no retrograde circular photon orbit between r+ and 60 M")), "jp.no_photon_orbit")
        i = pos[-1]
        r_ph = brentq(norm, rs[i], rs[i + 1], xtol=1e-15, rtol=8.9e-16, maxiter=200)

        def dE(r):
            h = 1e-20 * max(1.0, r)
            E = _circular(complex(r, h), chi, dev, pro)[2]
            return E.imag / h if isinstance(E, complex) else math.nan  # a float NaN: no circular geodesic here
        grid = r_ph * np.exp(np.linspace(1e-6, math.log(200.0 / r_ph), 4001))
        d = np.array([dE(r) for r in grid])  # NaN where no circular geodesic exists (Omega^2 < 0)
        # the stable circular orbits connected to infinity (where a disk's gas comes from): inward from 200 M while
        # they exist and dE/dr >= 0; the ISCO is where that region ends - by stability (dE/dr = 0: Kerr and small
        # deviations) or by existence (Omega^2 = 0 at the edge of a repulsive band: the orbit there is static)
        stable = np.isfinite(d) & (d >= 0)
        if not stable[-1]:
            raise coded(ValueError(T("no stable prograde circular orbit at 200 M") if pro else
                                   T("no stable retrograde circular orbit at 200 M")), "jp.no_stable_orbit")
        bad = np.nonzero(~stable)[0]
        if bad.size == 0:
            raise coded(ValueError(T("no prograde ISCO between the photon orbit and 200 M") if pro else
                                   T("no retrograde ISCO between the photon orbit and 200 M")), "jp.no_isco")
        j = int(bad[-1])
        if np.isfinite(d[j]):
            r_isco = brentq(dE, grid[j], grid[j + 1], xtol=1e-14 * grid[j + 1], rtol=8.9e-16, maxiter=200)
            kind = "stability"
        else:
            def disc(r):
                _, (dtt, dtp, dpp) = _equatorial_metric(r, chi, dev)
                return dtp * dtp - dtt * dpp
            r_isco = brentq(disc, grid[j], grid[j + 1], xtol=1e-14 * grid[j + 1], rtol=8.9e-16, maxiter=200)
            while disc(r_isco) < 0.0:  # the edge's own side, where the orbit exists
                r_isco = float(np.nextafter(r_isco, math.inf))
            kind = "existence"
        _, _, E, L = _circular(r_isco, chi, dev, pro)
        out.update({f"photon_{name}": r_ph, f"isco_{name}": r_isco, f"E_isco_{name}": float(E),
                    f"L_isco_{name}": float(L), f"isco_kind_{name}": kind})
    return out


def ergosurface(chi, dev: Deviation, theta):
    """The outer boundary of the ergoregion, r_E(theta) (the deviating metric's own, for drawing it; review B5-K7):
    where g_tt = 0 (Johannsen 2013a Eq. 68), i.e. "Delta - a^2 A2(r)^2 sin^2 theta = 0" (his Eq. 69: it depends on
    the spin and A2 only, and meets the horizon at the poles). The outermost root above r+ by a vectorized bisection
    (the left side is positive beyond it: Delta ~ r^2 against a^2 A2^2 sin^2 theta -> a^2 sin^2 theta); Kerr:
    1 + sqrt(1 - a^2 cos^2 theta)."""
    check_regular(chi, dev)
    a = chi
    theta = np.asarray(theta, dtype=float)
    s2 = np.sin(theta.ravel()) ** 2
    rp = KN.horizon(chi)

    def f(r, s2):
        return r * r - 2.0 * r + a * a - a * a * dev.A2(r) ** 2 * s2

    # the outermost grid point where f <= 0 on a geometric grid out to 1e3 r+ (f(r+) <= 0 always), then a bisection
    # between it and the next point to adjacent doubles
    rs = rp * np.exp(np.linspace(0.0, math.log(1e3), 4001))
    neg = f(rs[:, None], s2[None, :]) <= 0.0
    at_horizon = ~neg.any(axis=0)  # f(r+) = -a^2 A2^2 sin^2 theta rounded to >= 0 (the poles): r_E = r+
    last = np.minimum(rs.size - 1 - np.argmax(neg[::-1], axis=0), rs.size - 2)
    last = np.where(at_horizon, 0, last)
    lo, hi = rs[last], rs[last + 1]
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        live = (mid > lo) & (mid < hi)
        if not live.any():
            break
        pos = f(mid, s2) > 0.0
        hi = np.where(live & pos, mid, hi)
        lo = np.where(live & ~pos, mid, lo)
    r = np.where(at_horizon, rp, np.where(f(lo, s2) == 0.0, lo, 0.5 * (lo + hi)))
    return float(r[0]) if theta.ndim == 0 else r.reshape(theta.shape)


def shadow_curve(chi, theta_o, dev: Deviation | None = None, n=721):
    """The edge of the shadow on the screen of an observer at inclination theta_o (radians): dict ``alpha``,
    ``beta`` (closed curve), ``r`` (bound-orbit radius behind each point). a = 0: the circle of radius b_c."""
    from scipy.optimize import brentq
    dev = dev or Deviation()
    check_regular(chi, dev)
    if dev.is_kerr and chi > 0.0:
        return KN.critical_curve(chi, theta_o, n)
    if chi == 0.0:
        b, r_ph = nonspinning_shadow(dev)
        ph = np.linspace(0.0, 2.0 * math.pi, n)
        return {"alpha": b * np.cos(ph), "beta": b * np.sin(ph), "r": np.full(n, r_ph)}
    th = min(theta_o, math.pi - theta_o)
    s, c = math.sin(th), math.cos(th)
    a = chi
    r_lo, r_hi = photon_shell(chi, dev)

    def beta2(r):
        lam, eta = photon_orbit_constants(np.asarray(r, float), chi, dev)
        return eta + a * a * c * c - lam * lam * c * c / (s * s)

    rr = np.linspace(r_lo, r_hi, 4001)
    b2 = beta2(rr)
    pos = np.nonzero(b2 >= 0)[0]
    if pos.size == 0:
        raise coded(ValueError(T("no bound orbit is visible at this inclination")), "jp.no_bound_orbit")
    i0, i1 = pos[0], pos[-1]
    f = lambda r: float(beta2(r))  # noqa: E731
    lo = r_lo if i0 == 0 else brentq(f, rr[i0 - 1], rr[i0], xtol=1e-15, rtol=8.9e-16, maxiter=200)
    hi = r_hi if i1 == rr.size - 1 else brentq(f, rr[i1], rr[i1 + 1], xtol=1e-15, rtol=8.9e-16, maxiter=200)
    m = max(8, n // 2)
    r = lo + (hi - lo) * 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, m)))
    lam, eta = photon_orbit_constants(r, chi, dev)
    al = -lam / s
    be = np.sqrt(np.maximum(eta + a * a * c * c - lam * lam * c * c / (s * s), 0.0))
    return {"alpha": np.concatenate((al, al[::-1][1:])), "beta": np.concatenate((be, -be[::-1][1:])),
            "r": np.concatenate((r, r[::-1][1:]))}


def _radius_at(alpha, beta, cx, angle):
    """Distance from (cx, 0) to the closed polygon (alpha, beta) along ``angle`` (the outermost crossing)."""
    return float(_radii(alpha, beta, cx, np.array([angle]))[0])


def _radii(alpha, beta, cx, angles):
    """Distances from (cx, 0) to the closed polygon along each of ``angles`` (the outermost crossings)."""
    ux, uy = np.cos(angles)[:, None], np.sin(angles)[:, None]
    x0, y0 = (alpha[:-1] - cx)[None, :], beta[:-1][None, :]
    ex, ey = (alpha[1:] - alpha[:-1])[None, :], (beta[1:] - beta[:-1])[None, :]
    den = ux * ey - uy * ex
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (x0 * ey - y0 * ex) / den  # distance along the ray
        s = (x0 * uy - y0 * ux) / den  # position along the segment
    ok = (np.abs(den) > 0) & (s >= -1e-12) & (s <= 1.0 + 1e-12) & (t > 0)
    return np.max(np.where(ok, t, -np.inf), axis=1)


def _charm_minima(al, be, n_angles):
    """Centres on the symmetry axis (beta = 0) at which the variance of the diameters through them (n_angles/2
    orientations) has a local minimum: CHARM's step (iv) (EHT 2022 Sgr A* Paper VI Sec. 3) applied to the curve.
    A scan of 201 centres, each local minimum refined by Brent's method; returned as [(centre, variance), ...] sorted
    by the variance (the first is the global minimum)."""
    from scipy.optimize import minimize_scalar
    ang = 2.0 * math.pi * np.arange(n_angles) / n_angles
    half = n_angles // 2

    def var(cx):
        rad = _radii(al, be, cx, ang)
        return float(np.var(rad[:half] + rad[half:2 * half]))
    lo, hi = float(al.min()), float(al.max())
    grid = np.linspace(lo + 0.02 * (hi - lo), hi - 0.02 * (hi - lo), 201)
    vals = np.array([var(c) for c in grid])
    out = []
    for i in range(1, grid.size - 1):
        if vals[i] <= vals[i - 1] and vals[i] < vals[i + 1]:
            res = minimize_scalar(var, bounds=(grid[i - 1], grid[i + 1]), method="bounded",
                                  options={"xatol": 1e-10 * (hi - lo)})
            out.append((float(res.x), float(res.fun)))
    if not out:
        i = int(np.argmin(vals))
        out.append((float(grid[i]), float(vals[i])))
    return sorted(out, key=lambda t: t[1])


def shadow_size(curve: dict, n_angles: int = 128, charm: bool = True) -> dict:
    """Size and shape of a shadow curve. The median diameter is twice the median distance from a centre to the curve
    along ``n_angles`` equally spaced directions (EHT 2022 Sgr A* Paper VI Sec. 3, step iii; Sec. 5.1: "we define the
    size of a shadow as its median radius"; Eq. 14: delta = d/(6 sqrt 3) - 1). Two centres (review B5-K5):

    * "extremes" (``delta``, ``median_diameter``, ``center_alpha``): half-way between the extreme alpha on the
      symmetry axis. With it the Kerr shadows span delta in [-0.0704, 0] over spins <= 0.998 and all
      inclinations, the range Paper VI quotes for Kerr ("values of delta in the range [-0.075, 0] are consistent
      with the Kerr predictions", Takahashi 2004; Chan et al. 2013). This is the engine's default.
    * "charm" (``delta_charm``, ``median_diameter_charm``, ``center_alpha_charm``): a centre that minimises the
      variance of the diameters (CHARM's step iv, which Paper VI applies to images). For circles both agree. For
      spinning, inclined shadows the variance has two local minima on the symmetry axis, one on each side of the
      "extremes" centre; the global one is reported, all of them in ``charm_minima`` [(centre, variance, delta)].
      Measured (Kerr; delta at "extremes" / at the global CHARM minimum / at the other one): a = 0.5, 30 deg:
      -0.0128 / -0.0148 / -0.0147; a = 0.9, 17 deg: -0.0523 / -0.0565 / -0.0563; a = 0.9, 60 deg: -0.0380 /
      -0.0684 / -0.0650; a = 0.998, 60 deg: -0.0590 / -0.1222 / -0.1054; a = 0.998, 90 deg: -0.0530 / -0.1238 /
      -0.1050. ``delta_difference`` = charm - extremes; the convention moves delta by up to 0.07, the size of the
      Sgr A* error bars (review B5-K5).

    Also the mean radius and the radius of the circle of equal area (about the "extremes" centre), and the
    fractional spread of the diameters (standard deviation of the diameters along orientations over their mean: the
    circularity measure of EHT 2019 M87* Paper VI Sec. 7.4). ``charm`` False skips the CHARM centre (its scan
    costs ~0.5 s)."""
    al, be = np.asarray(curve["alpha"], float), np.asarray(curve["beta"], float)
    if al[0] != al[-1] or be[0] != be[-1]:
        al, be = np.append(al, al[0]), np.append(be, be[0])
    ang = 2.0 * math.pi * np.arange(n_angles) / n_angles
    half = n_angles // 2
    cx = 0.5 * (al.max() + al.min())
    rad = _radii(al, be, cx, ang)
    diam = rad[:half] + rad[half:2 * half]
    if charm:
        minima = _charm_minima(al, be, n_angles)
        cc = minima[0][0]
        rad_c = _radii(al, be, cc, ang)
        charm = [(c, v, 2.0 * float(np.median(_radii(al, be, c, ang))) / SCHWARZSCHILD_DIAMETER - 1.0)
                 for c, v in minima]
    else:
        cc, rad_c, charm = math.nan, np.full(n_angles, math.nan), []
    area = 0.5 * abs(np.sum(al[:-1] * be[1:] - al[1:] * be[:-1]))
    d_med = 2.0 * float(np.median(rad))
    d_med_c = 2.0 * float(np.median(rad_c))
    return {"center_alpha": cx, "median_diameter": d_med, "delta": d_med / SCHWARZSCHILD_DIAMETER - 1.0,
            "center_alpha_charm": cc, "median_diameter_charm": d_med_c,
            "delta_charm": d_med_c / SCHWARZSCHILD_DIAMETER - 1.0,
            "delta_difference": (d_med_c - d_med) / SCHWARZSCHILD_DIAMETER, "charm_minima": charm,
            "mean_radius": float(np.mean(rad)), "area_radius": math.sqrt(area / math.pi),
            "diameter_spread": float(np.std(diam) / np.mean(diam)), "width_alpha": float(al.max() - al.min()),
            "height_beta": float(be.max() - be.min())}


def delta(chi, theta_o, dev: Deviation | None = None, n=1441, centre="extremes"):
    """The shadow-size deviation delta = d/(6 sqrt 3) - 1 of the metric (exact circle at a = 0), with the median
    diameter about the ``centre`` "extremes" (default) or "charm" (``shadow_size``)."""
    dev = dev or Deviation()
    if centre not in ("extremes", "charm"):
        raise ValueError("centre: 'extremes' or 'charm'")
    if chi == 0.0:
        b, _ = nonspinning_shadow(dev)
        return 2.0 * b / SCHWARZSCHILD_DIAMETER - 1.0
    sz = shadow_size(shadow_curve(chi, theta_o, dev, n), charm=(centre == "charm"))
    return sz["delta"] if centre == "extremes" else sz["delta_charm"]


def delta_vs_kerr(chi, theta_o, dev: Deviation, n=1441, centre="extremes"):
    """delta of the deviating metric minus delta of the Kerr hole of the same spin and inclination: the size
    deviation from Kerr itself (the quantity a mass-to-distance test such as M87*'s, EHT 2019 Paper VI Eq. 31, bounds
    when the ring is calibrated on Kerr; Psaltis et al. 2020 use it as "consistent to within 17%")."""
    return delta(chi, theta_o, dev, n, centre) - delta(chi, theta_o, Deviation(), n, centre)


def eht_delta_bounds() -> dict:
    """The 68% intervals of delta used for the comparison, with their sources (core.data)."""
    k = D.EHT_SGRA_SHADOW_RADIUS_KECK
    v = D.EHT_SGRA_SHADOW_RADIUS_VLTI
    m = D.EHT_M87_DELTA_STELLAR
    return {"M87* (|delta| <= 0.17, Psaltis et al. 2020)": (-m[1], m[1]),
            "Sgr A* Keck (Paper VI Eq. 12)": (k[0] - 1.0, k[1] - 1.0),
            "Sgr A* VLTI (Paper VI Eq. 13)": (v[0] - 1.0, v[1] - 1.0)}


def allowed_range(param: str, bounds: tuple, chi=0.0, theta_o=math.pi / 2, others: dict | None = None,
                  search=(-8.0, 30.0)) -> dict:
    """The interval of one deviation parameter (``"alpha12"``, ``"alpha13"`` or ``"alpha22"``) around zero where
    delta stays within ``bounds`` (the others fixed): the crossings of delta(param) with the bounds nearest to zero,
    by stepping outwards and bisection. Returns {"low", "high", "low_limited", "high_limited"}: a side "limited"
    found no crossing before the metric stops being regular (or the search range ends) and reports the last regular
    value there."""
    from scipy.optimize import brentq
    others = dict(others or {})
    if param not in ("alpha12", "alpha13", "alpha22"):
        raise ValueError("param: alpha12, alpha13 or alpha22")

    def d(v):
        kw = dict(others)
        kw[param] = v
        return delta(chi, theta_o, Deviation(**kw))

    lo_b, hi_b = bounds
    d0 = d(0.0)
    if not lo_b <= d0 <= hi_b:
        raise coded(ValueError(T("zero deviation (δ = {d:.4f}) is already outside the bounds", d=float(d0))),
                    "jp.outside_bounds")
    out = {}
    for direction, key in ((-1.0, "low"), (1.0, "high")):
        step, v_prev, d_prev = 0.05, 0.0, d0
        v = direction * step
        found, last = None, 0.0
        while search[0] <= v <= search[1]:
            try:
                dv = d(v)
            except ValueError:  # left the regular / single-shell domain
                break
            for b in (lo_b, hi_b):
                if (d_prev - b) * (dv - b) <= 0.0 and d_prev != dv:
                    found = brentq(lambda t, b=b: d(t) - b, min(v_prev, v), max(v_prev, v), xtol=1e-12)
                    break
            if found is not None:
                break
            last = v
            v_prev, d_prev = v, dv
            step *= 1.3
            v = v + direction * step
        out[key] = found if found is not None else last
        out[key + "_limited"] = found is None
    return out


def shadow_computable(chi, dev: Deviation) -> str | None:
    """None when this module can compute the metric's shadow edge (regular outside the horizon, and a single photon
    sphere at a = 0 or a single band of spherical photon orbits at a > 0); otherwise the reason (English): "regular"
    (``check_regular`` fails) or "shell" (``nonspinning_shadow`` / ``photon_shell`` fail)."""
    m = regularity_margins(chi, dev)
    if not all(v > 0.0 for v in m.values()):
        return "regular"
    try:
        if chi == 0.0:
            nonspinning_shadow(dev)
        elif not dev.is_kerr:
            photon_shell(chi, dev)
    except ValueError:
        return "shell"
    return None


def admissible_intervals(chi, param: str, others: dict | None = None, lo=-10.0, hi=10.0, n=121,
                         tol=1e-4) -> list:
    """The values of one deviation parameter (``"alpha12"``, ``"alpha13"`` or ``"alpha22"``) in [lo, hi], the
    others fixed, for which ``shadow_computable`` holds: a list of closed intervals (a, b), found on a uniform grid of
    ``n`` points and their ends refined by bisection to ``tol``. For a world to say which values it can take (review
    UX-params P6); an interval narrower than the grid step can be missed (stated)."""
    if param not in ("alpha12", "alpha13", "alpha22"):
        raise ValueError("param: alpha12, alpha13 or alpha22")
    others = dict(others or {})

    def ok(v):
        kw = dict(others)
        kw[param] = float(v)
        return shadow_computable(chi, Deviation(**kw)) is None

    xs = np.linspace(lo, hi, n)
    good = [ok(x) for x in xs]

    def edge(a, b):  # ok(a) != ok(b): bisection to the change
        ga = ok(a)
        while abs(b - a) > tol:
            m = 0.5 * (a + b)
            if ok(m) == ga:
                a = m
            else:
                b = m
        return float(a if ga else b)  # the end on the admissible side

    out, start = [], None
    for i, g in enumerate(good):
        if g and start is None:
            start = float(xs[0]) if i == 0 else edge(xs[i], xs[i - 1])
        if start is not None and (not g or i == n - 1):
            end = float(xs[-1]) if g else edge(xs[i - 1], xs[i])
            out.append((start, end))
            start = None
    return out
