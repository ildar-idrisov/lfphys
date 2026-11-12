"""P7 review, check 4b: the size of the physics effect of the 3.5PN coefficient errors that the tests did not catch
(s04), and a re-run of the polarisation-handedness control (the s04 mutation P -> -P was a no-op: P and Q = N x P
both flip, and h+, hx are invariant under a rotation of the basis by pi).

Mutated copies of pn_binary are loaded as separate modules from the read-only source (no file is written).
Effects measured: (i) the orbit-averaged loss of E_2PN (2.5 + 3.5PN reaction on the 2PN orbit) relative to the
correct one, and relative to its 3.5PN part, for the states (eps, j) = (1e-3, 0.5), (5e-3, 0.5), (1e-2, 0.9)
((1e-2, 0.5) is avoided: state_from_invariants diverges there, s10); (ii) the
time of a quasi-circular inspiral from r = 20 to r = 10 (nu = 0.25).

Run: python3 s04b_uncaught_effects.py
"""
import argparse
import importlib.util
import math
import sys
import types

import numpy as np

SRC = "/lf/lfphys/lfphys/core/gravity/pn_binary.py"
MUT = {
    "A3.5: 112 -> 113 (rdot^5 term)": ("+ 112.0 * rd2 * rd2)", "+ 113.0 * rd2 * rd2)"),
    "A3.5: 3956/35 -> 3946/35": ("(3956.0 / 35.0 + 184.0 / 5.0 * nu)", "(3946.0 / 35.0 + 184.0 / 5.0 * nu)"),
    "A3.5: 184/5 nu -> 180/5 nu": ("(3956.0 / 35.0 + 184.0 / 5.0 * nu)", "(3956.0 / 35.0 + 180.0 / 5.0 * nu)"),
    "B3.5: 12/5 nu -> 13/5 nu (v^2 rdot^2)": ("(678.0 / 5.0 + 12.0 / 5.0 * nu)", "(678.0 / 5.0 + 13.0 / 5.0 * nu)"),
    "B3.5: -120 -> -119 (caught, for scale)": ("- 120.0 * rd2 * rd2)", "- 119.0 * rd2 * rd2)"),
}


def load(name, old=None, new=None):
    src = open(SRC).read().replace("from ..constants import C", "from lfphys.core.constants import C")
    if old is not None:
        assert src.count(old) == 1
        src = src.replace(old, new)
    mod = types.ModuleType(name)
    exec(compile(src, f"<{name}>", "exec"), mod.__dict__)
    return mod


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    P0 = load("pn_ok")
    nu = 0.25
    base = {}
    for eps, j in ((1e-3, 0.5), (5e-3, 0.5), (1e-2, 0.9)):
        st = P0.state_from_invariants(eps, j, nu)
        r = P0.averaged_dissipation(st, nu, conservative=(1, 2), dissipative=(2.5, 3.5), order=2)
        r25 = P0.averaged_dissipation(st, nu, conservative=(1, 2), dissipative=(2.5,), order=2)
        base[eps, j] = (st, r["dE"], r["dE"] - r25["dE"])
    stc = P0.circular_state(20.0, nu)
    t_ok = P0.integrate(stc, 1e9, nu, r_stop=10.0, n_out=3)["end"]["t"]
    for name, (old, new) in MUT.items():
        Pm = load("pn_mut", old, new)
        parts = []
        for (eps, j), (st, dE, d35) in base.items():
            rm = Pm.averaged_dissipation(st, nu, conservative=(1, 2), dissipative=(2.5, 3.5), order=2)
            parts.append(f"{eps},{j}: dE {rm['dE'] / dE - 1:+.1e} (of the 3.5PN part {(rm['dE'] - dE) / d35:+.1e})")
        t_m = Pm.integrate(stc, 1e9, nu, r_stop=10.0, n_out=3)["end"]["t"]
        print(f"{name}: " + "; ".join(parts) + f"; inspiral 20->10: time {t_m / t_ok - 1:+.1e}")

    # polarisation handedness: a left-handed triad (Q = P x N) flips hx
    from lfphys.core.gravity import gw_quadrupole as W
    N, Pv, Qv = W.observer_triad(0.7, 0.3)
    r, w = 30.0, 30.0**-1.5
    x = r * np.array([math.cos(0.4), math.sin(0.4), 0])
    v = r * w * np.array([-math.sin(0.4), math.cos(0.4), 0])
    a, jk = W.newtonian_kinematics(x, v)
    _, Q2, _ = W.quadrupole(x, v, a, jk, 0.25)
    hp, hx = W.polarizations(Q2, Pv, Qv)
    hp2, hx2 = W.polarizations(Q2, Pv, np.cross(Pv, N))
    print(f"left-handed triad: h+ {hp:.6e} -> {hp2:.6e}, hx {hx:.6e} -> {hx2:.6e}")


if __name__ == "__main__":
    main()
