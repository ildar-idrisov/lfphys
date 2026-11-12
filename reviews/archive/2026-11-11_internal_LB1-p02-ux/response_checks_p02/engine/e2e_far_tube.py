# second method without a post: a packet passing a tube at a distance (never near it nor near its path), moved by s;
# reference: the scene with the tube at c0 - s, evolved and translated. Isolates the numerics of the comparison.
import math, sys, numpy as np
from lfphys.core.quantum import scene as Q
from lfphys.core.quantum import schrodinger_nd as S
el = Q.species("electron")
ty, sy, steps = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
def world(tube_at):
    s = Q.Scene((256, 256), 0.2, dt=0.004, edges=Q.EdgeLayers(5.12, 6.0), device="cpu")
    s.add(Q.FluxTube(list(tube_at), 2 * math.pi * 0.37, 0.5))
    pid = s.add_particle(Q.Packet(el, [-10.0, -4.0], [2.2, 0.0], [1.6, 1.6]))
    s.advance(steps)
    return s, pid
sh = np.array([0.0, sy])
sB, pB = world([0.0, ty]); sA, pA = world([0.0, ty - sy])
r = sB.move_particle(pB, sh)
ref = S.translate(sA.wave(pA), sA.grid, sh); got = sB.wave(pB)
ph = np.vdot(ref, got); ph /= abs(ph)
print(f"tube y {ty}, move {sh}, {steps} steps: eps {r['gauge']:.2e}; ||moved - e^(i phi) ref||/||ref|| = "
      f"{np.sqrt(np.sum(np.abs(got - ph * ref) ** 2) / np.sum(np.abs(ref) ** 2)):.2e}")
