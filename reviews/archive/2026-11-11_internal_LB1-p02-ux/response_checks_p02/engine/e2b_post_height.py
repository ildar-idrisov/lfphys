import math, numpy as np
from lfphys.core.quantum import scene as Q
from lfphys.core.quantum import schrodinger_nd as S
el = Q.species('electron')
def tryit(tag, s, pid, shift):
    try:
        r = s.move_particle(pid, shift)
        print(f"  {tag}: TAKEN gauge eps {r['gauge']:.2e}; T {r['T_before']:.6f} -> {r['T_after']:.6f}")
        return r
    except ValueError as e:
        print(f"  {tag}: REFUSED what={getattr(e, 'what', None)} eps={getattr(e, 'value', 0):.3g} "
              f"dT={getattr(e, 'dT', float('nan')):+.3g} tubes={getattr(e, 'tubes', {})} fields={getattr(e, 'fields', [])}")
        return None


print("== B shielded tube: post radius 3, V = 60, tube radius 0.5 at its centre; packet scattered round it; move by s")
c0 = np.array([0.0, 0.0])
import sys
VPOST = float(sys.argv[1])


def world(tube_at):
    s = Q.Scene((256, 256), 0.2, dt=0.004, edges=Q.EdgeLayers(5.0, 6.0), device="cpu")
    s.add(Q.Ball([0.0, 0.0], 3.0, VPOST, 1.0))
    s.add(Q.FluxTube(list(tube_at), 2 * math.pi * 0.37, 0.5))
    pid = s.add_particle(Q.Packet(el, [-9.0, 0.6], [2.2, 0.0], [1.6, 2.6]))
    s.advance(1500)
    return s, pid


for sh in ([0.0, 0.6],):
    shv = np.array(sh)
    sB, pB = world(c0)
    w0 = sB.wave(pB).copy()
    rho = np.abs(w0) ** 2
    X = sB.grid.mesh()
    print(f" move {sh}: wave's probability within r < 2.4 of the post's centre {rho[(X[0]**2 + X[1]**2) < 2.4**2].sum() / rho.sum():.2e}")
    r = tryit(f"move {sh}", sB, pB, sh)
    sA, pA = world(c0 - shv)
    ref = S.translate(sA.wave(pA), sA.grid, shv)
    if r is not None:
        got = sB.wave(pB)
        ph = np.vdot(ref, got)
        ph /= abs(ph)
        err = np.sqrt(np.sum(np.abs(got - ph * ref) ** 2) / np.sum(np.abs(ref) ** 2))
        print(f"   second method (tube at c0 - s, evolved, translated): ||moved - e^(i phi) ref|| / ||ref|| = {err:.2e}")
    # negative control: the old factor, straight-line integrals of the whole A from <r>
    q = -1.0
    c = np.array(sB.observables(pB)["r"]) if r is None else np.array(r["r_before"])
    g = sB.grid
    A = sB._arr["A"]
    old = S.translate(w0, g, shv) * np.exp(1j * q * (A.gauge(g, c + shv) - A.gauge(S.Grid(g.shape, g.d, center=np.array(g.center) - shv), c)))
    ph = np.vdot(ref, old)
    ph /= abs(ph)
    print(f"   negative control (old factor from <r>): ||old - e^(i phi) ref|| / ||ref|| = "
          f"{np.sqrt(np.sum(np.abs(old - ph * ref) ** 2) / np.sum(np.abs(ref) ** 2)):.2e}")
