# Review LB1-p02-ux, Part A, script a1: a free Gaussian across live grid changes against its closed form.
# Run (from engine/): docker run --rm --name lf-lbrx-a1 --memory=8g -v $PWD:/lf:ro -v <this folder>:/out
#   -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/lfphys -w /lf/lfphys light-funnel-viz
#   python3 /out/a1_regrid_free_gaussian.py
# Cases beyond the repository's tests: odd point counts (the cell's half-step offset), a packet near the band edge,
# a chain of changes (refine, enlarge, coarsen, shrink) with evolution in between, open edges on, 3-D.
import math
import numpy as np
from scipy import constants as sc
from lfphys.core.quantum import scene as Q
from lfphys.core.quantum import schrodinger_nd as S

UNIT = Q.species("atom", Q.Units(), mass_u=sc.m_e / sc.atomic_mass)  # mass 1


def ref(grid, t, c, k, sig):
    return S.Grid(grid.shape, grid.d, m=1.0, center=grid.center).free_gaussian(t, c, k, sig)


def rel(a, b):
    return float(np.max(np.abs(a - b)) / np.max(np.abs(b)))


def chain(name, shape0, d0, c, k, sig, steps, dt, edges=None, ndim=2):
    s = Q.Scene(shape0, d0, dt=dt, edges=edges, device="cpu")
    pid = s.add_particle(Q.Packet(UNIT, list(c), list(k), list(sig)))
    print(f"\n== {name}: start {list(shape0)} x {d0}, window {[n * d0 for n in shape0]}, edges={'open' if edges else 'closed'}")
    for (shape, d, nsteps) in steps:
        s.advance(nsteps)
        t = s.t
        e0 = rel(s.wave(pid), ref(s.grid, t, c, k, sig))
        try:
            rep = s.regrid(shape, d)
        except ValueError as e:
            print(f"  t={t:6.3f} {list(s.grid.shape)}x{s.grid.d[0]:.4g} -> {list(shape)}x{d:.4g}: REFUSED: {e}")
            continue
        r = rep["particles"][pid]
        e1 = rel(s.wave(pid), ref(s.grid, t, c, k, sig))
        lo, hi = S.window(s.grid, 0)
        print(f"  t={t:6.3f} -> {list(shape)} x {d:.5g} (cell x [{lo:.5g}, {hi:.5g})): err before {e0:.2e} after {e1:.2e}; "
              f"norm {r['norm_before']:.15f} -> {r['norm_after']:.15f} (dropped {r['dropped']:.2e}); spectrum {r['spectrum']:.1e} "
              f"outside {r['outside']:.1e} face {r['face']:.1e}; E {r['E_before']:.12f} -> {r['E_after']:.12f}")
    s.advance(8)
    print(f"  final t={s.t:.3f}: err vs closed form {rel(s.wave(pid), ref(s.grid, s.t, c, k, sig)):.2e}; balance "
          f"{s.checks()[pid]['balance']:.2e} (tol {s.checks()[pid]['balance_tol']:.1e}); absorbed {s.absorbed(pid)}")
    return s, pid


# 1. odd point counts: the cell moves by (d - d2)/2 on a same-window change (the sample n//2 stays at the centre)
chain("odd counts, same window and both changed", (191, 191), 0.5, (-4.0, 2.0), (1.5, -0.5), (3.0, 3.0),
      [((287, 287), 0.5 * 191 / 287, 4), ((190, 190), 0.5 * 191 / 190, 4), ((257, 257), 0.4, 4), ((191, 191), 0.5, 4)],
      0.25)
# 2. a packet near the band: |k| + 6 sigma_k = 5.0 against pi/d = 6.28 (d = 0.5); refine, then coarsen back
chain("near the band edge", (192, 192), 0.5, (-4.0, 2.0), (4.5, 0.0), (3.0, 3.0),
      [((384, 384), 0.25, 2), ((192, 192), 0.5, 2), ((160, 160), 0.6, 2)], 0.05)
# 3. a chain with evolution in between and open edges on (the packet stays far from the layers)
chain("chain with open edges", (192, 192), 0.5, (-4.0, 2.0), (1.5, -0.5), (3.0, 3.0),
      [((288, 288), 1 / 3, 4), ((320, 320), 1 / 3, 4), ((200, 200), 0.6, 4), ((176, 176), 0.6, 4)], 0.25,
      edges=Q.EdgeLayers(8.0, 2.0))
# 4. 3-D: 64^3 -> 80^3 (same window) -> 96^3 (same step) -> 72^3 x 0.5 (both changed) -> 64^3
chain("3-D", (64, 64, 64), 0.5, (-2.0, 1.0, 0.5), (1.0, 0.0, -0.5), (1.5, 1.5, 1.5),
      [((80, 80, 80), 0.4, 2), ((96, 96, 96), 0.4, 2), ((72, 72, 72), 0.5, 2), ((64, 64, 64), 0.5, 2)], 0.25)
