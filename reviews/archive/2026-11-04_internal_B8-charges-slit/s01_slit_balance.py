"""Review B8 (slit): the optical theorem and the transmission for one configuration, with an independent energy check.

Configuration: two unequal slits (w = 0.8, 0.5 lambda, centres -0.6, 0.7), screen 0.4 lambda thick, theta = 0.3 rad,
both polarisations, default modes. Lengths in wavelengths (k = 2 pi).

Independent route: the energy flux of the computed FIELD (``field`` with its gradient: the Rayleigh-Sommerfeld
quadratures above and below, not the angular spectrum) through closed contours:
* above: a half circle of radius r0 about the exit face's centre; no flux crosses the conductor, so the outward flux
  must equal P_t;
* below: the total field (incident + specular + scattered) on the half circle below; the half disc has no sources, so
  the inward flux through the arc equals the flux into the apertures, P_t.
Both by Gauss-Legendre in the angle; compared with ``power_balance``'s far-field P_t and the extinction.
"""
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.em import slit as S  # noqa: E402

K = 2 * math.pi
xg, wg = np.polynomial.legendre.leggauss(400)
ph = 0.5 * math.pi * xg  # angle from the normal, in (-pi/2, pi/2)
wph = 0.5 * math.pi * wg

for pol in ("TE", "TM"):
    sol = S.solve(K, [-0.6, 0.7], [0.8, 0.5], 0.4, pol, theta=0.3)
    b = sol.power_balance()
    print(f"{pol}: modes {sol.modes}, P_t = {b['P_t']:.12f}, P_b = {b['P_b']:.12f}, extinction = {b['extinction']:.12f}, "
          f"rel = {b['rel']:.1e}, P_modes rel = {b['rel_modes']:.1e}, T = {b['T']:.9f}")
    for r0 in (1.5, 4.0):
        # above: centre of the exit face, arc z = t + r0 cos(phi), x = r0 sin(phi)
        x = r0 * np.sin(ph)
        z = sol.thickness + r0 * np.cos(ph)
        u, ux, uz = sol.field(x, z)
        jx, jz = np.imag(np.conj(u) * ux) / K, np.imag(np.conj(u) * uz) / K
        Pup = float(np.sum(wph * r0 * (jx * np.sin(ph) + jz * np.cos(ph))))
        # below: arc z = -r0 cos(phi); outward normal (sin phi, -cos phi)
        zb = -r0 * np.cos(ph)
        u, ux, uz = sol.field(x, zb)
        jx, jz = np.imag(np.conj(u) * ux) / K, np.imag(np.conj(u) * uz) / K
        Pdown_in = -float(np.sum(wph * r0 * (jx * np.sin(ph) - jz * np.cos(ph))))
        print(f"   r0 = {r0}: flux out of the upper arc {Pup:.12f} (P_t rel {Pup / b['P_t'] - 1:+.1e}); "
              f"flux into the lower arc {Pdown_in:.12f} (rel {Pdown_in / b['P_t'] - 1:+.1e})")
    # TM: E_x continuity: E_x ~ du/dz on both sides of the exit plane at a slit centre; TE: u
    # (already in the engine tests) - here the specular sign: far below, on the axis, |u|^2 must average 2 (|1 + r e^..|)
print("\nSign check of the specular wave: field at z = -3 lambda far from the slits (x = 40 lambda), |u + ...| vs closed form")
for pol in ("TE", "TM"):
    sol = S.solve(K, [0.0], [0.6], 0.0, pol, theta=0.0)
    for zz in (-0.25, -0.5):
        u = sol.field(np.array([40.0]), np.array([zz]), deriv=False)[0][0]
        ref = math.cos(K * zz) * 2 if pol == "TM" else 2j * math.sin(K * zz)
        print(f"  {pol} z = {zz}: u = {u:.6f}, screen without slits gives {ref:.6f}")
