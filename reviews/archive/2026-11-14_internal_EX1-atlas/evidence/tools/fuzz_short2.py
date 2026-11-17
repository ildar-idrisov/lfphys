import sys, signal, math, faulthandler, numpy as np
sys.path.insert(0, "/lf/visualizations/server")
from lfviz import protocol
signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(TimeoutError()))
rng = np.random.default_rng(7)
n = hang = 0; ex = []
for i in range(400):
    base = float(10 ** rng.uniform(-3, 12)) * (1 if rng.random() < 0.8 else -1)
    k = int(rng.integers(1, 9))
    arr = np.array([base, base + k * np.spacing(base)])
    n += 1
    signal.alarm(1)
    try:
        protocol.quantize(arr, "u16"); signal.alarm(0)
    except TimeoutError:
        hang += 1
        if len(ex) < 5: ex.append((base, k))
print(f"{n} two-value blobs [x, x + k ulp] (1 <= k <= 8), x log-uniform in 1e-3..1e12: {hang} hang in protocol.quantize; e.g. {ex}")
# where it hangs
signal.alarm(0)
faulthandler.dump_traceback_later(2, exit=True)
protocol.quantize(np.array([1000.1, 1000.1 + 2 * np.spacing(1000.1)]), "u16")
