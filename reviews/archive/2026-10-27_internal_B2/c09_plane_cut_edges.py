# B2 review, check 9: lfphys.core.geometry.plane_cut on planes through corners of the box (a box face; a diagonal
# plane). Every corner that lies on the plane must be a vertex of the cut polygon exactly once.
# Run: docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys light-funnel-viz python3 reviews/2026-10-27_internal_B2/c09_plane_cut_edges.py
import numpy as np

from lfphys.core import geometry as G

box = ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0))
for name, o, n in (("face x = 1", (1.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
                   ("face x = -1", (-1.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
                   ("diagonal x + y = 0", (0.0, 0.0, 0.0), (1.0, 1.0, 0.0)),
                   ("diagonal x - y = 0", (0.0, 0.0, 0.0), (1.0, -1.0, 0.0))):
    n = np.asarray(n) / np.linalg.norm(n)
    pl, poly, s, t = G.plane_cut(o, n, box)
    P = np.asarray(pl.origin) + poly[:, :1] * np.asarray(pl.u) + poly[:, 1:] * np.asarray(pl.v)
    uniq = np.unique(np.round(P, 12), axis=0)
    print(f"{name:20s}: {len(poly)} polygon vertices, {len(uniq)} distinct; expected 4 distinct (a rectangle); "
          f"vertices {np.round(uniq, 3).tolist()}")
