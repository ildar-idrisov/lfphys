# Reviewer script (B6 gravity): how often the symmetric step rule is NOT converged with the defaults
# (dt_rtol 1e-3, max_passes 6) - such steps are not time-symmetric and are only counted in diagnostics() - and what the
# energy does on a very eccentric orbit with the defaults and with a strict rule; the Pythagorean close encounters.
import math
import sys

sys.path.insert(0, "/lf/lfphys/tests")
from test_nbody import binary, pythagorean  # noqa: E402

for e in (0.9, 0.99, 0.999):
    for kw in ({}, {"dt_rtol": 1e-8, "max_passes": 30}):
        nb, P = binary(e=e, eta=0.02, **kw)
        E0 = nb.energy()
        out = []
        for k in (1, 10, 50):
            nb.advance((k + 0.5) * P)
            out.append(abs(nb.energy() - E0) / abs(E0))
        d = nb.diagnostics()
        print(f"e = {e}, {kw or 'defaults'}: |dE/E| at 1.5, 10.5, 50.5 P = "
              + ", ".join(f"{x:.2e}" for x in out)
              + f"; steps {d['steps']}, unconverged {d['unconverged_steps']} "
                f"({100 * d['unconverged_steps'] / d['steps']:.2f} %), passes/step {d['passes'] / d['steps']:.2f}",
              flush=True)

for eta in (1e-2, 1e-3):
    nb = pythagorean(eta=eta)
    nb.advance(30.0)
    d = nb.diagnostics()
    print(f"Pythagorean to t = 30, eta = {eta}: steps {d['steps']}, unconverged {d['unconverged_steps']} "
          f"({100 * d['unconverged_steps'] / d['steps']:.2f} %), passes/step {d['passes'] / d['steps']:.2f}", flush=True)
