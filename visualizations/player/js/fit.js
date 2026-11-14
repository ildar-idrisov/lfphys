// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The lab's fit (design lfphys/sources/explore_2026-11-14_design.md §2.3, §3.5): statistics on the student's measured
// readings, not physics. A weighted least squares with the effective variance σ_i² = σ_y,i² + (f′(x_i)·σ_x,i)², iterated
// three times after a first fit with σ_y alone (Orear, Am. J. Phys. 50, 912 (1982); to be checked against the text before
// it is cited in a user document, AGENTS rule 11). The parameters' σ come from the covariance (the inverse of the normal
// matrix), scaled by √(χ²/dof) when that ratio exceeds 1 (the Birge ratio, as the PDG scales errors): the virtual bench
// repeats exactly, so the scatter comes only from the readings' rounding and the errors from the instruments; a bench that
// scatters more is taken into account by the scaling. Readings without errors (every σ zero) are fitted with unit
// weights and their σ always from the scatter (ordinary least squares). The Python reference is
// lfphys.tools.stats.linear_fit(x, y, sx, sy, model) (fit.test.mjs).
//
//   fit(x, y, sx, sy, model)  model: "line0" y = b·x; "line" y = a + b·x; "quadratic" y = c0 + c1·x + c2·x², its vertex
//                             x* = −c1/(2·c2) with σ from the covariance (a maximum found from points); "power" y = A·x^p,
//                             a line in log–log (x, y > 0). Returns {model, params, sigma, cov, names, chi2, dof, birge,
//                             scaled, n, f(x)}; throws an Error with .why ("points", "positive", "singular") when it
//                             cannot fit.
export const MODELS = {
  // min: more points than parameters (so that χ²/dof exists; lfphys.tools.stats.linear_fit refuses fewer)
  line0: { names: ["b"], basis: (x) => [x], min: 2 },
  line: { names: ["a", "b"], basis: (x) => [1, x], min: 3 },
  quadratic: { names: ["c0", "c1", "c2"], basis: (x) => [1, x, x * x], min: 4 },
  power: { names: ["A", "p"], min: 3 },
};
export const ITERATIONS = 3;

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
  for (let j = 0; j < k; j++) if (!(Math.abs(R[j][j]) > 1e-14 * Math.abs(R[0][0]))) throw fail("singular", "the points do not determine the fit");
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

// the linear models' fit with effective variance: f′(x) from the current parameters
function linearFit(m, x, y, sx, sy) {
  const n = x.length, k = m.names.length;
  const deriv = (p, xi) => (k === 1 ? p[0] : k === 2 ? p[1] : p[1] + 2 * p[2] * xi);
  const errs = sy.some((s) => s > 0) || sx.some((s) => s > 0);
  let unit = !errs;
  let w = errs ? sy.map((s) => (s > 0 ? 1 / (s * s) : NaN)) : new Array(n).fill(1);
  if (w.some((v) => !Number.isFinite(v))) w = new Array(n).fill(1);  // first pass: σ_y alone (unit weights if one is 0)
  let { p, C } = wls(m.basis, x, y, w);
  let s2 = null;
  if (!unit) {
    for (let it = 0; it < ITERATIONS; it++) {
      s2 = x.map((xi, i) => sy[i] * sy[i] + (deriv(p, xi) * sx[i]) ** 2);
      if (s2.some((v) => !(v > 0))) { unit = true; break; }  // a reading without any error: ordinary least squares
      w = s2.map((v) => 1 / v);
      ({ p, C } = wls(m.basis, x, y, w));
    }
    if (unit) { w = new Array(n).fill(1); ({ p, C } = wls(m.basis, x, y, w)); }
  }
  let chi2 = 0;
  for (let i = 0; i < n; i++) {
    const f = m.basis(x[i]).reduce((s, b, j) => s + b * p[j], 0);
    chi2 += w[i] * (y[i] - f) ** 2;
  }
  const dof = n - k;
  const birge = dof > 0 ? Math.sqrt(chi2 / dof) : NaN;
  const scaled = unit ? dof > 0 : birge > 1;
  const cov = scaled ? C.map((r) => r.map((c) => c * birge * birge)) : C;
  return { p, cov, chi2: unit ? NaN : chi2, dof, birge: unit ? NaN : birge, scaled, unit };
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
    const L = linearFit(MODELS.line, x.map(Math.log), y.map(Math.log), sx.map((s, i) => s / x[i]), sy.map((s, i) => s / y[i]));
    const A = Math.exp(L.p[0]);
    // the covariance of (A, p) from that of (ln A, p): dA = A·d(ln A)
    const cov = [[A * A * L.cov[0][0], A * L.cov[0][1]], [A * L.cov[1][0], L.cov[1][1]]];
    out = { ...L, p: [A, L.p[1]], cov, f: (xv) => A * xv ** L.p[1] };
  } else {
    const L = linearFit(m, x, y, sx, sy);
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
           scaled: out.scaled, n: x.length, f: out.f };
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
