# mutation check of the strengthened Penrose test: a wrong contraction (gamma -> 1) or a wrong radius must fail it
import inspect, math, numpy as np, pytest
from lfphys.core import lorentz as L
src = inspect.getsource(L.sphere_outline)
import tests.test_lorentz_3d as TT
for name, mut in (("no contraction", src.replace("g = float(gamma_of(b))", "g = 1.0")),
                  ("radius x1.01", src.replace("alpha = np.arcsin(radius / dist)", "alpha = np.arcsin(1.01 * radius / dist)"))):
    ns = dict(L.__dict__)
    exec(mut, ns)
    orig = L.sphere_outline
    L.sphere_outline = ns["sphere_outline"]
    try:
        TT.test_penrose_circle(); print(name, "-> test PASSED (not caught)")
    except AssertionError as e:
        print(name, "-> test FAILED (caught)")
    finally:
        L.sphere_outline = orig
