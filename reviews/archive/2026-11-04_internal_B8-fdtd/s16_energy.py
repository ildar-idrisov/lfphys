# Review B8-fdtd, script s16: is energy()['total'] = (1/2) sum eps|E^n|^2 + (1/2) sum mu H^{n-1/2}.H^{n+1/2} the
# scheme's conserved invariant beyond the tests' PEC box? Closed lossless worlds: PEC/PMC walls with both
# polarizations, a Bloch-periodic (complex) world, a PEC body (edge rule) inside, 3-D with PMC walls; random fields.
# Derivation (leapfrog): E^{n+1} = E^n + dt eps^-1 C H^{n+1/2}, H^{n+1/2} = H^{n-1/2} - dt mu^-1 C^T E^n gives
# W^{n+1} - W^n = dt H^{n+1/2}.C^T(E^{n+1} + E^n) - dt H^{n+1/2}.C^T(E^{n+1} + E^n) = 0 when the E update's curl is the
# adjoint of the H update's (Yee's staggering with PEC/PMC/periodic sides).
import argparse
import math
import numpy as np
from lfphys.core.em import fdtd as F
argparse.ArgumentParser(description=__doc__).parse_args()


def drift(w, steps=2000):
    rng = np.random.default_rng(4)
    for c in w.comps:
        a = rng.standard_normal(w.shape[:w.dim])
        if w.complex:
            a = a + 1j * rng.standard_normal(w.shape[:w.dim])
        w.set_field(c, a)
    e0 = w.energy()["total"]
    es = []
    for _ in range(10):
        w.advance(steps // 10)
        es.append(w.energy()["total"])
    return max(abs(e - e0) for e in es) / e0


w = F.FDTD((1.0, 0.8), 0.04, pol="both", boundary={"x": ("pec", "pmc"), "y": ("pmc", "pec")})
w.add_body(F.Cylinder((0.5, 0.4), 0.2), F.Medium(eps=3.0, mu=1.5))
print(f"  2-D both pols, PEC/PMC walls, a dielectric-magnetic body: relative drift {drift(w):.1e}")
w = F.FDTD((1.0, 0.8), 0.04, pol="tm", boundary="periodic", bloch=(2 * math.pi * 0.3, 1.0))
w.add_body(F.Cylinder((0.5, 0.4), 0.2), F.Medium(eps=3.0))
print(f"  2-D Bloch-periodic (complex): relative drift {drift(w):.1e}")
w = F.FDTD((1.0, 0.8), 0.04, pol="te", boundary="pec")
w.add_body(F.Cylinder((0.5, 0.4), 0.2), F.Medium.pec())
print(f"  2-D TE, a PEC cylinder (edge rule) inside a PEC box: relative drift {drift(w):.1e}")
w = F.FDTD((0.6, 0.5, 0.4), 0.05, boundary={"x": "pmc", "y": ("pec", "pmc"), "z": "periodic"})
w.add_body(F.Sphere((0.3, 0.25, 0.2), 0.12), F.Medium(eps=3.0))
print(f"  3-D PMC/PEC/periodic sides, a sphere: relative drift {drift(w, 1000):.1e}")
w = F.FDTD((1.0, 0.8), 0.04, pol="tm", boundary="pec")
w.add_body(F.Cylinder((0.5, 0.4), 0.2), F.Medium(eps=2.0, poles=[F.Debye(1.0, 0.3)]))
print(f"  negative control, a lossy Debye body: relative change {drift(w):.1e}")
