# Q1/Q2: the move of a charged wave near a flux tube / across a field's edge, after the fix.
# (A) the reviewer's cases (a3): uniform field (exact), field region left (refused), AB wave moved across the tube's path
#     (refused); (B) a wave that went round a shielded tube (a hard post around it), moved by a small s that keeps the tube's
#     relative path inside the post: taken, and equal (up to one global phase) to the SECOND METHOD: the same packet evolved
#     in a scene whose tube stands at c0 - s, then translated by s (no move code involved); the old construction
#     (straight-line integrals from <r>) on the same move as the negative control.
import math, numpy as np
from lfphys.core.quantum import scene as Q
from lfphys.core.quantum import schrodinger_nd as S

el = Q.species("electron")


def tryit(tag, s, pid, shift):
    try:
        r = s.move_particle(pid, shift)
        print(f"  {tag}: TAKEN gauge eps {r['gauge']:.2e}; T {r['T_before']:.6f} -> {r['T_after']:.6f}")
        return r
    except ValueError as e:
        print(f"  {tag}: REFUSED what={getattr(e, 'what', None)} eps={getattr(e, 'value', 0):.3g} "
              f"dT={getattr(e, 'dT', float('nan')):+.3g} tubes={getattr(e, 'tubes', {})} fields={getattr(e, 'fields', [])}")
        return None


print("== A1 uniform field everywhere, evolved a quarter period, move (3, 4)")
s = Q.Scene((192, 192), 0.25, dt=0.01, edges=Q.EdgeLayers(5.0, 4.0), device="cpu")
s.add(Q.MagneticField([0.0, 0.0, 0.5]))
pid = s.add_particle(Q.Packet(el, [0.0, -4.0], [2.0, 0.0], [1.5, 1.5]))
s.advance(314)
tryit("move (3, 4)", s, pid, [3.0, 4.0])
print("== A2 field in x in [-6, 6] (B = 0.5, edge 1.5), wave inside moved out by (12, 0); control B = 0")
for B in (0.5, 0.0):
    s = Q.Scene((256, 256), 0.25, dt=0.01, edges=Q.EdgeLayers(6.0, 4.0), device="cpu")
    s.add(Q.MagneticField([0.0, 0.0, B], lo=[-6.0, None], hi=[6.0, None], edge=1.5))
    pid = s.add_particle(Q.Packet(el, [0.0, -2.0], [1.5, 0.0], [1.5, 1.5]))
    s.advance(150)
    tryit(f"B = {B}: move (12, 0)", s, pid, [12.0, 0.0])
    tryit(f"B = {B}: move (0, 3) inside the field strip", s, pid, [0.0, 3.0])
print("== A3 AB tube (h/2e) with a soft post, the wave gone round both sides, moved (0, 6); control flux 0")
for flux in (0.5, 0.0):
    s = Q.Scene((384, 384), 0.2, dt=0.01, edges=Q.EdgeLayers(5.0, 4.0), device="cpu")
    s.add(Q.FluxTube([0.0, 0.0], 2 * math.pi * flux, 0.5))
    s.add(Q.Ball([0.0, 0.0], 1.6, 5.0, 1.0))
    pid = s.add_particle(Q.Packet(el, [-8.0, 0.0], [2.0, 0.0], [2.0, 3.0]))
    s.advance(500)
    tryit(f"flux {flux}: move (0, 6)", s, pid, [0.0, 6.0])

print("== B shielded tube: post radius 3, V = 60, tube radius 0.5 at its centre; packet scattered round it; move by s")
c0 = np.array([0.0, 0.0])


def world(tube_at):
    s = Q.Scene((256, 256), 0.2, dt=0.004, edges=Q.EdgeLayers(5.0, 6.0), device="cpu")
    s.add(Q.Ball([0.0, 0.0], 3.0, 60.0, 1.0))
    s.add(Q.FluxTube(list(tube_at), 2 * math.pi * 0.37, 0.5))
    pid = s.add_particle(Q.Packet(el, [-9.0, 0.6], [2.2, 0.0], [1.6, 2.6]))
    s.advance(1500)
    return s, pid


for sh in ([0.0, 0.6], [0.5, -0.4], [0.0, 2.5]):
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
