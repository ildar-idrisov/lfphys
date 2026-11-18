// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The lab's fit (fit.js; design lfphys/sources/explore_2026-11-14_design.md §2.3): every model on exact data, York's
// line and the Birge scaling on cases computed by hand, the cross-check against the Python reference
// lfphys.tools.stats.linear_fit on the shared fixture (fixtures/fit_cases.json, Pearson–York included; integrator D3),
// and the fit's printed output (EX2 §5 F6 (c): the σ from the declared errors, the σ scaled by the Birge ratio on its own,
// χ² and its p-value against SciPy, fixtures/chi2_sf.json); the verdict of «Check against the law» is withdrawn (the
// owner, 2026-11-18). Run from visualizations/: node --test player/js/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { chi2Sf, fit, lnGamma } from "../fit.js";

const close = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol * Math.max(1, Math.abs(b)), `${msg}: ${a} vs ${b}`);

test("line0 on exact data: b, σ_b = σ/√Σx², χ² = 0 (no scaling)", () => {
  const r = fit([1, 2, 3], [2, 4, 6], [0, 0, 0], [0.1, 0.1, 0.1], "line0");
  close(r.params.b, 2, 1e-15, "b");
  close(r.sigma.b, 0.1 / Math.sqrt(14), 1e-15, "σ_b");
  close(r.chi2, 0, 1e-20, "χ²");
  assert.equal(r.scaled, false);
  assert.equal(r.dof, 2);
});

test("line0 with equal x and y errors: York's line is the orthogonal (total) least squares through the origin", () => {
  // S(b) = Σ(y − b·x)²/(σ²(1 + b²)) is least where Sxy·b² + (Sxx − Syy)·b − Sxy = 0: Sxx = 5, Syy = 21.64, Sxy = 10.4
  const r = fit([1, 2], [2, 4.2], [0.1, 0.1], [0.1, 0.1], "line0");
  const b = (16.64 + Math.sqrt(16.64 ** 2 + 4 * 10.4 ** 2)) / 20.8;
  close(r.params.b, b, 1e-14, "b");
  close(r.chi2, ((2 - b) ** 2 + (4.2 - 2 * b) ** 2) / (0.01 * (1 + b * b)), 1e-12, "χ² = S at the minimum");
  assert.equal(r.method, "york");
  assert.equal(r.scaled, false, "χ²/dof < 1: not scaled");
});

test("York's line on Pearson's data with York's weights (York et al. 2004, Table II, data set 3)", () => {
  const X = [0.0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4], Y = [5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5];
  const WX = [1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1], WY = [1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500];
  const r = fit(X, Y, WX.map((w) => 1 / Math.sqrt(w)), WY.map((w) => 1 / Math.sqrt(w)), "line");
  assert.ok(Math.abs(r.params.a - 5.47991) < 5e-6 && Math.abs(r.params.b + 0.480533) < 5e-7, `a ${r.params.a}, b ${r.params.b}`);
  assert.ok(Math.abs(r.chi2 / r.dof - 1.483) < 5e-4, `S/(n − 2) ${r.chi2 / r.dof}`);
  // the paper's σ are unscaled; the lab scales by the Birge ratio since χ²/dof > 1
  assert.equal(r.scaled, true);
  close(r.sigma.b / r.birge, 0.057985, 2e-5, "σ_b unscaled"); close(r.sigma.a / r.birge, 0.294970, 2e-5, "σ_a unscaled");
});

test("line on exact data and a scatter that scales the errors (Birge)", () => {
  const x = [0, 1, 2, 3, 4], ex = x.map((v) => 1 + 2 * v);
  const r = fit(x, ex, null, x.map(() => 0.01), "line");
  close(r.params.a, 1, 1e-13, "a"); close(r.params.b, 2, 1e-13, "b");
  // unweighted (equal σ) closed forms: σ_b² = σ²/Sxx, σ_a² = σ²·Σx²/(n·Sxx); Sxx = 10, Σx² = 30
  close(r.sigma.b, 0.01 / Math.sqrt(10), 1e-12, "σ_b"); close(r.sigma.a, 0.01 * Math.sqrt(30 / 50), 1e-12, "σ_a");
  const y = [1.0, 3.1, 4.9, 7.2, 8.8];  // a scatter far larger than σ = 0.01: χ²/dof ≫ 1, the σ are scaled by √(χ²/dof)
  const s = fit(x, y, null, x.map(() => 0.01), "line");
  // ordinary least squares by hand: x̄ = 2, ȳ = 5, Sxy = Σ(x − x̄)(y − ȳ) = 19.7, b = 1.97, a = 5 − 1.97·2 = 1.06
  close(s.params.b, 1.97, 1e-13, "b"); close(s.params.a, 1.06, 1e-12, "a");
  const res = y.map((v, i) => v - (1.06 + 1.97 * x[i]));
  const rss = res.reduce((q, v) => q + v * v, 0);
  close(s.chi2, rss / 1e-4, 1e-10, "χ²");
  assert.equal(s.scaled, true);
  close(s.sigma.b, Math.sqrt(rss / 3 / 10), 1e-12, "σ_b scaled = the OLS σ_b");
});

test("quadratic: exact parabola, its vertex and the vertex's σ from the covariance", () => {
  const x = [15, 30, 45, 60, 75], y = x.map((v) => -((v - 45) ** 2) / 100 + 20);
  const r = fit(x, y, null, x.map(() => 0.05), "quadratic");
  close(r.params.xv, 45, 1e-11, "x*");
  close(r.params.yv, 20, 1e-11, "y*");
  close(r.params.c2, -0.01, 1e-11, "c2");
  assert.ok(r.sigma.xv > 0 && r.sigma.xv < 1, `σ(x*) ${r.sigma.xv}`);
  // the σ of x* by a numerical gradient of x*(c1, c2) with the same covariance
  const [c1, c2] = [r.params.c1, r.params.c2], h1 = 1e-7 * Math.abs(c1), h2 = 1e-7 * Math.abs(c2);
  const g = [0, (-(c1 + h1) / (2 * c2) + c1 / (2 * c2)) / h1, (-c1 / (2 * (c2 + h2)) + c1 / (2 * c2)) / h2];
  let v = 0;
  for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) v += g[a] * r.cov[a][b] * g[b];
  close(r.sigma.xv, Math.sqrt(v), 1e-5, "σ(x*)");
});

test("power: y = A·x^p in log–log; non-positive values refused", () => {
  const x = [1, 2, 4, 8], y = x.map((v) => 3 * v ** 0.5);
  const r = fit(x, y, null, y.map((v) => 0.01 * v), "power");
  close(r.params.A, 3, 1e-12, "A"); close(r.params.p, 0.5, 1e-12, "p");
  assert.throws(() => fit([0, 1, 2], [1, 2, 3], null, null, "power"), (e) => e.why === "positive");
  assert.throws(() => fit([1], [2], null, null, "line"), (e) => e.why === "points");
  assert.throws(() => fit([1, 1, 1], [1, 2, 3], null, null, "line"), (e) => e.why === "singular");
  assert.throws(() => fit([30, 30, 30, 40], [1, 2, 3, 4], null, [0.1, 0.1, 0.1, 0.1], "quadratic"), (e) => e.why === "singular", "R-E F8");
});

test("readings without errors: ordinary least squares, σ from the scatter", () => {
  const r = fit([0, 1, 2, 3, 4], [1.0, 3.1, 4.9, 7.2, 8.8], null, null, "line");
  close(r.params.b, 1.97, 1e-13, "b");
  assert.ok(Number.isNaN(r.chi2));
  assert.equal(r.scaled, true);
});

// The cross-check with Python's lfphys.tools.stats.linear_fit: fixtures/fit_cases.json, written by
// fixtures/make_fit_cases.py: each case {x, y, sx, sy, model, params, sigma, chi2, scaled, method} or {…, refused:
// "singular"}; agreement to 1e-12, the same method, the same refusals
const FIX = new URL("./fixtures/fit_cases.json", import.meta.url);
test("against lfphys.tools.stats.linear_fit (Python) on shared cases", { skip: !existsSync(FIX) && "no fixture (fixtures/make_fit_cases.py)" }, () => {
  const cases = JSON.parse(readFileSync(FIX, "utf-8"));
  assert.ok(cases.length >= 8 && new Set(cases.map((c) => c.model)).size === 4, "every model");
  assert.ok(cases.some((c) => c.method === "york") && cases.some((c) => c.method === "effective_variance") && cases.some((c) => c.method === "ols"), "every method");
  assert.ok(cases.some((c) => c.x[9] === 7.4 && c.y[0] === 5.9), "Pearson–York");
  assert.ok(cases.filter((c) => c.refused).length >= 3, "the singular designs");
  for (const [i, c] of cases.entries()) {
    if (c.refused) { assert.throws(() => fit(c.x, c.y, c.sx, c.sy, c.model), (e) => e.why === c.refused, `case ${i} ${c.model} refused`); continue; }
    const r = fit(c.x, c.y, c.sx, c.sy, c.model);
    if (c.method) assert.equal(r.method, c.method, `case ${i} ${c.model}: method`);
    for (const [k, v] of Object.entries(c.params)) close(r.params[k], v, 1e-12, `case ${i} ${c.model} ${k}`);
    for (const [k, v] of Object.entries(c.sigma || {})) close(r.sigma[k], v, 1e-12, `case ${i} ${c.model} σ ${k}`);
    if (c.chi2 !== null) close(r.chi2, c.chi2, 1e-12, `case ${i} ${c.model} χ²`); else assert.ok(Number.isNaN(r.chi2));
    assert.equal(r.scaled, c.scaled, `case ${i} ${c.model}: scaled`);
  }
});

// --- the fit's output (EX2 §5 F6 (c)): no verdict, the σ declared and scaled, χ² and its p-value ---------------------------
const SF = new URL("./fixtures/chi2_sf.json", import.meta.url);
test("the p-value of χ² against SciPy's chi2.sf, from p near 1 to 1e-60", { skip: !existsSync(SF) && "no fixture" }, () => {
  const cases = JSON.parse(readFileSync(SF, "utf-8"));
  assert.ok(cases.length >= 50);
  for (const c of cases) close(chi2Sf(c.chi2, c.dof), c.p, 1e-10, `χ² ${c.chi2}, ν ${c.dof}`);
  assert.equal(chi2Sf(0, 3), 1);
  assert.ok(Number.isNaN(chi2Sf(1, 0)) && Number.isNaN(chi2Sf(-1, 2)));
  close(lnGamma(0.5), Math.log(Math.sqrt(Math.PI)), 1e-15, "ln Γ(½)");
  close(lnGamma(10), Math.log(362880), 1e-15, "ln Γ(10) = ln 9!");
});

test("the σ from the declared errors and, when χ²/dof > 1, the σ scaled by the Birge ratio, each printed on its own", () => {
  const x = [0, 1, 2, 3, 4], y = [1.0, 3.1, 4.9, 7.2, 8.8];
  const a = fit(x, y, null, x.map(() => 0.1), "line");
  assert.ok(a.birge > 1 && a.scaled);
  close(a.sigmaScaled.b, a.sigmaDeclared.b * a.birge, 1e-15, "scaled = declared × √(χ²/dof)");
  close(a.sigmaScaled.b, a.sigma.b, 1e-15, "the scaled σ is EX1's σ");
  close(a.p, chi2Sf(a.chi2, a.dof), 1e-15, "p");
  const b = fit([1, 2, 3], [2, 4, 6.01], null, [0.1, 0.1, 0.1], "line0");
  assert.ok(!b.scaled && b.birge < 1);
  assert.deepEqual(b.sigmaScaled, b.sigmaDeclared, "χ²/dof ≤ 1: nothing scaled");
  const c = fit(x, y, null, null, "line");  // no declared errors: the σ from the scatter, no χ²
  assert.ok(c.unit && Number.isNaN(c.p) && Number.isNaN(c.chi2));
  close(c.sigmaDeclared.b, c.sigma.b, 1e-15, "from the scatter");
  const q = fit([-2, -1, 0, 1, 2, 3], [-3.9, -1.1, 0.1, -0.9, -4.1, -9.0], null, [0.1, 0.1, 0.1, 0.1, 0.1, 0.1], "quadratic");
  assert.ok(q.sigmaScaled.xv >= q.sigmaDeclared.xv && q.sigmaDeclared.xv > 0, "the vertex's σ both ways");
});
