import sys, signal, math, numpy as np
sys.path.insert(0, "/lf/visualizations/server")
from lfviz import protocol
signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(TimeoutError()))
rng = np.random.default_rng(1)
hangs, worst = [], 0.0
cases = []
for base in [10.6, 1.0, 3.3, 1e3 + 0.1, 1.7e9, 1e11, 9.80665]:
    for k in range(1, 6):  # a column constant up to k ulps of noise (a conserved quantity, vx in vacuum)
        col = base + np.arange(8) % (k + 1) * np.spacing(base)
        cases.append((f"{base} + {k} ulp noise", np.column_stack([np.linspace(0, 1, 8), col])))
for name, arr in cases:
    signal.alarm(3)
    try:
        q = protocol.quantize(arr, "u16")
        signal.alarm(0)
        dec = protocol.dequantize(q.codes, "u2", q.q).astype(np.float64)
        e = float(np.abs(dec - arr).max())
        worst = max(worst, e)
    except TimeoutError:
        hangs.append(name)
print(f"{len(cases)} cases; hung (>3 s in quantize): {len(hangs)}: {hangs[:8]}")
print(f"worst abs error of the others: {worst:.3g}")
