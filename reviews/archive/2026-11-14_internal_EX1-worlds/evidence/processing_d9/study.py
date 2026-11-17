"""D9 study: the bootstrap error of |gamma_12| (old vs candidate) against the Monte Carlo scatter of the estimator."""
import math, sys, json, time
import numpy as np
from lfphys.tools import stats as S

def basis(nb=200, fr=10.0, env=0.35):
    """Two slits: A_j(x) = sinc(env x) exp(+-i pi fr x), x in [-1, 1], integrated over nb bins (fine sampling)."""
    sub = 16
    xe = np.linspace(-1, 1, nb + 1)
    xs = (xe[:-1, None] + (np.arange(sub)[None, :] + 0.5) / sub * (xe[1] - xe[0])).ravel()
    E = np.sinc(env * 4 * xs)
    A1, A2 = E * np.exp(1j * math.pi * fr * xs / 2), E * np.exp(-1j * math.pi * fr * xs / 2)
    rb = lambda f: f.reshape(nb, sub).mean(axis=1)
    return rb(np.abs(A1) ** 2), rb(np.abs(A2) ** 2), rb((A1 * A2.conj()).real) + 1j * rb((A1 * A2.conj()).imag)

def pattern(b, g11, g22, gam, phi=0.3):
    b11, b22, b12 = b
    G12 = gam * math.sqrt(g11 * g22) * np.exp(1j * phi)
    P = g11 * b11 + g22 * b22 + 2 * (G12 * b12).real
    return np.maximum(P, 0)

def new_err(h, b11, b22, b12, g11, g22, dark=None, rng=None, n_boot=100):
    rng = rng or np.random.default_rng(0)
    h = np.asarray(h, float)
    d = np.zeros_like(h) if dark is None else np.asarray(dark, float)
    X = np.stack([g11 * b11 + g22 * b22, b12.real, b12.imag], axis=1)
    beta = S._fit_beta(h, X, d)
    if beta is None or not beta[0] > 0:
        return None, 0
    amp = math.hypot(beta[1], beta[2]); gam = amp / (2 * beta[0] * math.sqrt(g11 * g22))
    bb = beta.copy()
    if gam > 1:
        bb[1:] /= gam
    mu = np.maximum(X @ bb + d, 0.0)
    vals = []
    for _ in range(n_boot):
        g_b, _ = S.coherence_ml(rng.poisson(mu).astype(float), b11, b22, b12, g11, g22, dark=d)
        if g_b is not None:
            vals.append(g_b)
    if len(vals) < 0.9 * n_boot:
        return None, len(vals)
    q16, q84 = np.percentile(vals, [15.865525393145708, 84.13447460685429])
    return float(0.5 * (q84 - q16)), len(vals)

def main():
    b = basis()
    g11, g22 = 1.0, 0.8
    rng = np.random.default_rng(7)
    out = []
    for gam in (1.0, 0.95, 0.7, 0.3):
        P = pattern(b, g11, g22, gam)
        for N in (50, 100, 200, 600, 2000, 5000):
            vals = []
            for _ in range(600):
                h = rng.poisson(P / P.sum() * N).astype(float)
                g, _ = S.coherence_ml(h, *b, g11, g22)
                if g is not None:
                    vals.append(g)
            vals = np.array(vals)
            sd = float(np.std(vals, ddof=1)); q = np.percentile(vals, [15.87, 84.13]); hw = 0.5 * float(q[1] - q[0])
            ro, rn, fo, fn = [], [], 0, 0
            K = 30
            for k in range(K):
                h = rng.poisson(P / P.sum() * N).astype(float)
                eo, _ = S.coherence_boot_err(h, *b, g11, g22, rng=np.random.default_rng(k))
                en, _ = new_err(h, *b, g11, g22, rng=np.random.default_rng(k))
                if eo is None: fo += 1
                else: ro.append(eo / hw)
                if en is None: fn += 1
                else: rn.append(en / hw)
            def summ(r):
                r = np.array(r)
                return (float(np.median(r)), float(np.mean((r > 0.5) & (r < 2))), float(r.min()), float(r.max())) if len(r) else None
            row = {"gam": gam, "N": N, "n_est": len(vals), "mean": float(vals.mean()), "sd": sd, "hw": hw,
                   "old": summ(ro), "old_none": fo, "new": summ(rn), "new_none": fn}
            print(json.dumps(row), flush=True)
            out.append(row)
    json.dump(out, open(sys.argv[1], "w"), indent=1)

main()
