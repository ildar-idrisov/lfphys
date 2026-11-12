"""Review B8 (charges): FunctionWorldline with v, a = None (finite differences, default step h = 1e-3 max(1, |t|) s)
on a relativistic orbit (circular, R = 1 m, beta = 0.5: period 42 ns) against the closed-form worldline."""
import sys
import numpy as np
sys.path.insert(0, "/lf/lfphys")
from lfphys.core.em import charges as ch  # noqa: E402
C, Q = ch.C, 1.602176634e-19
ref = ch.circular(1.0, 0.5 * C)
for h in (None, 1e-12):
    fw = ch.FunctionWorldline(ref.r, None, None, h=h)
    t = np.array([1e-9, 2e-9])
    r1, v1, a1 = fw.state(t)
    r0, v0, a0 = ref.state(t)
    print(f"h = {h}: |v - v_true|/|v_true| = {np.max(np.linalg.norm(v1 - v0, axis=1) / np.linalg.norm(v0, axis=1)):.2e}, "
          f"|a - a_true|/|a_true| = {np.max(np.linalg.norm(a1 - a0, axis=1) / np.linalg.norm(a0, axis=1)):.2e}; "
          f"derivative_error() = {fw.derivative_error(t)}")
    x = np.array([[3.0, 1.0, 2.0]])
    try:
        E1, _ = ch.fields(ch.Charge(Q, fw), x, 2e-8)
        E0, _ = ch.fields(ch.Charge(Q, ref), x, 2e-8)
        print(f"   field error {np.linalg.norm(E1 - E0) / np.linalg.norm(E0):.2e}")
    except Exception as exc:  # noqa: BLE001
        print(f"   fields raised {type(exc).__name__}: {exc}")
