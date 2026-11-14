// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The lab's fit (fit.js; design lfphys/sources/explore_2026-11-14_design.md §2.3): every model on exact data, the
// effective variance and the Birge scaling on cases computed by hand. The cross-check against the Python reference
// lfphys.tools.stats.linear_fit on shared fixtures is added when that function lands (step E of batch EX1; until then
// the cases here are the hand-computed ones). Run from visualizations/: node --test player/js/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { agrees, fit, quantity } from "../fit.js";

const close = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol * Math.max(1, Math.abs(b)), `${msg}: ${a} vs ${b}`);

test("line0 on exact data: b, σ_b = σ/√Σx², χ² = 0 (no scaling)", () => {
  const r = fit([1, 2, 3], [2, 4, 6], [0, 0, 0], [0.1, 0.1, 0.1], "line0");
  close(r.params.b, 2, 1e-15, "b");
  close(r.sigma.b, 0.1 / Math.sqrt(14), 1e-15, "σ_b");
  close(r.chi2, 0, 1e-20, "χ²");
  assert.equal(r.scaled, false);
  assert.equal(r.dof, 2);
});

test("line0 with x errors: the effective variance by hand", () => {
  // first pass (σ_y only, equal): b = Σxy/Σx² = 10.4/5 = 2.08; then σ_i² = 0.01 + (2.08·0.05)² = 0.020816 (equal: b stays)
  const r = fit([1, 2], [2, 4.2], [0.05, 0.05], [0.1, 0.1], "line0");
  close(r.params.b, 2.08, 1e-14, "b");
  close(r.sigma.b, Math.sqrt(0.020816 / 5), 1e-13, "σ_b");
  close(r.chi2, (0.0064 + 0.0016) / 0.020816, 1e-12, "χ²");
  assert.equal(r.scaled, false, "χ²/dof = 0.38 < 1: not scaled");
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
});

test("readings without errors: ordinary least squares, σ from the scatter", () => {
  const r = fit([0, 1, 2, 3, 4], [1.0, 3.1, 4.9, 7.2, 8.8], null, null, "line");
  close(r.params.b, 1.97, 1e-13, "b");
  assert.ok(Number.isNaN(r.chi2));
  assert.equal(r.scaled, true);
});

test("the law's quantity and the agreement within two errors", () => {
  const r = fit([1, 2, 3], [2, 4, 6], null, [0.1, 0.1, 0.1], "line0");
  assert.deepEqual(quantity(r, "slope"), { value: r.params.b, sigma: r.sigma.b });
  assert.equal(quantity(r, "vertex"), null);
  assert.equal(agrees(2.0, 0.01, 2.015).agrees, true);
  assert.equal(agrees(2.0, 0.01, 2.03).agrees, false);
});

// The cross-check with Python's lfphys.tools.stats.linear_fit: tests/fixtures/fit_cases.json, written by
// lfphys/tests (step E), when present: each case {x, y, sx, sy, model, params, sigma, chi2}; agreement to 1e-12
const FIX = new URL("./fixtures/fit_cases.json", import.meta.url);
test("against lfphys.tools.stats.linear_fit (Python) on shared cases", { skip: !existsSync(FIX) && "no fixture (fixtures/make_fit_cases.py)" }, () => {
  const cases = JSON.parse(readFileSync(FIX, "utf-8"));
  assert.ok(cases.length >= 8 && new Set(cases.map((c) => c.model)).size === 4, "every model");
  for (const [i, c] of cases.entries()) {
    const r = fit(c.x, c.y, c.sx, c.sy, c.model);
    for (const [k, v] of Object.entries(c.params)) close(r.params[k], v, 1e-12, `case ${i} ${c.model} ${k}`);
    for (const [k, v] of Object.entries(c.sigma || {})) close(r.sigma[k], v, 1e-12, `case ${i} ${c.model} σ ${k}`);
    if (c.chi2 !== null) close(r.chi2, c.chi2, 1e-12, `case ${i} ${c.model} χ²`); else assert.ok(Number.isNaN(r.chi2));
    assert.equal(r.scaled, c.scaled, `case ${i} ${c.model}: scaled`);
  }
});
