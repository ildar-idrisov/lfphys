# Reviewer's check: the dye (D2Q5) across Flow2D.remap against the exact diffusion of a Gaussian, with variants of the
# dye's antisymmetric factor kgm (patched in a copy of lbm.py's source in memory; the engine's files are not touched).
# Run in Docker from engine/ (REVIEW.md).
import inspect
import importlib.util
import math
import sys

import numpy as np

sys.path[:0] = ["/lf/lfphys"]
from lfphys.core import backend  # noqa: E402
from lfphys.core.fluids import lbm  # noqa: E402

KGM = "            kgm = (self.tau_gm * u1.dx) / (tgm0 * u0.dx) if REMAP_NEQ_RESCALE else 1.0\n"


def variant(name, expr):
    src = inspect.getsource(lbm)
    assert src.count(KGM) == 1
    src = src.replace(KGM, f"            kgm = {expr}\n")
    spec = importlib.util.spec_from_loader(f"lfphys.core.fluids._rev_dye_{name}", loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "lfphys.core.fluids"
    exec(compile(src, f"lbm_dye_{name}", "exec"), mod.__dict__)
    return mod


L, NU, D, S0 = 32.0, 0.1, 0.02, 2.5
PER = {s: "periodic" for s in lbm.SIDES}


def exact(fl, t, ux=0.0):
    s2 = S0 * S0 + 2 * D * t
    out = np.zeros_like(fl._X)
    for ix in (-1, 0, 1):          # periodic images
        for iy in (-1, 0, 1):
            X = fl._X - 0.5 * L - ux * t + ix * L
            Y = fl._Y - 0.5 * L + iy * L
            out += (S0 * S0 / s2) * np.exp(-(X * X + Y * Y) / (2 * s2))
    return out


def flow(Lm, dx, dt, ux=0.0):
    fl = Lm.Flow2D((L, L), dx, nu=NU, rho=1.0, dt=dt, sides=PER, device="cpu", dye=D)
    if ux:
        fl.set_flow(velocity=lambda X, Y: (ux + 0 * X, 0 * Y))
    C = exact(fl, 0.0)
    w = np.array(Lm.WG)[:, None, None]
    ex = np.array([0, 1, 0, -1, 0])[:, None, None]
    fl._g = np.ascontiguousarray(w * C[None] * (1 + 3 * ex * ux))
    return fl


def err(fl, ux=0.0):
    C = fl.dye()
    return float(np.max(np.abs(C - exact(fl, fl.t, ux))))


if __name__ == "__main__":
    backend.configure(None)
    variants = {"engine": lbm, "kgm = kgp": variant("kgp", "kgp"), "kgm = 1": variant("one", "1.0")}
    print("== dye: a Gaussian (sigma 2.5, D 0.02 lattice units of the coarse grid) diffusing, remapped at t = 101, "
          "error against the exact Gaussian (peak 1) ==")
    for ux in (0.0, 0.05):
        for (dx, dt, lab) in ((0.5, 0.25, "refine diffusive"), (2.0, 4.0, "coarsen diffusive"), (1.0, 0.5, "new dt")):
            ref = flow(lbm, dx, dt, ux)
            nT = int(round(101 / dt)) + int(round(200 / dt))
            ref.advance(nT)
            line = [f"target grid alone {err(ref, ux):.3e}"]
            co = flow(lbm, 1.0, 1.0, ux)
            co.advance(301)
            line.append(f"coarse alone {err(co, ux):.3e}")
            for name, Lm in variants.items():
                fl = flow(Lm, 1.0, 1.0, ux)
                fl.advance(100)
                fl.remap(dx=dx, dt=dt)
                e1 = err(fl, ux)
                worst = e1
                for _ in range(int(round(200 / dt))):
                    fl.advance(1)
                    worst = max(worst, err(fl, ux))
                line.append(f"[{name}] after remap {e1:.3e}, worst {worst:.3e}, end {err(fl, ux):.3e}")
            print(f"  u_x {ux} {lab:18s}: " + "; ".join(line))
            sys.stdout.flush()
