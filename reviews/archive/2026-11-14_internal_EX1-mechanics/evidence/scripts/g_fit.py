"""R-E part G: linear_fit. York (2004) exact straight line vs the iterated effective variance on Pearson-York; the
attenuation of the effective-variance slope when x errors are random and comparable to the x spread (Monte Carlo
coverage); the singular design; the t-distribution of the 2-sigma verdict at small dof; cases exported for fit.js."""
import json, math, sys
import numpy as np
from scipy import stats, optimize
sys.path[:0] = ["/lf/lfphys"]
from lfphys.tools.stats import linear_fit

def york(x, y, sx, sy, iters=200):
    """York, Evensen, Martinez Lopez & De Basabe Delgado, Am. J. Phys. 72, 367 (2004), uncorrelated errors (r = 0):
    the least-squares line with errors in both coordinates and its standard errors (their eqs. 13-14 and the error
    expressions of their Section III)."""
    wX, wY = 1 / sx ** 2, 1 / sy ** 2
    b = np.polyfit(x, y, 1)[0]
    for _ in range(iters):
        W = wX * wY / (wX + b * b * wY)
        Xb, Yb = np.sum(W * x) / W.sum(), np.sum(W * y) / W.sum()
        U, V = x - Xb, y - Yb
        beta = W * (U / wY + b * V / wX)
        b = np.sum(W * beta * V) / np.sum(W * beta * U)
    a = Yb - b * Xb
    xs = Xb + beta
    xb = np.sum(W * xs) / W.sum(); u = xs - xb
    sb = math.sqrt(1 / np.sum(W * u * u)); sa = math.sqrt(1 / W.sum() + xb * xb * sb * sb)
    S = float(np.sum(W * (y - a - b * x) ** 2))
    return a, b, sa, sb, S

PY_X = np.array([0.0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4]); PY_Y = np.array([5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5])
PY_WX = np.array([1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1.0]); PY_WY = np.array([1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500.0])
sx, sy = 1 / np.sqrt(PY_WX), 1 / np.sqrt(PY_WY)
a, b, sa, sb, S = york(PY_X, PY_Y, sx, sy)
f = linear_fit(PY_X, PY_Y, sx, sy, "line")
print("== Pearson-York")
print(f" York 2004: a={a:.6f} b={b:.6f} sa={sa:.6f} sb={sb:.6f} S={S:.4f} S/dof={S/8:.4f}")
print(f" linear_fit (3 re-weightings): a={f['params'][0]:.6f} b={f['params'][1]:.6f} sigma_unscaled={f['sigma_unscaled']} sigma(Birge)={f['sigma']} chi2/dof={f['chi2_dof']:.4f}")
print(f" gap in b: {f['params'][1]-b:+.5f} = {(f['params'][1]-b)/sb:+.3f} York sb = {(f['params'][1]-b)/f['sigma_unscaled'][1]:+.3f} unscaled EV sb = {(f['params'][1]-b)/f['sigma'][1]:+.3f} Birge-scaled sb")

print("== attenuation: random x errors comparable to the x spread (homoscedastic): EV fixed point = OLS")
rng = np.random.default_rng(1)
N = 4000; z = 1.959963984540054
for n, span, sxv, syv in [(10, 4.5, 0.1, 0.2), (10, 1.0, 0.2, 0.05), (8, 1.0, 0.3, 0.05)]:
    xt = np.linspace(0, span, n); cov_ev = cov_y = 0; bs_ev = []; bs_y = []
    for _ in range(N):
        xo = xt + rng.normal(0, sxv, n); yo = 1 + 2 * xt + rng.normal(0, syv, n)
        g = linear_fit(xo, yo, sxv, syv, "line"); bs_ev.append(g["params"][1])
        cov_ev += abs(g["params"][1] - 2) < z * g["sigma_unscaled"][1]
        _, by, _, sby, _ = york(xo, yo, np.full(n, sxv), np.full(n, syv), iters=60); bs_y.append(by)
        cov_y += abs(by - 2) < z * sby
    print(f" n={n} x in [0,{span}] sx={sxv} sy={syv} (b sx/sy={2*sxv/syv:.0f}): mean b EV {np.mean(bs_ev):.4f}, York {np.mean(bs_y):.4f} (true 2);"
          f" 95 % coverage EV {cov_ev/N:.3f}, York {cov_y/N:.3f}")

print("== singular design: every x equal")
try:
    g = linear_fit([2.0, 2.0, 2.0, 2.0], [1.0, 1.1, 0.9, 1.05], 0.0, 0.05, "line")
    print(" linear_fit returned:", g["params"], g["sigma"])
except Exception as e:
    print(" linear_fit raised", type(e).__name__, e)
try:
    g = linear_fit([30.0, 30.0, 30.0, 40.0], [1.0, 1.1, 0.9, 1.05], 0.5, 0.05, "quadratic")
    print(" quadratic on two distinct x:", g["params"], g["sigma"], g.get("vertex"))
except Exception as e:
    print(" quadratic raised", type(e).__name__, e)

print("== the verdict |q - ref| <= 2 sigma at small dof when sigma comes from the scatter (unit weights, or Birge > 1)")
for dof in (1, 2, 3, 5, 10, 30):
    print(f" dof={dof}: false 'does not agree' rate of a correct law, sigma from the scatter: {2*stats.t.sf(2, dof):.3f} (normal 0.046)")

# cases for fit.js: (x, y, sx, sy, model)
cases = []
cases.append(("pearson_york", PY_X.tolist(), PY_Y.tolist(), sx.tolist(), sy.tolist(), "line"))
r = np.random.default_rng(5)
for i in range(60):
    model = ["line0", "line", "quadratic", "power"][i % 4]
    n = int(r.integers(4, 15))
    x = np.sort(r.uniform(0.5, 80 if model == "quadratic" else 10, n))
    if model == "power": y = 2.5 * x ** 0.7 * (1 + r.normal(0, 0.02, n))
    elif model == "quadratic": y = 20 - 0.01 * (x - 42) ** 2 + r.normal(0, 0.05, n)
    else: y = 0.3 * (model == "line") + 1.7 * x + r.normal(0, 0.1, n)
    sxv = r.uniform(0, 0.6, n) * (i % 3 != 0); syv = r.uniform(0.01, 0.2, n) * (i % 5 != 0)
    cases.append((f"rand{i}", x.tolist(), y.tolist(), sxv.tolist(), syv.tolist(), model))
out = []
for name, x, y, sxv, syv, model in cases:
    try:
        g = linear_fit(x, y, sxv, syv, model)
        out.append({"name": name, "x": x, "y": y, "sx": sxv, "sy": syv, "model": model, "params": g["params"],
                    "sigma": g["sigma"], "chi2": g["chi2"], "vertex": g.get("vertex"), "vertex_sigma": g.get("vertex_sigma"),
                    "A": g.get("A"), "A_sigma": g.get("A_sigma")})
    except ValueError as e:
        print(" skip", name, e)
json.dump(out, open("/out/g_fit_cases.json", "w"))
print("exported", len(out), "cases")
