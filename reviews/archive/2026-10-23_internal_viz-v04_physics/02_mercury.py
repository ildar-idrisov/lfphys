"""02: Mercury preset. 50-digit references for the exact same initial data, the run's measurement, the century value,
the float references used by the checks, and whether the 'r_peri/r_apo' tolerance (~1.7e-7) is a real limitation.

Independent of the project's code: e, l, e^2 - 1 recomputed in mpmath from the same float launch data; turning points
as mp roots of the cubic; the advance by the chi-integral (script 01); the radial period in Schwarzschild t by
quadrature  t_r = 2 int_{r_p}^{r_a} (e/f) dr/sqrt(R),  r^3 R = (e^2-1)(r - r_a)(r - r_p)(r - r_3).
"""
import math
import sys
import time

import mpmath as mp
import numpy as np

from lfphys.core.constants import AU, C, DAY, GM_SUN
from lfphys.core.gravity import orbit_stream as osm
from lfphys.core.gravity import orbits
from harness import Harness
from v04_orbits import viz

mp.mp.dps = 50
out = []


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.append(s)


r0 = viz.MERCURY_R0
k = viz.MERCURY_K
v = k * math.sqrt(1.0 / (r0 - 2.0))
v_r, v_phi = 0.0, v
P("constants: GM_SUN", GM_SUN, "AU", AU, "C", C, "DAY", DAY)
P("M_sun length GM/c^2 [m]", GM_SUN / C**2, "  T_s GM/c^3 [s]", GM_SUN / C**3)
P("r0 (perihelion, M)", repr(r0), " k", repr(k), " v/c", repr(v))

# --- 50-digit constants from the same floats -----------------------------------------------------------------
R0, V = mp.mpf(r0), mp.mpf(v_phi)
g2 = 1 / (1 - V * V)
E = mp.sqrt(g2) * mp.sqrt(1 - 2 / R0)
EM1 = g2 * (V * V - 2 / R0)
L = mp.sqrt(g2) * V * R0
k_fl = osm.local_velocity_to_constants(r0, v_r, v_phi)
P("e  float", repr(k_fl["e"]), " mp", mp.nstr(E, 20), " rel", float((k_fl["e"] - E) / E))
P("em1 float", repr(k_fl["em1"]), " mp", mp.nstr(EM1, 20), " rel", float((k_fl["em1"] - EM1) / EM1))
P("e*e-1 (cancelling) float", repr(k_fl["e"] ** 2 - 1), " rel vs mp", float((k_fl["e"] ** 2 - 1 - EM1) / EM1))
P("l  float", repr(k_fl["l"]), " rel", float((k_fl["l"] - L) / L))

# turning points (u = M/r): roots of 2u^3 - u^2 + 2u/l^2 + em1/l^2
U = sorted([mp.re(z) for z in mp.polyroots([2, -1, 2 / L**2, EM1 / L**2], maxsteps=200, extraprec=200)])
u1, u2, u3 = U
ra, rp, r3 = 1 / u1, 1 / u2, 1 / u3
p_mp = 2 / (u1 + u2)
ecc_mp = (u2 - u1) / (u2 + u1)
a_mp = p_mp / (1 - ecc_mp**2)
P("mp turning points: r_peri", mp.nstr(rp, 20), " r_apo", mp.nstr(ra, 20), " r3", mp.nstr(r3, 12))
P("r_peri - r0 (rel)", mp.nstr((rp - R0) / R0, 5), " (start at the perihelion)")

# exact advance, chi-integral and elliptic integral
mu = 1 / p_mp
adv_chi = mp.quad(lambda c: 1 / mp.sqrt(1 - 2 * mu * (3 + ecc_mp * mp.cos(c))), [0, mp.pi, 2 * mp.pi]) - 2 * mp.pi
m = (u2 - u1) / (u3 - u1)
adv_ell = 4 * mp.ellipk(m) / mp.sqrt(2 * (u3 - u1)) - 2 * mp.pi
P("exact advance per orbit [rad]: chi-integral", mp.nstr(adv_chi, 20), " elliptic", mp.nstr(adv_ell, 20))

# radial period in t (M units): r = c - d cos th
cc, dd = (ra + rp) / 2, (ra - rp) / 2


def dt_dth(th):
    r = cc - dd * mp.cos(th)
    return (E / (1 - 2 / r)) * mp.sqrt(r**3 / (abs(EM1) * (r - r3)))


def dtau_dth(th):
    r = cc - dd * mp.cos(th)
    return mp.sqrt(r**3 / (abs(EM1) * (r - r3)))


t_r = 2 * mp.quad(dt_dth, [0, mp.pi / 2, mp.pi])
tau_r = 2 * mp.quad(dtau_dth, [0, mp.pi / 2, mp.pi])
T_s = mp.mpf(GM_SUN) / mp.mpf(C) ** 3
P("radial period t_r [days]", mp.nstr(t_r * T_s / DAY, 15), "  tau_r/t_r", mp.nstr(tau_r / t_r, 18))
cent_exact = adv_chi * mp.mpf(36525 * 86400) / (t_r * T_s) * 180 / mp.pi * 3600
P("EXACT GR advance per Julian century for these initial data [arcsec]:", mp.nstr(cent_exact, 12))

# 1PN with the NSSDCA elements directly (Will Eq. 64/65 with gamma=beta=1, J2=0)
a_m = mp.mpf(viz.MERCURY_A_AU) * mp.mpf(AU)
ecc = mp.mpf(viz.MERCURY_ECC)
gm = mp.mpf(GM_SUN)
adv1 = 6 * mp.pi * gm / (mp.mpf(C) ** 2 * a_m * (1 - ecc**2))
Pk = 2 * mp.pi * mp.sqrt(a_m**3 / gm)
cent1 = adv1 * 36525 * 86400 / Pk * 180 / mp.pi * 3600
P("1PN 6 pi GM/(c^2 a (1-e^2)) per Kepler period (NSSDCA a, e): per orbit", mp.nstr(adv1, 15), " period [d]",
  mp.nstr(Pk / DAY, 12), " century", mp.nstr(cent1, 10))
P("  with the sidereal period 87.969 d (fact sheet):", mp.nstr(adv1 * 36525 / mp.mpf("87.969") * 180 / mp.pi * 3600, 10))
P("a_run (AU)", mp.nstr(a_mp * gm / mp.mpf(C) ** 2 / mp.mpf(AU), 15), " ecc_run", mp.nstr(ecc_mp, 15))

# --- float references used by the checks ------------------------------------------------------------------
el = orbits.elements(k_fl["e"], abs(k_fl["l"]))
adv_fl = orbits.periapsis_advance(k_fl["e"], abs(k_fl["l"]))
P("\nfloat references (orbits.elements / periapsis_advance with float e):")
P("  r_peri rel err", float((el["r_peri"] - rp) / rp), "  r_apo rel err", float((el["r_apo"] - ra) / ra))
P("  ecc rel err", float((el["ecc"] - ecc_mp) / ecc_mp), "  p rel err", float((el["p"] - p_mp) / p_mp))
P("  advance rel err", float((adv_fl - adv_chi) / adv_chi))
tol_v04 = max(1e-9, 4.0 * 2.2e-16 / (abs(k_fl["em1"]) * max(el["ecc"], 1e-6)))
P("  v04 r_peri/r_apo tolerance", tol_v04)

# the same turning points from e^2 - 1 without cancellation (what passing em1 instead of e would give)
ll = abs(k_fl["l"])
z = np.roots([2.0, -1.0, 2.0 / ll**2, k_fl["em1"] / ll**2])
zr = np.sort(z.real[np.abs(z.imag) < 1e-12 * np.maximum(1, abs(z.real))])
P("  turning points from em1 via np.roots: r_peri rel err", float((1 / zr[1] - rp) / rp), " r_apo rel err",
  float((1 / zr[0] - ra) / ra))
# a well-conditioned alternative: the two small roots from u1 + u2 = 1/2 - u3, u1 u2 = -em1/(2 l^2 u3) ... in floats:
u3f = 0.5 - 2.0 / ll**2  # leading estimate, refined by Newton on the cubic
for _ in range(5):
    F = ((2 * u3f - 1) * u3f + 2 / ll**2) * u3f + k_fl["em1"] / ll**2
    dF = (6 * u3f - 2) * u3f + 2 / ll**2
    u3f -= F / dF
s = 0.5 - u3f
q = -k_fl["em1"] / (2 * ll**2 * u3f)
disc = math.sqrt(s * s - 4 * q)
u2f = 0.5 * (s + disc)
u1f = q / u2f
P("  Vieta route from em1 (float): r_peri rel err", float((1 / u2f - rp) / rp), " r_apo rel err", float((1 / u1f - ra) / ra))

# --- the run -------------------------------------------------------------------------------------------------
P("\nthe run (Harness, preset mercury):")
t0 = time.time()
h = Harness("v04_orbits", "mercury")
scale = h.sim._period_estimate(h.sim.track) * h.sim.T_s
h.run_to(10.3 * scale)
P("  wall", round(time.time() - t0, 2), "s")
peri = [m for m in h.of("apsis") if m["kind"] == "peri"]
advs = [m["adv"] for m in peri if m["adv"] is not None]
P("  periapses", len(peri))
for a in advs:
    P("   adv", repr(a), " rel vs exact", float((a - adv_chi) / adv_chi))
for cid, c in sorted(h.checks().items()):
    P(f"  check {cid:14s} value {c['value']!r:>24} ref {c['ref']!r:>24} rel {c['rel']!r:>24} tol {c['tol']!r}"
      + (f" ok {c['ok']}" if 'ok' in c else ""))
cent = [c for c in h.checks().values() if c["id"].endswith(".century")][-1]["value"]
P("  run century", cent, " vs exact for these data", mp.nstr(cent_exact, 12), " rel", float((cent - cent_exact) / cent_exact))
P("  run century vs 42.98: rel", (cent - 42.98) / 42.98)
