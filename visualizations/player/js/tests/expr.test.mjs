// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The formula columns (expr.js; design lfphys/sources/explore_EX2_2026-11-18_design.md §5 F5, §7): the shared fixture
// fixtures/expr_cases.json (values and both error terms against mpmath's own derivatives, to 1e-12; the undefined values
// with their reasons; the refused formulas with their codes), which tests/test_expr.py reads too; and the parser's
// safety: no eval, no Function, no property access, names looked up in Maps only.
// Run from visualizations/: node --test player/js/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { ExprError, MAX_CHARS, RESERVED, Undefined, evaluate, parse } from "../expr.js";

const F = JSON.parse(readFileSync(new URL("./fixtures/expr_cases.json", import.meta.url), "utf8"));
// relative to the reference; mpmath's numerical derivative of a linear function leaves ~1e-130 for ∂²f/∂x²: a floor
const close = (a, b, tol, msg, floor = 1e-300) => assert.ok(Math.abs(a - b) <= tol * Math.max(Math.abs(b), floor) || a === b, `${msg}: ${a} vs ${b}`);
const valuesOf = (vars) => Object.fromEntries(Object.entries(vars).map(([k, [v, e]]) => [k, { v, e }]));

test("the shared fixture: values and both error terms against mpmath's derivatives, to 1e-12", () => {
  let n = 0;
  for (const c of F.cases.filter((x) => !x.undefined)) {
    const r = evaluate(parse(c.expr, { columns: Object.keys(c.vars) }), valuesOf(c.vars));
    close(r.v, c.value, 1e-12, `${c.expr}: value`);
    close(r.t1, c.t1, 1e-12, `${c.expr}: Σ(∂f/∂x·σ)²`);
    close(r.t2, c.t2, 1e-12, `${c.expr}: ½Σ(∂²f/∂x²)²σ⁴`, 1e-90);
    close(r.e, c.error, 1e-12, `${c.expr}: σ`);
    n++;
  }
  assert.ok(n >= 50, `${n} cases`);
});

test("the shared fixture: an undefined value says why (the cell stays empty with the reason)", () => {
  for (const c of F.cases.filter((x) => x.undefined)) {
    assert.throws(() => evaluate(parse(c.expr), valuesOf(c.vars)), (e) => e instanceof Undefined && e.reason === c.undefined, c.expr);
  }
});

test("the shared fixture: refused formulas with their codes (unknown names, later columns, bad syntax, calls)", () => {
  for (const c of F.refused) {
    assert.throws(() => parse(c.expr, { columns: c.columns, later: c.later }), (e) => e instanceof ExprError && e.code === c.code,
      `${JSON.stringify(c.expr).slice(0, 60)} → ${c.code}`);
  }
  assert.ok(F.refused.some((c) => c.expr === "constructor") && F.refused.some((c) => c.expr === "__proto__"));
});

test("names: the distinct columns in the order of their first appearance; pi and the functions are no columns", () => {
  assert.deepEqual([...parse("b * a + sin(b) / pi + a").names], ["b", "a"]);
  assert.deepEqual([...parse("pi * 2").names], []);
  assert.ok(RESERVED.has("pi") && RESERVED.has("sind") && !RESERVED.has("x"));
});

test("safety: a column called like a property of Object never reaches the prototype", () => {
  // with no column list, any name parses; its value must come from the values given, not from Object.prototype
  for (const name of ["constructor", "toString", "valueOf", "hasOwnProperty", "__proto__", "prototype"]) {
    const ex = parse(`${name} + 1`);
    assert.throws(() => evaluate(ex, {}), (e) => e instanceof Undefined && e.reason === "missing", name);
    assert.equal(evaluate(ex, { [name]: { v: 2, e: 0 } }).v, 3, name);
    assert.equal(evaluate(ex, new Map([[name, { v: 2, e: 0 }]])).v, 3, name);
  }
  const proto = JSON.parse('{"__proto__": {"v": 5, "e": 0}}');  // an own property named __proto__
  assert.equal(evaluate(parse("__proto__ * 2"), proto).v, 10);
});

test("safety: the module has no eval, no Function, no dynamic property access by a formula's name", () => {
  const src = readFileSync(new URL("../expr.js", import.meta.url), "utf8").replace(/\/\/.*$/gm, "");
  assert.ok(!/\beval\s*\(/.test(src) && !/\bnew\s+Function\b/.test(src) && !/\bFunction\s*\(/.test(src), "no eval or Function");
  assert.ok(!/\bimport\s*\(/.test(src), "no dynamic import");
});

test("limits: too long, too deep, an empty formula", () => {
  assert.throws(() => parse("x".repeat(MAX_CHARS + 1)), (e) => e.code === "too_long");
  assert.throws(() => parse("(".repeat(100) + "1" + ")".repeat(100)), (e) => e.code === "too_deep");
  assert.throws(() => parse(""), (e) => e.code === "empty");
  assert.throws(() => parse(42), (e) => e.code === "syntax");
});

test("precedence: -2^2 = -4, 2^-1 = 0.5, 2^3^2 = 512, 1 - 2 - 3 = -4, 8 / 4 / 2 = 1", () => {
  const v = (s) => evaluate(parse(s), {}).v;
  assert.equal(v("-2^2"), -4); assert.equal(v("2^-1"), 0.5); assert.equal(v("2^3^2"), 512);
  assert.equal(v("1 - 2 - 3"), -4); assert.equal(v("8 / 4 / 2"), 1); assert.equal(v("2 * (3 + 4)"), 14);
  assert.equal(v("sind(30) * 2"), Math.sin(30 * Math.PI / 180) * 2);
});

test("an exact input (σ 0) adds nothing; σ by hand for a product: σ² = (bσa)² + (aσb)² + (σaσb)², its exact variance", () => {
  const r = evaluate(parse("a * b"), { a: { v: 2, e: 0.1 }, b: { v: 3, e: 0.2 } });
  assert.ok(Math.abs(r.e - Math.sqrt(0.09 + 0.16 + 0.0004)) < 1e-15 && Math.abs(r.t2 - 0.0004) < 1e-18, `${r.e} ${r.t2}`);
  // review R2-F F2: at the saddle x = y = 0 the mixed term is the whole error (it was 0 without it)
  const saddle = evaluate(parse("x * y"), { x: { v: 0, e: 1 }, y: { v: 0, e: 1 } });
  assert.ok(saddle.v === 0 && saddle.t1 === 0 && saddle.e === 1, `${saddle.e}`);
  const r2 = evaluate(parse("a * b"), { a: { v: 2, e: 0 }, b: { v: 3, e: 0.2 } });
  assert.ok(Math.abs(r2.e - 0.4) < 1e-15);
  const sq = evaluate(parse("x^2"), { x: { v: 0, e: 0.1 } });  // at a stationary point the second order keeps an error
  assert.ok(Math.abs(sq.e - Math.sqrt(0.5) * 2 * 0.01) < 1e-15, `${sq.e}`);
});

test("ASCII digits and spaces only, as expr.py (review R2-F F8): a formula parses in both or in neither", () => {
  assert.equal(evaluate(parse("x\t+\n1\r*\f2\v"), { x: { v: 1, e: 0 } }).v, 3);
  for (const bad of ["\u0663 * x", "x\u00a0+ 1", "x\u2028+ 1", "x\ufeff+ 1", "x\x1c+ 1", "x\x85+ 1"]) {
    assert.throws(() => parse(bad), (e) => e instanceof ExprError && e.code === "syntax", JSON.stringify(bad));
  }
});
