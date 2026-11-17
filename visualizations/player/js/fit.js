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
//   verdict(res, value, σ, ref)  «Check against the law»: two errors, or Student's t for σ from the scatter (below).
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
  return { p, cov, chi2: unit ? NaN : chi2, dof, birge: unit ? NaN : birge, scaled, unit, method, iterations };
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
    const cov = [[A * A * L.cov[0][0], A * L.cov[0][1]], [A * L.cov[1][0], L.cov[1][1]]];
    out = { ...L, p: [A, L.p[1]], cov, f: (xv) => A * xv ** L.p[1] };
  } else {
    const L = linearFit(m, model, x, y, sx, sy);
    out = { ...L, f: (xv) => m.basis(xv).reduce((s, b, j) => s + b * L.p[j], 0) };
  }
  const params = {}, sigma = {};
  m.names.forEach((nm, j) => { params[nm] = out.p[j]; sigma[nm] = Math.sqrt(Math.max(0, out.cov[j][j])); });
  if (model === "quadratic") {  // the vertex x* = −c1 / (2·c2) and its σ from the covariance (the gradient)
    const [, c1, c2] = out.p;
    params.xv = -c1 / (2 * c2);
    params.yv = out.f(params.xv);
    const g = [0, -1 / (2 * c2), c1 / (2 * c2 * c2)];
    let v = 0;
    for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) v += g[a] * out.cov[a][b] * g[b];
    sigma.xv = Math.sqrt(Math.max(0, v));
  }
  return { model, names: m.names, params, sigma, cov: out.cov, chi2: out.chi2, dof: out.dof, birge: out.birge,
           scaled: out.scaled, fromScatter: !!(out.unit || out.scaled), method: out.method, iterations: out.iterations,
           n: x.length, f: out.f };
}

// The law's quantity of a fit (design §2.3 "law"): "slope" (b; p of a power law), "intercept" (a), "vertex" (x* of a
// quadratic), "exponent" (p), "coefficient" (A): {value, sigma} or null when the fit has no such quantity
export function quantity(res, q) {
  const P = res.params, S = res.sigma;
  const pick = (k) => (k in P ? { value: P[k], sigma: S[k] } : null);
  if (q === "slope") return res.model === "power" ? pick("p") : pick("b");
  if (q === "intercept") return pick("a");
  if (q === "vertex" || q === "maximum" || q === "x_max") return pick("xv");
  if (q === "exponent") return pick("p");
  if (q === "coefficient") return pick("A");
  return pick(q);
}

// agreement with the reference within k combined errors (the reference's own error, when it has one, added in
// quadrature): {agrees, diff, sigma}
export function agrees(value, sigma, ref, refSigma = 0, k = 2) {
  const s = Math.sqrt(sigma * sigma + refSigma * refSigma);
  const diff = value - ref;
  return { agrees: Math.abs(diff) <= k * s, diff, sigma: s };
}

// --- the verdict of «Check against the law» (integrator D4; review EX1-mechanics F9) -------------------------------------
// The bound is two errors (a normal 95.45 % interval) when the errors are the instruments' declared ones. When they come
// from the scatter of the points (readings without errors, or the Birge scaling applied), the error is itself estimated
// from n − p residuals, and the bound with the same coverage is Student's t quantile for n − p degrees of freedom
// (29.5 % false rejections at dof 1 with k = 2 instead of 4.55 %). A fit whose χ²/dof exceeds BIRGE_MAX² gives no verdict:
// a scatter that large means the model does not describe the points, and scaling the error up would turn a wrong model
// into an «agrees» (the PDG's caution for its scale factor: «we may choose not to use the average at all»).
export const COVER = 0.9544997361036416;  // erf(√2): the two-sided coverage of ±2σ of the normal distribution
export const BIRGE_MAX = 3;
// P(|T| ≤ t) for Student's t with ν (an integer ≥ 1) degrees of freedom, by its finite series in θ = atan(t/√ν)
// (Abramowitz & Stegun 26.7.3–26.7.4; exact for integer ν)
export function tCoverage(t, nu) {
  if (!(t > 0)) return 0;
  if (!Number.isFinite(t)) return 1;
  const th = Math.atan(t / Math.sqrt(nu)), c2 = Math.cos(th) ** 2, sn = Math.sin(th);
  if (nu % 2 === 1) {
    if (nu === 1) return 2 * th / Math.PI;
    let term = Math.cos(th), sum = term;  // cos θ · [1 + (2/3)cos²θ + (2·4)/(3·5)cos⁴θ + …], up to cos^(ν−2)θ
    for (let k = 1; k <= (nu - 3) / 2; k++) { term *= c2 * (2 * k) / (2 * k + 1); sum += term; }
    return (2 / Math.PI) * (th + sn * sum);
  }
  let term = 1, sum = 1;  // 1 + (1/2)cos²θ + (1·3)/(2·4)cos⁴θ + …, up to cos^(ν−2)θ
  for (let k = 1; k <= (nu - 2) / 2; k++) { term *= c2 * (2 * k - 1) / (2 * k); sum += term; }
  return sn * sum;
}
// the t with P(|T| ≤ t) = cover (by bisection: the coverage grows with t)
export function tQuantile(nu, cover = COVER) {
  if (!(nu >= 1)) return NaN;
  let lo = 0, hi = 1;
  while (tCoverage(hi, nu) < cover) hi *= 2;
  for (let i = 0; i < 200 && hi - lo > 1e-14 * hi; i++) { const mid = 0.5 * (lo + hi); if (tCoverage(mid, nu) < cover) lo = mid; else hi = mid; }
  return 0.5 * (lo + hi);
}
// the verdict on a fit's quantity against a reference: {agrees, diff, sigma, k, kind: "normal" | "t", dof, refused:
// null | "birge" (the scatter is more than BIRGE_MAX times the errors) | "dof" (no degree of freedom to estimate it)}
export function verdict(res, value, sigma, ref, refSigma = 0) {
  const dof = res.dof;
  if (res.fromScatter && !(dof >= 1)) return { agrees: false, diff: value - ref, sigma, k: NaN, kind: "t", dof, refused: "dof" };
  if (res.scaled && Number.isFinite(res.birge) && res.birge > BIRGE_MAX) {
    return { agrees: false, diff: value - ref, sigma, k: NaN, kind: "t", dof, refused: "birge" };
  }
  const kind = res.fromScatter ? "t" : "normal", k = kind === "t" ? tQuantile(dof) : 2;
  return { ...agrees(value, sigma, ref, refSigma, k), k, kind, dof, refused: null };
}
