# lfphys source verification — 2026-11-17: York's straight-line fit (lab fit, EX1 review D3)

The exact algorithm of `tools.stats.linear_fit` and its mirror `visualizations/player/js/fit.js`, written when the
EX1 reviews were processed (engine → player).

The Python reference is `lfphys/lfphys/tools/stats.py` `linear_fit` / `_york` / `_wls` (final). `fit.js` must give the
same numbers to 1e-12 relative on every fixture case.

Source, verified on the paper's text (AIP PDF, read 2026-11-17): York, Evensen, Martínez López & De Basabe Delgado,
Am. J. Phys. 72, 367 (2004), Table I, eqs. (13a)–(13d), steps (1)–(10) of section III, cov(a, b) = −x̄σ_b² (section
II). Benchmark (their Table II, data set 3, Pearson's data with York's weights): a = 5.47991, b = −0.480533, S/(n−2) =
1.483, σ_a = 0.294970, σ_b = 0.057985. The Python reproduces a = 5.479910224, b = −0.480533407, σ_a = 0.294970735,
σ_b = 0.057985009 (unscaled), χ²/dof = 1.48329, in 9 iterations.

## 0. What changes, what stays

| model | before | now |
|---|---|---|
| `line` (y = a + b·x) | effective variance, 3 re-weightings | **York**, iterated to convergence |
| `line0` (y = b·x) | effective variance, 3 re-weightings | **York with the intercept fixed at 0** (below) |
| `power` (y = A·x^p) | `line` on (ln x, ln y), σ → σ/x, σ/y | the same, so now **York** on the logs |
| `quadratic` | effective variance, 3 re-weightings | **unchanged** (effective variance, `ITERATIONS = 3`) |

Unchanged as well:
- input handling: fit.js drops non-finite rows and takes |σ|; Python refuses them;
- the minimum point counts;
- the unit-weights (OLS) path;
- the Birge scaling;
- the vertex and its σ;
- the power law's (A, p) covariance transform.

## 1. Constants

```
ITERATIONS    = 3       // the parabola's effective variance only
YORK_TOL      = 1e-14
YORK_MAX_ITER = 200
SINGULAR      = 1e-14   // |R_jj| <= SINGULAR·|R_00| → refuse (unchanged; now also in Python)
```

## 2. The start, and the singular-design refusal (all models)

1. Choose the start's weights:
   - `unit = !(any sx_i > 0 || any sy_i > 0)`;
   - if every sy_i > 0, then w_i = 1/sy_i²; otherwise w_i = 1 for all i.
2. Run `wls(basis, x, y, w)` by Householder QR, as now.
3. Refuse when `!(|R_jj| > SINGULAR·|R_00|)` for any j, or when a column norm is not > 0: `why: "singular"`.
   - Python raises `ValueError`, code `"fit.singular"`, text "the points do not determine the fit (all x equal, or
     fewer distinct x than parameters)".
   - The design matrix is [1, x] for `line`/`power`, [x] for `line0`, [1, x, x²] for `quadratic`.
4. If `unit`: OLS on unit weights (as now) and stop: `method = "ols"`.

## 3. Straight lines: York (r_i = 0)

Inputs, after the power transform for `power`: X_i = x_i, Y_i = y_i, vx_i = sx_i², vy_i = sy_i². The start slope b is
the start's slope (p[1] for `line`/`power`, p[0] for `line0`). `origin = (model === "line0")`.

```
it = 0
loop:
  it += 1
  W_i = 1 / (vy_i + b*b*vx_i)                  // if any W_i is not finite → OLS fallback (§5)
  if origin: Xb = Yb = 0
  else:      Xb = ΣW_i X_i / ΣW_i,  Yb = ΣW_i Y_i / ΣW_i
  U_i = X_i − Xb,  V_i = Y_i − Yb
  β_i = W_i·(U_i·vy_i + b·V_i·vx_i)
  den = Σ W_i β_i U_i,  num = Σ W_i β_i V_i
  if !(den > 0) or !isFinite(num): refuse "no_convergence"
  b_new = num / den
  scale = sqrt( Σ W_i V_i² / Σ W_i U_i² )      // with the W, U, V of this pass
  done = |b_new − b| <= YORK_TOL·(|b_new| + scale)
  b = b_new
  if done: break
  if it >= YORK_MAX_ITER: refuse "no_convergence"
```

The refusal "no_convergence": Python raises `ValueError`, code `"fit.no_convergence"`, text "the fit with errors in x
and y does not converge". In fit.js, throw with `why: "converge"` and a message of your own.

### The final pass at the converged b (York's steps 7–10)

```
W_i = 1 / (vy_i + b*b*vx_i)                    // not finite → OLS fallback (§5)
Xb, Yb, U_i, V_i, β_i as in the loop (with this W and this b)
xa_i = Xb + β_i                                // the adjusted abscissae (Xb = 0 for origin)
```

For `origin`:

```
Su = Σ W_i xa_i²       (no centring);  if !(Su > 0) → "singular"
params = [b];  cov = [[1/Su]]
```

Otherwise (`line`, `power`):

```
sw = Σ W_i;  xm = Σ W_i xa_i / sw;  u_i = xa_i − xm
Su = Σ W_i u_i²;  if !(Su > 0) → "singular"
vb = 1/Su
params = [Yb − b·Xb, b]
cov = [[1/sw + xm²·vb, −xm·vb], [−xm·vb, vb]]
```

## 4. χ², Birge, outputs (all non-OLS paths)

- The effective error of each point:
  - York: σ_i = 1/√W_i, with the final pass's W;
  - the parabola: σ_i² = sy_i² + (f′(x_i)·sx_i)², from its last re-weighting, as now.
- χ² = Σ ((y_i − f(x_i))/σ_i)². For York this is S = ΣW_i (Y_i − a − bX_i)² (a = 0 for origin).
- dof = n − p.
- Birge scaling: when χ²/dof > 1, cov is multiplied by χ²/dof and `scaled = true`.
- `power`: A = exp(params[0]). The (A, p) covariance is transformed from (ln A, p) as fit.js does now.

## 5. OLS fallback (as before)

Fit by unit-weight OLS, as when no errors are given (σ from the scatter, chi2 NaN, `scaled = dof > 0`), when either
happens:
- a York W_i is not finite (a point with sy_i = 0 and sx_i·b = 0, e.g. a reading without any error);
- in the parabola, an effective σ_i² is not > 0.

## 6. Notes for the parity fixture (`player/js/tests/fixtures/make_fit_cases.py`)

Regenerate it with the new Python. Worth adding:
- Pearson–York (x, y, sx = 1/√wX, sy = 1/√wY), `line`;
- a set with random x errors comparable to the spread: n = 8, x = linspace(0, 1), sx = 0.3, sy = 0.05;
- a `line0` with equal sx = sy: (1, 2), (2, 4.2), σ 0.1 → b = (16.64 + √(16.64² + 4·10.4²))/20.8;
- a `power` with x errors;
- the singular cases. Python refuses each with code `fit.singular`; fit.js must throw `why: "singular"`:
  - all x equal (`line`);
  - x = 0 throughout (`line0`);
  - x = 30, 30, 30, 40 (`quadratic`).

Python's output now also carries `method` ("york" | "effective_variance" | "ols") and `iterations`. Python sums with
NumPy's pairwise summation and JS adds sequentially; the difference stays at the 1e-16 level, far inside 1e-12.

## 7. The text for users (fit.js header comment, any help text)

Straight lines (through the origin or not, and power laws in log–log): York's least-squares line with errors in both x
and y (York et al., Am. J. Phys. 72, 367 (2004)). This is the minimum of S = Σ(y − f(x))²/(σ_y² + b²σ_x²) with the
maximum-likelihood errors.

The parabola keeps the effective variance (Orear 1982), three re-weightings. It is an approximation: it is biased when
random x errors are comparable to the spread of x. On S03's lab C it equals the minimum of S within 0.001 σ.
