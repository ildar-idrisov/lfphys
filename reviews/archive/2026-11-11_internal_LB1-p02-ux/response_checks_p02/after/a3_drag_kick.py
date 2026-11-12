# Review LB1-p02-ux, Part A, script a3: a drag (move_particle) and a throw (boost_particle) checked through <r>, the
# kinetic momentum <p - qA> and the kinetic energy <(p - qA)^2>/2m, beyond the repository's tests (which move a packet
# only right after it was prepared):
#   1. free particle, evolved;
#   2. a charged wave in a uniform field filling the scene, evolved a quarter cyclotron period (the magnetic translation
#      must keep the whole kinetic distribution: <pi>, <pi^2>);
#   3. a charged wave in a field confined to a box region, moved from inside the field to outside;
#   4. a charged wave that has passed on both sides of an Aharonov-Bohm tube, moved sideways (control: flux 0);
#   5. a throw in the uniform field: k0 = m v / hbar is the kinetic momentum (Ehrenfest: d<r>/dt = <pi>/m right after).
# Run as a1 (PYTHONPATH=/lf/lfphys).
import math
import numpy as np
from lfphys.core.quantum import scene as Q
from lfphys.core.quantum import schrodinger_nd as S

el = Q.species("electron")  # mass 1, charge -1 in the scene's default units (hbar = 1)


def kin(s, pid):
    """<pi>, <pi^2>/2m (kinetic energy) by spectral derivatives with A on the grid; and <r>."""
    p = s.particles[pid]
    psi = s.wave(pid)
    comps = psi if psi.ndim == s.ndim + 1 else psi[None]
    g = s.grid
    H = s.hamiltonian(s._key(p))
    A = H.A_arrays() if p.species.charge != 0 else None
    q, m = p.species.charge, p.species.mass
    nn = float(np.sum(np.abs(comps) ** 2))
    pis, T = [], 0.0
    for a in range(s.ndim):
        F = np.fft.fft(comps, axis=a + 1)
        shp = [1] * (s.ndim + 1)
        shp[a + 1] = -1
        d = np.fft.ifft(1j * g.k[a].reshape(shp) * F, axis=a + 1)  # d psi / dx_a
        pi = -1j * d - (q * A[a] * comps if A is not None else 0.0)
        pis.append(float(np.real(np.vdot(comps, pi)) / nn))
        T += float(np.sum(np.abs(pi) ** 2) / nn) / (2 * m)
    return np.array(pis), T, np.array(s.observables(pid)["r"])


def report(tag, s, pid, fn):
    pi0, T0, r0 = kin(s, pid)
    E0 = s.observables(pid)["E"]
    try:
        rep = fn()
    except ValueError as e:
        print(f"  {tag}: REFUSED ({getattr(e, 'what', None)}): {str(e)[:220]}")
        return None
    pi1, T1, r1 = kin(s, pid)
    E1 = s.observables(pid)["E"]
    print(f"  {tag}: <r> {np.round(r0, 4)} -> {np.round(r1, 4)}; <pi> {np.round(pi0, 5)} -> {np.round(pi1, 5)}; "
          f"T = <pi^2>/2m {T0:.6f} -> {T1:.6f} (dT/T = {(T1 - T0) / T0:+.2e}); <H> {E0:.6f} -> {E1:.6f}")
    return rep


print("== 1. free particle, evolved t = 2 (mass 1): move by (5, -3), then throw dk = (-1, 0.5)")
s = Q.Scene((192, 192), 0.25, dt=0.02, edges=Q.EdgeLayers(5.0, 4.0), device="cpu")
pid = s.add_particle(Q.Packet(el, [-5.0, 0.0], [1.5, 0.5], [2.0, 2.0]))
s.advance(100)
report("move", s, pid, lambda: s.move_particle(pid, [5.0, -3.0]))
report("throw", s, pid, lambda: s.boost_particle(pid, [-1.0, 0.5]))

print("\n== 2. uniform field everywhere (B = 0.5, cyclotron period 2 pi m/(|q| B) = 12.57), evolved a quarter period")
s = Q.Scene((192, 192), 0.25, dt=0.01, edges=Q.EdgeLayers(5.0, 4.0), device="cpu")
s.add(Q.MagneticField([0.0, 0.0, 0.5]))
pid = s.add_particle(Q.Packet(el, [0.0, -4.0], [2.0, 0.0], [1.5, 1.5]))
s.advance(int(round(12.566 / 4 / 0.01)))
report("move by (3, 4)", s, pid, lambda: s.move_particle(pid, [3.0, 4.0]))
report("move back by (-3, -4)", s, pid, lambda: s.move_particle(pid, [-3.0, -4.0]))

print("\n== 3. field confined to a box x in [-6, 6], y unbounded (B = 0.5 inside, edge 1.5); a wave evolved inside, "
      "moved out across the field's edge")
for B in (0.5, 0.0):
    s = Q.Scene((256, 256), 0.25, dt=0.01, edges=Q.EdgeLayers(6.0, 4.0), device="cpu")
    s.add(Q.MagneticField([0.0, 0.0, B], lo=[-6.0, None], hi=[6.0, None], edge=1.5))
    pid = s.add_particle(Q.Packet(el, [0.0, -2.0], [1.5, 0.0], [1.5, 1.5]))
    s.advance(150)
    print(f" B = {B}:")
    report("move by (12, 0) (out of the field)", s, pid, lambda: s.move_particle(pid, [12.0, 0.0]))

print("\n== 4. an AB tube (flux h/2e, radius 0.5) at the origin; a wave that has gone round it (packet started on the "
      "tube's line, passed it), moved sideways by (0, 6)")
for flux in (0.5, 0.0):
    s = Q.Scene((384, 384), 0.2, dt=0.01, edges=Q.EdgeLayers(5.0, 4.0), device="cpu")
    s.add(Q.FluxTube([0.0, 0.0], 2 * math.pi * flux, 0.5))
    s.add(Q.Ball([0.0, 0.0], 1.6, 5.0, 1.0))  # a hard-ish post keeps the wave off the tube's field
    pid = s.add_particle(Q.Packet(el, [-8.0, 0.0], [2.0, 0.0], [2.0, 3.0]))
    s.advance(500)
    print(f" flux = {flux} h/e:")
    print(f"   wrap fraction for (0, 6) on a 51.2-nm window was refused (1.34e-6 in the layers); here 76.8 nm")
    report("move by (0, 6)", s, pid, lambda: s.move_particle(pid, [0.0, 6.0]))

print("\n== 5. a throw in the uniform field: target velocity v -> k0 = m v / hbar (kinetic); Ehrenfest check d<r>/dt")
s = Q.Scene((192, 192), 0.25, dt=0.005, edges=Q.EdgeLayers(5.0, 4.0), device="cpu")
s.add(Q.MagneticField([0.0, 0.0, 0.5]))
pid = s.add_particle(Q.Packet(el, [3.0, -4.0], [0.0, 0.0], [1.5, 1.5]))
o = s.observables(pid)
target = np.array([1.2, -0.7])   # mass 1: v = k
dk = target - np.array(o["k"])
s.boost_particle(pid, dk)
o1 = s.observables(pid)
r0 = np.array(o1["r"])
s.advance(2)
r1 = np.array(s.observables(pid)["r"])
print(f"  observables k (kinetic) after the throw {np.round(o1['k'], 6)} (target {target}); canonical <p> "
      f"{np.round(s._grid_for(1.0).mean_p(s.wave(pid)), 4)}; d<r>/dt over 2 steps {np.round((r1 - r0) / (2 * 0.005), 4)}")
