# Reviewer's checks of Flow2D.remap (LB1, plan P16.1) and of STATUS V41 (ac). Run in Docker from engine/ (REVIEW.md).
# Variants of the transfer are built by patching ONE line of a copy of lbm.py's source in memory (the antisymmetric
# factor km, or a deliberate error in the transferred velocity); the engine's files are not touched.
import argparse
import importlib.util
import inspect
import math
import sys

import numpy as np

sys.path[:0] = ["/lf/lfphys"]
from lfphys.core import backend  # noqa: E402
from lfphys.core.fluids import lbm  # noqa: E402

KM_LINE = "        km = (self.tau_m * u1.dt ** 2 / u1.dx) / (tm0 * u0.dt ** 2 / u0.dx) if REMAP_NEQ_RESCALE else 1.0\n"
U_LINE = "        ux1, uy1 = R[\"u\"][0] / u1.c, R[\"u\"][1] / u1.c\n"
PER_X = {"left": "periodic", "right": "periodic"}
PER = {s: "periodic" for s in lbm.SIDES}


def variant(name, km_expr=None, u_scale=None):
    src = inspect.getsource(lbm)
    assert src.count(KM_LINE) == 1 and src.count(U_LINE) == 1
    if km_expr is not None:
        src = src.replace(KM_LINE, f"        km = {km_expr}\n")
    if u_scale is not None:
        src = src.replace(U_LINE, f"        ux1, uy1 = {u_scale} * R[\"u\"][0] / u1.c, R[\"u\"][1] / u1.c\n")
    spec = importlib.util.spec_from_loader(f"lfphys.core.fluids._rev_{name}", loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "lfphys.core.fluids"
    exec(compile(src, f"lbm_{name}", "exec"), mod.__dict__)
    return mod


VARIANTS = {"engine (km = tau-' dt'^2/dx' / ...)": lbm,
            "km = kp (Dupuis-Chopard's one factor)": None,
            "km = 1 (odd part not rescaled)": None}


def build_variants():
    v = dict(VARIANTS)
    v["km = kp (Dupuis-Chopard's one factor)"] = variant("kmkp", "kp")
    v["km = 1 (odd part not rescaled)"] = variant("km1", "1.0")
    return v


def poiseuille(L, tau=0.8, ny=8, g=1e-5, collision="trt"):
    nu = (tau - 0.5) / 3
    fl = L.Flow2D((4.0, float(ny)), 1.0, nu=nu, rho=1.0, dt=1.0, sides=PER_X, gravity=(g, 0.0), device="cpu",
                  collision=collision)
    H = float(ny)
    fl.set_flow(velocity=lambda X, Y: (g / (2 * nu) * Y * (H - Y), 0 * X))
    fl.advance(int(36 * H ** 2 / (nu * math.pi ** 2)) + 200)
    return fl, nu, g, H


def worst(fl, nu, g, H, steps):
    def err():
        exact = g / (2 * nu) * fl.y * (H - fl.y)
        return float(np.max(np.abs(fl.velocity()[0] - exact[None, :])) / exact.max())
    w = err()
    for _ in range(steps):
        fl.advance(1)
        w = max(w, err())
    return w


def part_poiseuille(V):
    print("== P. Poiseuille across a remap: largest deviation over 200 steps from the target grid's own steady state "
          "(relative to its peak) ==")
    cases = [("refine-diffusive", 0.5, 0.25, 8), ("refine-acoustic", 0.5, 0.5, 8), ("coarsen", 2.0, 4.0, 16),
             ("new-time-step", 1.0, 0.5, 8)]
    for coll in ("trt", "bgk"):
        for tau in (0.8, 1.0):
            for cname, dx, dt, ny in cases:
                row = []
                # the reference: the same channel built on the target grid and run to its own steady state (BGK's
                # wall slip depends on tau, so the closed-form parabola is not BGK's steady state)
                ref, nu, g, H = poiseuille(lbm, tau, ny, collision=coll)
                ref.remap(dx=dx, dt=dt)
                ref.advance(int(40 * H ** 2 / (ref.units.viscosity(ref.nu) * math.pi ** 2) * 1.0) + 400)
                uref = ref.velocity()[0].copy()
                for vname, L in V.items():
                    fl, nu, g, H = poiseuille(L, tau, ny, collision=coll)
                    r = fl.remap(dx=dx, dt=dt)
                    if vname.startswith("engine"):
                        kp, km = r["factors"]["neq_plus"], r["factors"]["neq_minus"]
                    w = 0.0
                    for _ in range(200):
                        fl.advance(1)
                        w = max(w, float(np.max(np.abs(fl.velocity()[0] - uref)) / np.max(np.abs(uref))))
                    row.append(f"{w:.1e}")
                print(f"  {coll} tau={tau} {cname:17s} kp={kp:.4f} km(engine)={km:.4f}: " + "  ".join(
                    f"[{n.split(' (')[0]}] {x}" for n, x in zip(V, row)))


def tg_flow(L, dx, dt, tau=0.8, u0=0.02, collision="trt"):
    Lb = 32.0
    nu = (tau - 0.5) / 3
    k = 2 * math.pi / Lb
    fl = L.Flow2D((Lb, Lb), dx, nu=nu, rho=1.0, dt=dt, sides=PER, device="cpu", collision=collision)
    fl.set_flow(velocity=lambda X, Y: (-u0 * np.cos(k * X) * np.sin(k * Y), u0 * np.sin(k * X) * np.cos(k * Y)),
                pressure=lambda X, Y: -0.25 * u0 ** 2 * (np.cos(2 * k * X) + np.cos(2 * k * Y)))
    return fl, nu, k, u0


def tg_err(fl, nu, k, u0):
    a = u0 * math.exp(-2 * nu * k * k * fl.t)
    ux, uy = fl.velocity()
    return float(max(np.max(np.abs(ux + a * np.cos(k * fl._X) * np.sin(k * fl._Y))),
                     np.max(np.abs(uy - a * np.sin(k * fl._X) * np.cos(k * fl._Y)))) / a)


def part_tg(V):
    print("== T. Taylor-Green 32^2 for 300 steps, remapped, then 400 fine steps: error against the exact vortex ==")
    for coll in ("trt", "bgk"):
        for (dx, dt, lab) in ((0.5, 0.25, "refine diffusive"), (0.5, 0.5, "refine acoustic"), (1.0, 0.5, "new dt")):
            ref, nu, k, u0 = tg_flow(lbm, dx, dt, collision=coll)       # the target grid from the start
            ref.advance(int(round(300 / dt * 1.0)) + int(round(1.0 / dt)))
            nref = 400
            ref.advance(nref)
            line = [f"target grid alone {tg_err(ref, nu, k, u0):.3e}"]
            for vname, L in V.items():
                fl, nu, k, u0 = tg_flow(L, 1.0, 1.0, collision=coll)
                fl.advance(300)
                fl.remap(dx=dx, dt=dt)
                e1 = tg_err(fl, nu, k, u0)
                fl.advance(nref)
                line.append(f"[{vname.split(' (')[0]}] just after {e1:.3e}, end {tg_err(fl, nu, k, u0):.3e}")
            print(f"  {coll} {lab:16s}: " + "; ".join(line))


def part_balance_blind():
    print("== B. the 'remap' book: a deliberately wrong transfer (velocity x 1.01 along x) passes the balance ==")
    bad = variant("ubad", u_scale="1.01")
    for L, lab in ((lbm, "engine"), (bad, "velocity x1.01")):
        fl, nu, g, H = poiseuille(L, 0.8, 8)
        fl.remap(dx=0.5, dt=0.25)
        c = fl.checks()
        b = fl.balance()
        print(f"  {lab:15s}: momentum check ok={c['momentum']['ok']} rel.residual {c['momentum']['relative_residual']:.1e}; "
              f"booked 'remap' momentum {b['momentum']['booked'].get('remap', [0, 0])[0]:.3e} of now "
              f"{b['momentum']['now'][0]:.3e}; parabola error after 200 steps {worst(fl, nu, g, H, 200):.2e}")


def v41_run(steps_list, tau=0.8, ny=16, g=1e-5, exact_books=False):
    fl, nu, g, H = poiseuille(lbm, tau, ny, g)
    print(f"  setup: 4 x {ny}, tau {tau}, g {g}, steps already {fl.steps} (the test helper's run)")
    c = fl.checks()["momentum"]
    print(f"    after {fl.steps:6d} steps: |rel.residual| {abs(c['relative_residual']):.3e}  limit {c['limit']:.3e}  ok {c['ok']}")
    return fl


def part_v41():
    print("== V. STATUS V41 (ac): the running momentum bound on the test's 4 x 16 Poiseuille channel ==")
    fl = v41_run([])
    # its growth with more steps, and the same books recomputed exactly (math.fsum of every step's per-link record)
    fl2, nu, g, H = poiseuille(lbm, 0.8, 16)
    fl2._baseline()    # restart the books' reference here: count from this moment (same as a fresh balance)
    for k in ("acc_m", "acc_p"):
        fl2._L[k] = np.zeros(fl2._L["n"])
    fl2._banked = {}
    fl2._body_imp = [0.0, 0.0]
    L = fl2._L
    ex, ey = lbm.EX[L["dir"]].astype(float), lbm.EY[L["dir"]].astype(float)
    terms_x, terms_y = [], []
    P0x, P0y = fl2._totals()[1], fl2._totals()[2]
    M0 = fl2._totals()[0]
    marks = {1000, 2000, 4000, 8000, 16000, 32000, 64000}
    n = 0
    print("    steps   engine rel.residual   limit 2 eps n   exact-books residual   max |per-link acc_p|")
    while n < 64000:
        fl2.advance(1)
        n += 1
        lp = fl2._L["last_p"]
        terms_x.extend((ex * lp).tolist())
        terms_y.extend((ey * lp).tolist())
        if n in marks:
            c = fl2.checks()["momentum"]
            Mx, Px, Py, _ = fl2._totals()
            body = fl2._F[0] * fl2._n_fluid * n
            rx = (Px - P0x) - (math.fsum(terms_x) + body)
            ry = (Py - P0y) - math.fsum(terms_y)
            print(f"   {n:6d}   {abs(c['relative_residual']):.3e}            {c['limit']:.3e}      "
                  f"{max(abs(rx), abs(ry)) / M0:.3e}            {float(np.max(np.abs(fl2._L['acc_p']))):.3e}")
            terms_x = [math.fsum(terms_x)]
            terms_y = [math.fsum(terms_y)]


def part_open():
    print("== O. the same bound on an open channel (inlet, outlet, interpolated disk: the remap test's _channel) ==")
    fl = lbm.Flow2D(size=(0.6, 0.12), dx=0.005, nu=1e-3, rho=1.0, u_max=0.3, dye=None, device="cpu",
                    sides={"left": lbm.Inlet(velocity=0.2, profile="parabolic", ramp=0.2), "right": lbm.Outlet()})
    fl.add_obstacle(lbm.Disk((0.15, 0.06), 0.02), interpolated=True, label="disk")
    done = 0
    for target in (2000, 8000, 32000):
        fl.advance(target - done)
        done = target
        c = fl.checks()
        print(f"   {done:6d} steps: momentum |rel.res| {abs(c['momentum']['relative_residual']):.3e} limit "
              f"{c['momentum']['limit']:.3e} ok {c['momentum']['ok']}; mass |rel.res| "
              f"{abs(c['mass']['relative_residual']):.3e} ok {c['mass']['ok']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("parts", nargs="*", default=["P", "T", "B", "V", "O"])
    a = ap.parse_args()
    backend.configure(None)
    V = build_variants()
    for p in a.parts:
        {"P": lambda: part_poiseuille(V), "T": lambda: part_tg(V), "B": part_balance_blind, "V": part_v41,
         "O": part_open}[p]()
        sys.stdout.flush()
