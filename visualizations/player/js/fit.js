// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The lab's fit (design lfphys/sources/explore_2026-11-14_design.md §2.3, §3.5): statistics on the student's measured
// readings, not physics. The Python reference is lfphys.tools.stats.linear_fit(x, y, sx, sy, model); this file mirrors
// it step by step (integrator D3; the shared fixture fixtures/fit_cases.json, fit.test.mjs, agrees to 1e-12).
//  - The start: a weighted least squares with σ_y alone (unit weights if any σ_y is 0), by Householder QR, which also
//    refuses a singular design (|R_jj| ≤ 1e-14·|R_00|: all x equal, or fewer distinct x than parameters).
//  - Straight lines (through the origin or not, and power laws in log–log): York's least-squares line with errors in
//    both x and y (York, Evensen, Martínez López & De Basabe Delgado, Am. J. Phys. 72, 367 (2004), eqs. (13), r_i = 0),
//    iterated from the start's slope to convergence: the minimum of S = Σ(y − f(x))²/(σ_y² + b²σ_x²) with the
//    maximum-likelihood errors. Through the origin, the same iteration with the centre fixed at (0, 0).
//  - The parabola keeps the effective variance σ_i² = σ_y,i² + (f′(x_i)·σ_x,i)² (Orear 1982), three re-weightings. It is
//    an approximation: it is biased when random x errors are comparable to the spread of x (on S03's lab part 3 it
//    equals the minimum of S within 0.001 σ).
//  - χ² = Σ (y_i − f(x_i))²/σ_i² with each point's effective error (York: 1/√W_i); dof = n − p. The parameters' σ come
//    from the covariance, scaled by √(χ²/dof) when that ratio exceeds 1 (the Birge ratio, as the PDG scales errors): the
//    virtual bench repeats exactly, so the scatter comes only from the readings' rounding and the errors from the
//    instruments; a bench that scatters more is taken into account by the scaling. Readings without errors (every σ
//    zero), or a point whose effective error comes out 0, are fitted with unit weights and their σ always from the
//    scatter (ordinary least squares).
//
//   fit(x, y, sx, sy, model)  model: "line0" y = b·x; "line" y = a + b·x; "quadratic" y = c0 + c1·x + c2·x², its vertex
//                             x* = −c1/(2·c2) with σ from the covariance (a maximum found from points); "power" y = A·x^p,
//                             a line in log–log (x, y > 0). Returns {model, params, sigma, cov, names, chi2, dof, birge,
//                             scaled, fromScatter, method ("york" | "effective_variance" | "ols"), iterations, n, f(x)};
//                             throws an Error with .why ("points", "positive", "singular", "converge") when it cannot
//                             fit. fromScatter: the parameters' σ come from the scatter of the
//                             points (no declared errors, or the Birge scaling applied), not from the declared errors.
//                             EX2 §5 F6 (c): also sigmaDeclared (the σ from the declared errors, unscaled; from the
//                             scatter when there are none), sigmaScaled (multiplied by the Birge ratio when χ²/dof > 1)
//                             and p (the p-value of χ² for dof degrees of freedom, chi2Sf). The fit is a tool: it prints
//                             its output and judges nothing (the owner, 2026-11-18: «Check against the law» and its
//                             verdict are withdrawn, with their bounds of two errors or Student's t).
//   chi2Sf(χ², ν)             P(X² ≥ χ²) for ν degrees of freedom: the regularised upper incomplete gamma Q(ν/2, χ²/2).
export const MODELS = {
  // min: more points than parameters (so that χ²/dof exists; lfphys.tools.stats.linear_fit refuses fewer)
  line0: { names: ["b"], basis: (x) => [x], min: 2 },
  line: { names: ["a", "b"], basis: (x) => [1, x], min: 3 },
  quadratic: { names: ["c0", "c1", "c2"], basis: (x) => [1, x, x * x], min: 4 },
  power: { names: ["A", "p"], min: 3 },
};
export const ITERATIONS = 3;         // the parabola's effective variance only
export const YORK_TOL = 1e-14, YORK_MAX_ITER = 200, SINGULAR = 1e-14;

const fail = (why, msg) => Object.assign(new Error(msg), { why });

// One weighted linear least squares on a basis: the parameters and the (unscaled) covariance (XᵀWX)⁻¹. By Householder QR
// of the row-weighted, column-scaled design matrix, as lfphys.tools.stats._wls does: the normal equations of a parabola
// over angles of tens of degrees are too ill-conditioned to agree with it to 1e-12.
function wls(basis, x, y, w) {
  const n = x.length, k = basis(x[0]).length;
  const sw = w.map(Math.sqrt);
  const A = x.map((xi, i) => basis(xi).map((v) => v * sw[i]));
  const b = y.map((yi, i) => yi * sw[i]);
  const norms = Array.from({ length: k }, (_, j) => Math.hypot(...A.map((r) => r[j])) || 1);
  for (const r of A) for (let j = 0; j < k; j++) r[j] /= norms[j];
  for (let j = 0; j < k; j++) {  // the reflection that zeroes column j below the diagonal, applied to A and b
    let nrm = 0;
    for (let i = j; i < n; i++) nrm = Math.hypot(nrm, A[i][j]);
    if (!(nrm > 0)) throw fail("singular", "the points do not determine the fit");
    const alpha = A[j][j] > 0 ? -nrm : nrm;
    const v = new Array(n).fill(0);
    v[j] = A[j][j] - alpha;
    for (let i = j + 1; i < n; i++) v[i] = A[i][j];
    const vv = v.reduce((q, z) => q + z * z, 0);
    if (vv > 0) {
      for (let c = j; c < k; c++) {
        let d = 0;
        for (let i = j; i < n; i++) d += v[i] * A[i][c];
        const f = 2 * d / vv;
        for (let i = j; i < n; i++) A[i][c] -= f * v[i];
      }
      let d = 0;
      for (let i = j; i < n; i++) d += v[i] * b[i];
      const f = 2 * d / vv;
      for (let i = j; i < n; i++) b[i] -= f * v[i];
    }
  }
  const R = A.slice(0, k).map((r) => r.slice());
  for (let j = 0; j < k; j++) if (!(Math.abs(R[j][j]) > SINGULAR * Math.abs(R[0][0]))) throw fail("singular", "the points do not determine the fit");
  // R⁻¹ by back substitution (upper triangular)
  const Ri = Array.from({ length: k }, () => new Array(k).fill(0));
  for (let c = 0; c < k; c++) {
    for (let r = k - 1; r >= 0; r--) {
      let sum = r === c ? 1 : 0;
      for (let m = r + 1; m < k; m++) sum -= R[r][m] * Ri[m][c];
      Ri[r][c] = sum / R[r][r];
    }
  }
  const p = Ri.map((row, r) => row.reduce((q, v, j) => q + v * b[j], 0) / norms[r]);
  const C = Array.from({ length: k }, (_, a) => Array.from({ length: k }, (_, c) => {
    let sum = 0;
    for (let m = 0; m < k; m++) sum += Ri[a][m] * Ri[c][m];
    return sum / (norms[a] * norms[c]);
  }));
  return { p, C };
}

// York's iteration (eqs. (13), r_i = 0; lfphys.tools.stats._york) from the start slope b; origin: the line through the
// origin (the centre fixed at (0, 0)). Returns {p, C, W, it}, or null when a weight is not finite (a point without any
// error at this slope: the caller fits by ordinary least squares)
function york(x, y, sx, sy, b, origin) {
  const n = x.length, vx = sx.map((s) => s * s), vy = sy.map((s) => s * s);
  const sum = (f) => { let a = 0; for (let i = 0; i < n; i++) a += f(i); return a; };
  const weights = (bb) => { const W = vy.map((v, i) => 1 / (v + bb * bb * vx[i])); return W.every(Number.isFinite) ? W : null; };
  const centre = (W) => {
    if (origin) return { Xb: 0, Yb: 0, U: x, V: y };
    const sw = sum((i) => W[i]), Xb = sum((i) => W[i] * x[i]) / sw, Yb = sum((i) => W[i] * y[i]) / sw;
    return { Xb, Yb, U: x.map((v) => v - Xb), V: y.map((v) => v - Yb) };
  };
  const noConv = () => fail("converge", "the fit with errors in x and y does not converge");
  let it = 0;
  for (;;) {
    it++;
    const W = weights(b);
    if (!W) return null;
    const { U, V } = centre(W);
    const beta = W.map((w, i) => w * (U[i] * vy[i] + b * V[i] * vx[i]));
    const den = sum((i) => W[i] * beta[i] * U[i]), num = sum((i) => W[i] * beta[i] * V[i]);
    if (!(den > 0 && Number.isFinite(num))) throw noConv();
    const bNew = num / den;
    const scale = Math.sqrt(sum((i) => W[i] * V[i] * V[i]) / sum((i) => W[i] * U[i] * U[i]));
    const done = Math.abs(bNew - b) <= YORK_TOL * (Math.abs(bNew) + scale);
    b = bNew;
    if (done) break;
    if (it >= YORK_MAX_ITER) throw noConv();
  }
  const W = weights(b);  // steps (7)–(10) at the converged slope
  if (!W) return null;
  const { Xb, Yb, U, V } = centre(W);
  const xa = W.map((w, i) => Xb + w * (U[i] * vy[i] + b * V[i] * vx[i]));  // the least-squares-adjusted abscissae
  if (origin) {
    const Su = sum((i) => W[i] * xa[i] * xa[i]);
    if (!(Su > 0)) throw fail("singular", "the points do not determine the fit");
    return { p: [b], C: [[1 / Su]], W, it };
  }
  const sw = sum((i) => W[i]), xm = sum((i) => W[i] * xa[i]) / sw;
  const Su = sum((i) => W[i] * (xa[i] - xm) ** 2);
  if (!(Su > 0)) throw fail("singular", "the points do not determine the fit");
  const vb = 1 / Su;
  return { p: [Yb - b * Xb, b], C: [[1 / sw + xm * xm * vb, -xm * vb], [-xm * vb, vb]], W, it };
}

// the linear models' fit: the start, then York (straight lines) or the effective variance (the parabola), then χ², the
// Birge scaling (lfphys.tools.stats.linear_fit)
function linearFit(m, model, x, y, sx, sy) {
  const n = x.length, k = m.names.length, ones = new Array(n).fill(1);
  let unit = !(sy.some((s) => s > 0) || sx.some((s) => s > 0));  // readings without errors: ordinary least squares
  let { p, C } = wls(m.basis, x, y, sy.every((s) => s > 0) ? sy.map((s) => 1 / (s * s)) : ones);  // the start
  let s2 = ones, method = "ols", iterations = 0;
  if (!unit && model === "quadratic") {
    method = "effective_variance";
    for (let it = 0; it < ITERATIONS; it++) {
      const e2 = x.map((xi, i) => sy[i] * sy[i] + ((p[1] + 2 * p[2] * xi) * sx[i]) ** 2);
      if (e2.some((v) => !(v > 0))) { unit = true; break; }  // a reading without any error: ordinary least squares
      ({ p, C } = wls(m.basis, x, y, e2.map((v) => 1 / v)));
      s2 = e2; iterations++;
    }
  } else if (!unit) {
    const r = york(x, y, sx, sy, p[p.length - 1], model === "line0");
    if (!r) unit = true;
    else { ({ p, C } = r); s2 = r.W.map((w) => 1 / w); method = "york"; iterations = r.it; }
  }
  if (unit) { s2 = ones; ({ p, C } = wls(m.basis, x, y, ones)); method = "ols"; iterations = 0; }
  let chi2 = 0;
  for (let i = 0; i < n; i++) {
    const f = m.basis(x[i]).reduce((s, b, j) => s + b * p[j], 0);
    chi2 += (y[i] - f) ** 2 / s2[i];
  }
  const dof = n - k;
  const birge = dof > 0 ? Math.sqrt(chi2 / dof) : NaN;
  const scaled = unit ? dof > 0 : birge > 1;
  const cov = scaled ? C.map((r) => r.map((c) => c * birge * birge)) : C;
  return { p, cov, cov0: unit ? cov : C, chi2: unit ? NaN : chi2, dof, birge: unit ? NaN : birge, scaled, unit, method, iterations };
}

export function fit(x, y, sx, sy, model) {
  const m = MODELS[model];
  if (!m) throw fail("model", `no fit model ${model}`);
  x = x.map(Number); y = y.map(Number);
  sx = (sx || x.map(() => 0)).map((v) => Math.abs(Number(v) || 0));
  sy = (sy || y.map(() => 0)).map((v) => Math.abs(Number(v) || 0));
  const ok = x.map((_, i) => Number.isFinite(x[i]) && Number.isFinite(y[i]));
  const keep = (a) => a.filter((_, i) => ok[i]);
  x = keep(x); y = keep(y); sx = keep(sx); sy = keep(sy);
  if (x.length < m.min) throw fail("points", "too few points for this fit");
  let out;
  if (model === "power") {
    if (x.some((v) => !(v > 0)) || y.some((v) => !(v > 0))) throw fail("positive", "a power law needs positive values");
    const L = linearFit(MODELS.line, "power", x.map(Math.log), y.map(Math.log), sx.map((s, i) => s / x[i]), sy.map((s, i) => s / y[i]));
    const A = Math.exp(L.p[0]);
    // the covariance of (A, p) from that of (ln A, p): dA = A·d(ln A)
    const tr = (C) => [[A * A * C[0][0], A * C[0][1]], [A * C[1][0], C[1][1]]];
    out = { ...L, p: [A, L.p[1]], cov: tr(L.cov), cov0: tr(L.cov0), f: (xv) => A * xv ** L.p[1] };
  } else {
    const L = linearFit(m, model, x, y, sx, sy);
    out = { ...L, f: (xv) => m.basis(xv).reduce((s, b, j) => s + b * L.p[j], 0) };
  }
  const params = {}, sigma = {}, sigmaDeclared = {};
  m.names.forEach((nm, j) => {
    params[nm] = out.p[j];
    sigma[nm] = Math.sqrt(Math.max(0, out.cov[j][j]));
    sigmaDeclared[nm] = Math.sqrt(Math.max(0, out.cov0[j][j]));
  });
  if (model === "quadratic") {  // the vertex x* = −c1 / (2·c2) and its σ from the covariance (the gradient)
    const [, c1, c2] = out.p;
    params.xv = -c1 / (2 * c2);
    params.yv = out.f(params.xv);
    const g = [0, -1 / (2 * c2), c1 / (2 * c2 * c2)];
    const vOf = (C) => { let v = 0; for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) v += g[a] * C[a][b] * g[b]; return Math.sqrt(Math.max(0, v)); };
    sigma.xv = vOf(out.cov);
    sigmaDeclared.xv = vOf(out.cov0);
  }
  // the σ scaled by the Birge ratio √(χ²/dof) when it exceeds 1: printed beside the declared ones, never instead (EX2 F6 (c))
  const sigmaScaled = Object.fromEntries(Object.entries(sigmaDeclared).map(([k, v]) => [k, out.unit || !(out.birge > 1) ? v : v * out.birge]));
  return { model, names: m.names, params, sigma, sigmaDeclared, sigmaScaled, cov: out.cov, chi2: out.chi2, dof: out.dof,
           birge: out.birge, p: out.unit ? NaN : chi2Sf(out.chi2, out.dof), scaled: out.scaled, fromScatter: !!(out.unit || out.scaled),
           unit: !!out.unit, method: out.method, iterations: out.iterations, n: x.length, f: out.f };
}

// --- the p-value of χ² (EX2 §5 F6 (c)) -------------------------------------------------------------------------------------
// ln Γ(x) for x > 0: Lanczos (g = 7, nine coefficients; relative error below 1e-15), with the reflection for x < 0.5
const LANCZOS = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059,
  12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
export function lnGamma(x) {
  if (x < 0.5) return Math.log(Math.PI / Math.abs(Math.sin(Math.PI * x))) - lnGamma(1 - x);
  x -= 1;
  let a = LANCZOS[0];
  const tt = x + 7.5;
  for (let i = 1; i < 9; i++) a += LANCZOS[i] / (x + i);
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(tt) - tt + Math.log(a);
}
// the regularised lower incomplete gamma P(a, x) by its series (x < a + 1), the upper Q(a, x) by Lentz's continued
// fraction (x ≥ a + 1) (Numerical Recipes, §6.2)
function gammaP(a, x) {
  let ap = a, del = 1 / a, sum = del;
  for (let n = 0; n < 1000; n++) { ap += 1; del *= x / ap; sum += del; if (Math.abs(del) < Math.abs(sum) * 1e-17) break; }
  return sum * Math.exp(-x + a * Math.log(x) - lnGamma(a));
}
function gammaQ(a, x) {
  const tiny = 1e-300;
  let b = x + 1 - a, c = 1 / tiny, d = 1 / b, h = d;
  for (let i = 1; i < 1000; i++) {
    const an = -i * (i - a);
    b += 2;
    d = an * d + b; if (Math.abs(d) < tiny) d = tiny;
    c = b + an / c; if (Math.abs(c) < tiny) c = tiny;
    d = 1 / d;
    const del = d * c;
    h *= del;
    if (Math.abs(del - 1) < 1e-17) break;
  }
  return Math.exp(-x + a * Math.log(x) - lnGamma(a)) * h;
}
export function chi2Sf(chi2, dof) {
  if (!(dof > 0) || !(chi2 >= 0) || !Number.isFinite(chi2)) return NaN;
  const a = dof / 2, x = chi2 / 2;
  if (x === 0) return 1;
  return x < a + 1 ? Math.max(0, 1 - gammaP(a, x)) : gammaQ(a, x);
}
