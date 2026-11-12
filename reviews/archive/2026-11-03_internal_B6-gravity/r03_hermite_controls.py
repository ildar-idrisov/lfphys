# Reviewer script (B6 gravity): lfphys.core.gravity.nbody, the Hermite scheme's controls.
# (a) max_passes = 1 silently makes the step P(EC)^1 whatever n_iter is (NBody._tentative: the first pass uses n = 1).
# (b) which ingredient removes the secular energy drift: the iterated corrector or the symmetrized step?
#     A: n_iter 3, symmetric steps (default); B: n_iter 1, symmetric steps; C: n_iter 3, steps NOT symmetrized
#     (Aarseth's tau at the end of the previous step, the usual adaptive rule); D: max_passes = 1 (the test's control).
# (c) the error ratio of runs with eta and eta/2 (the playground's companion; its note says "16 times").
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys/tests")
from lfphys.core.gravity import nbody as NB  # noqa: E402
from test_nbody import binary, kepler_relative, relative  # noqa: E402


class NonSymmetric(NB.NBody):
    """P(EC)^n with the usual (not time-symmetric) step: dt = Aarseth's tau at the end of the previous step."""

    def _tentative(self):
        if self._cache is not None:
            return self._cache
        if self._tau_prev is None:
            dt = self._start_guess()
            st = self._hermite_try(dt, self.n_iter)
            st.tau = self._tau_ends(st)
        else:
            dt = self._tau_prev[1]
            st = self._hermite_try(dt, self.n_iter)
            st.tau = self._tau_ends(st)
        st.passes = 1
        st.contacts = self._contacts(st)
        self._cache = st
        return st


# (a)
a, P = binary(e=0.9, eta=0.02, n_iter=3, max_passes=1)
b, _ = binary(e=0.9, eta=0.02, n_iter=1, max_passes=1)
a.advance(5 * P)
b.advance(5 * P)
print("(a) n_iter=3, max_passes=1 vs n_iter=1, max_passes=1 after 5 orbits: bit-identical positions:",
      np.array_equal(a.positions(), b.positions()), "| force evaluations", a.diagnostics()["force_evals"],
      b.diagnostics()["force_evals"], "| steps", a.diagnostics()["steps"], b.diagnostics()["steps"])

# (b)
print("(b) e = 0.9, eta = 0.02: |E(t) - E0| at apoapsis after k orbits")


def drift(make):
    nb, P = make()
    E0 = nb.energy()
    out = []
    for k in (1, 10, 30, 100):
        nb.advance((k + 0.5) * P)
        out.append(abs(nb.energy() - E0))
    return out, nb.diagnostics()["steps"]


def make_ns(n_iter):
    def f():
        nb = NonSymmetric(eta=0.02, n_iter=n_iter)
        M = 1.001
        x, v = kepler_relative(0.0, 1.0, 0.9, M)
        nb.add(-1e-3 / M * x, -1e-3 / M * v, 1.0, key="star")
        nb.add(1.0 / M * x, 1.0 / M * v, 1e-3, key="planet")
        return nb, 2 * math.pi / math.sqrt(M)
    return f


cases = {"A n_iter=3 symmetric (default)": lambda: binary(e=0.9, eta=0.02),
         "B n_iter=1 symmetric (max_passes 6)": lambda: binary(e=0.9, eta=0.02, n_iter=1, max_passes=6),
         "C n_iter=3 NOT symmetric": make_ns(3),
         "C' n_iter=10 NOT symmetric": make_ns(10),
         "D max_passes=1 (test's control)": lambda: binary(e=0.9, eta=0.02, max_passes=1)}
for name, mk in cases.items():
    d, steps = drift(mk)
    print(f"  {name:38s}: " + "  ".join(f"{k:3d}P {x:.2e}" for k, x in zip((1, 10, 30, 100), d))
          + f"   (steps {steps}; late/early(10) = {d[3] / d[1]:.2f})")

# (c)
print("(c) Kepler e = 0.5, 10 orbits: position error |x - x_kepler| for eta, eta/2, eta/16")
for eta in (0.02, 0.005):
    errs = []
    for f in (1, 2, 16):
        nb, P = binary(e=0.5, eta=eta / f)
        nb.advance(10.3 * P)
        x, _ = relative(nb)
        xk, _ = kepler_relative(10.3 * P, 1.0, 0.5, 1.001)
        errs.append(np.linalg.norm(x - xk))
    print(f"  eta = {eta}: err(eta) = {errs[0]:.3e}, err(eta/2) = {errs[1]:.3e}, err(eta/16) = {errs[2]:.3e}; "
          f"ratio eta/(eta/2) = {errs[0] / errs[1]:.2f} (16 claimed by the playground's note, 4 = 2^(4/2) expected "
          f"for dt ~ sqrt(eta)); eta/(eta/16) = {errs[0] / errs[2]:.1f}")
