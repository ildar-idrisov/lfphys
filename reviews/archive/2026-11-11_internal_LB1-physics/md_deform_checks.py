# Reviewer's checks of MD.deform (LB1, plan P16.1). Run in Docker from engine/ (see REVIEW.md, "Environment").
# Writes nothing outside stdout; the output is kept next to this script as md_deform_checks.out.
import argparse
import math
import sys

import numpy as np

sys.path[:0] = ["/lf/lfphys"]
from lfphys.core.md.system import MD  # noqa: E402
from lfphys.theories.models.interatomic import LJWall, LennardJones, WCA  # noqa: E402


def gas(dim, n, L, pair=None, T=1.0, seed=1, boundary="periodic", **kw):
    md = MD(dim=dim, box=L if np.ndim(L) else [L] * dim, boundary=boundary, pair=pair, dt=0.004, seed=seed, **kw)
    md.add_species("a")
    md.fill("a", n=n, T=T, arrangement="random")
    return md


def part_a():
    """(A) The ideal-gas adiabat through deform, and an INDEPENDENT second method: a slow driven piston."""
    print("== A. ideal gas: affine deform against the adiabat and against a slow driven piston ==")
    for dim in (2, 3):
        md = gas(dim, 400, 30.0)
        T0, V0 = md.temperature()["T"], md.volume()
        for k in range(10):
            md.deform([30.0 * (1 - 0.03 * (k + 1))] * dim)
        T1, V1 = md.temperature()["T"], md.volume()
        print(f"  d={dim}: T V^(2/d) before {T0 * V0 ** (2 / dim):.15g} after {T1 * V1 ** (2 / dim):.15g} "
              f"rel {T1 * V1 ** (2 / dim) / (T0 * V0 ** (2 / dim)) - 1:.2e}")
    # the piston: a collisionless 2-D gas, x periodic, y walled; the driven piston (mass inf) moves the hi face of y
    # from 30 to 21 at speed w; per particle |v_y| L_y is an adiabatic invariant to O(w / v)
    for w in (0.05, 0.01, 0.002):
        md = gas(2, 400, [30.0, 30.0], boundary=["periodic", "walls"], seed=2)
        Ky0 = 0.5 * float(np.sum(md.velocities()[:, 1] ** 2))
        aff = MD.from_state_dict(md.state_dict())
        aff.deform([30.0, 21.0])
        md.set_piston("y", X=30.0, V=-w)
        while md.piston()["X"] > 21.0 + 1e-12:
            dt_left = (md.piston()["X"] - 21.0) / w
            if dt_left < md.dt:
                md.set_dt(dt_left)
            md.step(1)
        md.set_piston("y", V=0.0)
        Ky_p = 0.5 * float(np.sum(md.velocities()[:, 1] ** 2))
        Ky_a = 0.5 * float(np.sum(aff.velocities()[:, 1] ** 2))
        vth = 1.0
        print(f"  piston w={w:g} (w/v_th={w / vth:g}): Ky L^2 piston/initial = {Ky_p * md.piston()['X'] ** 2 / (Ky0 * 900):.5f}, "
              f"affine/initial = {Ky_a * 21.0 ** 2 / (Ky0 * 900):.15f}; piston work {md.counters()['piston']['work']:.6g} "
              f"vs affine W_box {aff.energy_balance()['W_box']:.6g}")


def cycle(N, relax, total=None, seed=3, dim=2):
    md = MD(dim=dim, box=[16.0, 16.0], pair=LennardJones(2.5), dt=0.004, seed=seed)
    md.add_species("a")
    md.fill("a", n=100, T=1.5, arrangement="random")
    md.step(500)
    md.reset_counters()
    E0 = md.energy()
    W = PDV = 0.0
    for k in range(N):
        o = md.deform([16.0 * (1 - 0.15 * (k + 1) / N), 16.0])
        W += o["dE"]
        PDV += o["pdv"]
        md.step(relax)
    Wc = W
    for k in range(N):
        o = md.deform([16.0 * (1 - 0.15 * (N - k - 1) / N), 16.0])
        W += o["dE"]
        PDV += o["pdv"]
        md.step(relax)
    b = md.energy_balance()
    return Wc, W, PDV, b["residual"], md.energy() - E0


def part_b():
    """(B) LJ fluid: the work booked against the trapezoid of the virial, and the cycle compress -> expand (a
    quasi-static adiabatic process is reversible: the net work of the cycle tends to 0)."""
    print("== B. LJ fluid (2-D, 100 atoms, rho 0.39, T 1.5): W vs trapezoid, and a compress/expand cycle ==")
    print("  N  relax  W_compress   W_cycle(net)   sum(W-PDV)     integrator residual")
    for N, relax in ((1, 400), (4, 100), (16, 25), (64, 6), (16, 2), (64, 2), (256, 2), (64, 50)):
        Wc, W, PDV, res, dE = cycle(N, relax)
        print(f"  {N:4d} {relax:4d}  {Wc:11.5f}  {W:12.5f}  {W - PDV:12.3e}  {res:12.3e}")
    # several seeds for the slow case, to separate the dissipation from noise
    for N, relax in ((16, 25), (64, 25)):
        ws = [cycle(N, relax, seed=s)[1] for s in (3, 4, 5, 6)]
        print(f"  seeds 3-6, N={N}, relax={relax}: net cycle work {np.round(ws, 4).tolist()}, mean {np.mean(ws):.4f}")


def soft_walled():
    md = MD(dim=2, box=[20.0, 20.0], boundary=["periodic", "walls"], pair=LennardJones(2.5), dt=0.004, seed=6)
    md.add_species("a")
    md.set_wall("y", "lo", "soft", term=LJWall(2))
    md.set_wall("y", "hi", "soft", term=LJWall(2))
    md.fill("a", n=150, T=1.5, region=([0.0, 2.0], [20.0, 18.0]), arrangement="random")
    md.step(500)
    return md


def first_order(md, axis, delta):
    L = md.L.copy()
    L[axis] *= 1 + delta
    o = md.deform(L)
    return o["dE"], o["pdv"]


def part_c():
    """(C) dE = -P dV 'to first order with the virial pressure': where the virial misses a force (a field, soft walls,
    frozen atoms) the first-order term differs."""
    print("== C. first-order dE against -P dV (virial) for small delta ==")
    for label, make in (
            ("periodic LJ (control)", lambda: (lambda m: (m.step(200), m)[1])(gas(2, 150, 20.0, LennardJones(2.5), seed=4))),
            ("walled ideal gas, field g_y = -0.5", lambda: (lambda m: (m.set_gravity([0.0, -0.5]), m.step(2000), m)[2])(
                gas(2, 150, [20.0, 20.0], None, boundary="walls", seed=5))),
            ("walled LJ, soft 9-3 walls on y", soft_walled),
    ):
        for delta in (1e-3, 1e-4, 1e-5):
            md = make()
            dE, pdv = first_order(md, 1, delta)
            print(f"  {label:34s} delta {delta:.0e}: dE {dE: .6e}  -P dV {pdv: .6e}  (dE - pdv)/dE {(dE - pdv) / dE: .3e}")
    # frozen atoms: a mobile gas around a frozen block (walled box: the virial is defined there)
    for delta in (1e-3, 1e-4):
        md = MD(dim=2, box=[20.0, 20.0], boundary="walls", pair=LennardJones(2.5), dt=0.004, seed=7)
        md.add_species("w", mass=math.inf)
        md.add_species("a")
        md.fill("w", density=0.9, region=([8.0, 8.0], [12.0, 12.0]))
        md.fill("a", n=60, T=1.5, region=([0.5, 0.5], [19.5, 7.0]), arrangement="random")
        md.step(300)
        dE, pdv = first_order(md, 1, delta)
        print(f"  {'walled LJ gas + frozen block':34s} delta {delta:.0e}: dE {dE: .6e}  -P dV {pdv: .6e}  "
              f"(dE - pdv)/dE {(dE - pdv) / dE: .3e}")


def part_d():
    """(D) The phase-space volume of the step with the centre-of-mass velocity kept (conserved axes): the Jacobian of
    (x, p) -> (lambda x, u m + (p - m u)/lambda) along one axis, numerically, for 5 particles."""
    print("== D. Jacobian determinant of the affine step on a conserved axis ==")
    lam = 0.9
    m = np.array([1.0, 2.0, 1.5, 1.0, 3.0])
    n = len(m)
    J = np.zeros((2 * n, 2 * n))
    J[:n, :n] = lam * np.eye(n)
    M = m.sum()
    # p'_i = p_i / lam + m_i/M (1 - 1/lam) sum_j p_j
    J[n:, n:] = np.eye(n) / lam + np.outer(m / M, np.ones(n)) * (1 - 1 / lam)
    print(f"  lambda {lam}: det J = {np.linalg.det(J):.12f} (canonical point transformation: 1; with P kept: lambda)")


def part_e():
    """(E) Soft <-> hard in a walled box: the MD walls act on centres (x in [0, L]), the hard-sphere walls on surfaces
    (x in [sigma/2, L - sigma/2]). How often an equilibrated walled gas can be switched at all, and the accessible
    volume's change."""
    from lfphys.core.md import hard as HD
    print("== E. soft -> hard in walled boxes ==")
    for n, L in ((20, 20.0), (60, 30.0), (200, 30.0)):
        md = MD(dim=2, box=[L, L], boundary="walls", pair=WCA(), dt=0.004, seed=8)
        md.add_species("a")
        md.fill("a", n=n, T=1.0, region=([1.0, 1.0], [L - 1.0, L - 1.0]), arrangement="random")
        ok = tot = 0
        wall_only = 0
        for k in range(200):
            md.step(25)
            cv = HD.contact_violations(md.positions(), np.ones(md.n), md.L, md.periodic)
            tot += 1
            ok += (cv["pairs"] == 0 and cv["walls"] == 0)
            wall_only += (cv["pairs"] == 0 and cv["walls"] > 0)
        pred = (1 - 1.0 / L) ** (2 * n)
        print(f"  n={n:3d} L={L:g}: switch possible at {ok}/{tot} sampled moments; refused only by the walls at "
              f"{wall_only}/{tot}; (1 - sigma/L)^(2n) = {pred:.3g}; accessible area MD L^2 = {L * L:g}, hard (L - sigma)^2 "
              f"= {(L - 1) ** 2:g} ({(L * L / (L - 1) ** 2 - 1) * 100:.1f} % denser for the hard bodies)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("parts", nargs="*", default=list("abcde"))
    a = ap.parse_args()
    for p in a.parts:
        {"a": part_a, "b": part_b, "c": part_c, "d": part_d, "e": part_e}[p]()
        sys.stdout.flush()
