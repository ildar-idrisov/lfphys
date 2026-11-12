"""v06 (QCD) probes.
A. worlds over the allowed range of alpha_s(M_Z) in [0.05, 0.3]: construction errors.
B. the 'kap' comparison (ok=None, ref set, tol default 1e-9): how the player renders it (player.js: ok undefined and
   rel/ref present -> |rel| <= tol, else a red cross).
C. independent running written here (scipy solve_ivp, the 4-loop MS-bar beta function in the convention of
   van Ritbergen-Vermaseren-Larin) with (i) continuous matching (as the engine), (ii) + the 2-loop decoupling constant
   c2 = 11/72, (iii) + the 3-loop constant c3 (Chetyrkin-Kniehl-Steinhauser 1997 for the MS-bar mass at mu = m(m),
   c3 = 564731/124416 - 82043/27648 zeta3 - 2633/31104 n_l, as used by RunDec; quoted from memory, NOT verified
   against the paper in this review); alpha_s at m_tau, 2 GeV, m_c, m_b, 1 TeV.
D. live change of the sweep speed: the probe jumps back to the parameter mu (mu_now restarts from params["mu"]).
E. quarkonium levels: the fixed box R = 25 GeV^-1, N = 700 (cornell.spectrum defaults) against R = 60, N = 1700 over
   the live ranges m_q in (0, 10], kappa in [0, 1.5], a in [1, 5].
F. largest alpha_s on the drawn curves (the view clips at 0.5: view.js Y(a) = min(a, amax)).
Output: out/08_v06_qcd.txt
"""
import math
import sys

import numpy as np
from scipy import integrate, special

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402
from lfphys.core import data  # noqa: E402
from lfphys.core.qcd import running  # noqa: E402
from lfphys.theories.models import cornell  # noqa: E402
import v06_qcd.viz as V6  # noqa: E402

OUT = open("out/08_v06_qcd.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


say("A. world construction over alpha_s(M_Z) in the allowed range [0.05, 0.3]")
for a0 in (0.05, 0.10, 0.15, 0.18, 0.20, 0.205, 0.21, 0.22, 0.25, 0.3):
    try:
        h = Harness("v06_qcd", None, {"alpha_mz": a0})
        fails = [c["id"] for c in h.checks().values() if c.get("ok") is False]
        say(f"  alpha_mz = {a0}: built; errors {h.errors()}; ok=False checks {fails}")
    except Exception as e:  # noqa: BLE001
        say(f"  alpha_mz = {a0}: CONSTRUCTION FAILED {type(e).__name__}: {e}")

say("\nB. the 'kap' comparison as the player renders it")
for preset, extra in (("standard", {}), ("bottom", {}), ("standard", {"m_q": 4.0}), ("bottom", {"kappa": 0.3})):
    h = Harness("v06_qcd", preset, extra)
    k = [c for c in h.checks().values() if c["id"].startswith("kap")]
    for c in k:
        shown_ok = abs(c["rel"]) <= max(c.get("tol") or 1e-9, 1e-12) if c.get("ok") is None else c["ok"]
        say(f"  {preset} {extra}: {c['id']} value {c['value']:.4g} ref {c['ref']:.4g} rel {c['rel']:+.3f} tol {c['tol']}"
            f" ok-field {c.get('ok')!r} -> player shows {'✓' if shown_ok else '✗ (failed)'}")
    if not k:
        say(f"  {preset} {extra}: no kap check (mu_bs < 1 GeV), mu_bs = {h.sim.state['mu_bs']:.3g} GeV")

say("\nC. matching order at the quark thresholds (independent code)")
Z3 = float(special.zeta(3.0))


def betas(nf):
    return [11 - 2 / 3 * nf, 102 - 38 / 3 * nf, 2857 / 2 - 5033 / 18 * nf + 325 / 54 * nf**2,
            (149753 / 6 + 3564 * Z3) - (1078361 / 162 + 6508 / 27 * Z3) * nf + (50065 / 162 + 6472 / 81 * Z3) * nf**2
            + 1093 / 729 * nf**3]


def run_fixed(a, mu0, mu1, nf):
    b = betas(nf)
    f = lambda L, y: [-sum(bi * y[0] ** (i + 2) for i, bi in enumerate(b))]  # noqa: E731
    s = integrate.solve_ivp(f, (2 * math.log(mu0), 2 * math.log(mu1)), [a / (4 * math.pi)], method="DOP853",
                            rtol=1e-13, atol=1e-18)
    return 4 * math.pi * s.y[0, -1]


def down(alpha, nl, order):
    """alpha^(nl) from alpha^(nl+1) at mu = m_h(m_h)."""
    x = alpha / math.pi
    c2 = 11 / 72
    c3 = 564731 / 124416 - 82043 / 27648 * Z3 - 2633 / 31104 * nl
    f = 1.0 + (c2 * x * x if order >= 2 else 0) + (c3 * x**3 if order >= 3 else 0)
    return alpha * f


def alpha_at(mu, order):
    a, m = data.ALPHA_S_MZ[0], data.M_Z[0]
    mc, mb = data.M_C_MC[0], data.M_B_MB[0]
    if mu >= mb:
        return run_fixed(a, m, mu, 5)
    a = down(run_fixed(a, m, mb, 5), 4, order)
    if mu >= mc:
        return run_fixed(a, mb, mu, 4)
    a = down(run_fixed(a, mb, mc, 4), 3, order)
    return run_fixed(a, mc, mu, 3)


M_TAU = 1.77693  # GeV, PDG 2024 tau mass (1776.93 +- 0.09 MeV), used only as a scale here
TH = {"c": data.M_C_MC[0], "b": data.M_B_MB[0], "t": data.M_T_MSBAR}
say("  scale | engine (4 loops, continuous) | own, continuous | own + c2 (NNLO) | own + c2 + c3 (N3LO, RunDec-like) | "
    "engine - N3LO")
for mu in (M_TAU, 2.0, data.M_C_MC[0] * 0.999, 3.0, data.M_B_MB[0], 10.0):
    e = running.alpha_s(mu, data.ALPHA_S_MZ[0], data.M_Z[0], TH, 4)
    o1, o2, o3 = alpha_at(mu, 1), alpha_at(mu, 2), alpha_at(mu, 3)
    say(f"  {mu:.5g} GeV | {e:.6f} | {o1:.6f} | {o2:.6f} | {o3:.6f} | {e - o3:+.2e}")
dlo = running.alpha_s(M_TAU, data.ALPHA_S_MZ[0] - data.ALPHA_S_MZ[1], data.M_Z[0], TH, 4)
dhi = running.alpha_s(M_TAU, data.ALPHA_S_MZ[0] + data.ALPHA_S_MZ[1], data.M_Z[0], TH, 4)
say(f"  for scale: the PDG uncertainty +-0.0009 of alpha_s(M_Z) maps to alpha_s(m_tau) in [{dlo:.4f}, {dhi:.4f}]")
a3 = running.alpha_s(M_TAU, data.ALPHA_S_MZ[0], data.M_Z[0], TH, 3)
a4 = running.alpha_s(M_TAU, data.ALPHA_S_MZ[0], data.M_Z[0], TH, 4)
say(f"  engine 3 vs 4 loops at m_tau: {a3:.6f} vs {a4:.6f} (difference {a4 - a3:+.1e})")
say("  the run's threshold check: alpha(m(1+1e-9)) = alpha(m(1-1e-9)) holds by construction of continuous matching")

say("\nD. live change of the sweep speed while the probe is moving")
h = Harness("v06_qcd", "standard")
h.run_to(3.0)
mu_before = h.sim.mu_now()
h.set(sweep=0.6)
mu_after = h.sim.mu_now()
say(f"  t = 3 s, sweep 0.5 dec/s from mu = 10 GeV: probe at {mu_before:.4g} GeV; after set(sweep=0.6) at the same t: "
    f"{mu_after:.4g} GeV")

say("\nE. quarkonium levels: box R = 25 GeV^-1, N = 700 (as the run) vs R = 60, N = 1700")
for mq, kap, a in ((1.84, 0.52, 2.34), (5.18, 0.52, 2.34), (1.0, 0.52, 2.34), (0.5, 0.52, 2.34), (0.3, 0.52, 5.0),
                   (1.84, 0.0, 5.0), (0.2, 0.0, 5.0), (10.0, 1.5, 1.0)):
    s1 = cornell.spectrum(mq, kap, a, L_max=2, n_max=3)
    s2 = cornell.spectrum(mq, kap, a, L_max=2, n_max=3, R=60.0, N=1700)
    worst = max(abs((s1[k] - s1[(1, 0)]) - (s2[k] - s2[(1, 0)])) * 1e3 for k in s1 if k != (1, 0))
    say(f"  m_q = {mq}, kappa = {kap}, a = {a}: worst splitting error of the run's box = {worst:.3g} MeV "
        f"(3D level: run {1e3 * (s1[(3, 2)] - s1[(1, 0)]):.1f} MeV, big box {1e3 * (s2[(3, 2)] - s2[(1, 0)]):.1f} MeV)")

say("\nF. largest alpha_s on the drawn curves (view clips at 0.5)")
for preset in ("standard", "one_loop", "strong"):
    h = Harness("v06_qcd", preset)
    seg = h.of("segment")[-1]
    mx = {L: float(np.nanmax(h.sim.state["curves"][L])) for L in ("L1", "L2", "L3", "L4")}
    say(f"  {preset}: max alpha on the curves {mx}")
